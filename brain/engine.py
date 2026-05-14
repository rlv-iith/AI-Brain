"""
LayerWiseEngine — Phi-3.5-Mini with AirLLM-style layer shard loading.

Architecture
────────────
  model_shards/
    embed.pt       ← embedding layer  (~12 MB)
    layer_00.pt    ← transformer block 0  (~226 MB)
    ...
    layer_31.pt    ← transformer block 31
    norm.pt        ← final RMS norm   (~6 KB)
    lm_head.pt     ← output projection  (~12 MB)

Two modes
─────────
  fast (default)  — loads all shards once into RAM on warm(), then keeps them.
                    Suitable when RAM >= 10 GB. ~7.5 GB used.
  low_mem         — loads one shard at a time, frees after each layer.
                    Peak RAM ≈ embed + 1 layer + KV cache ≈ ~500 MB.
                    Slower (SSD read per layer per decode step) but educational.

Run scripts/setup.py once before using this class.
"""

from __future__ import annotations
import gc
import logging
import os
from pathlib import Path
from typing import Optional

import torch

logger = logging.getLogger(__name__)

MODEL_ID  = "microsoft/Phi-3.5-mini-instruct"
SHARD_DIR = Path(os.getenv("SHARD_DIR", "./model_shards"))


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_state(path: Path, device="cpu") -> dict:
    return torch.load(path, map_location=device, weights_only=True)


# ── main class ───────────────────────────────────────────────────────────────

class LayerWiseEngine:
    """
    Phi-3.5-Mini inference with per-layer shard loading.
    Call warm() before generate().
    """

    def __init__(self, low_memory: bool = False):
        self.low_memory = low_memory
        self._ready     = False

        from transformers import AutoTokenizer, AutoConfig
        from transformers.models.phi3.modeling_phi3 import Phi3DecoderLayer

        logger.info("Loading tokenizer + config…")
        self.tokenizer   = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        self.config      = AutoConfig.from_pretrained(MODEL_ID, trust_remote_code=True)
        self.n_layers    = self.config.num_hidden_layers   # 32

        # Skeleton layer — we swap weights in/out instead of creating new instances
        self._skeleton   = Phi3DecoderLayer(self.config, layer_idx=0)
        self._skeleton.eval()

        # In fast mode these hold all layer state_dicts in RAM
        self._layer_cache: dict[int, dict] = {}

        # Persistent small components (always in RAM)
        self._embed: Optional[torch.nn.Module] = None
        self._norm:  Optional[torch.nn.Module] = None
        self._head:  Optional[torch.nn.Module] = None

    def is_ready(self) -> bool:
        return self._ready

    def shards_exist(self) -> bool:
        return (SHARD_DIR / "embed.pt").exists() and \
               (SHARD_DIR / f"layer_{self.n_layers-1:02d}.pt").exists()

    # ── setup ─────────────────────────────────────────────────────────────────

    def warm(self):
        """Load embed/norm/head (always). Pre-cache all layers in fast mode."""
        import torch.nn as nn

        if not self.shards_exist():
            raise FileNotFoundError(
                f"Model shards not found in {SHARD_DIR}. Run: python scripts/setup.py"
            )

        logger.info("Loading embed / norm / lm_head…")
        embed = nn.Embedding(self.config.vocab_size, self.config.hidden_size)
        embed.load_state_dict(_load_state(SHARD_DIR / "embed.pt"))
        embed = embed.to(torch.float16).eval()
        self._embed = embed

        norm = nn.RMSNorm(self.config.hidden_size, eps=self.config.rms_norm_eps)
        norm.load_state_dict(_load_state(SHARD_DIR / "norm.pt"))
        norm = norm.to(torch.float16).eval()
        self._norm = norm

        head = nn.Linear(self.config.hidden_size, self.config.vocab_size, bias=False)
        head.load_state_dict(_load_state(SHARD_DIR / "lm_head.pt"))
        head = head.to(torch.float16).eval()
        self._head = head

        if not self.low_memory:
            logger.info(f"Pre-loading {self.n_layers} layer shards into RAM…")
            for i in range(self.n_layers):
                self._layer_cache[i] = _load_state(SHARD_DIR / f"layer_{i:02d}.pt")
                if (i + 1) % 8 == 0:
                    logger.info(f"  {i+1}/{self.n_layers} shards loaded")

        self._ready = True
        logger.info("Engine ready.")

    # ── layer access ──────────────────────────────────────────────────────────

    def _get_layer_state(self, i: int) -> dict:
        if i in self._layer_cache:
            return self._layer_cache[i]
        return _load_state(SHARD_DIR / f"layer_{i:02d}.pt")

    def _free_layer(self, i: int):
        """In low_mem mode, evict layer from RAM after use."""
        if self.low_memory and i in self._layer_cache:
            del self._layer_cache[i]
            gc.collect()

    # ── forward pass ─────────────────────────────────────────────────────────

    @torch.no_grad()
    def _forward(self, input_ids: torch.Tensor, kv_cache: Optional[list]) -> tuple:
        """
        Single forward pass. Returns (logits, updated_kv_cache).
        kv_cache: list of past (K,V) tuples per layer, or None for first pass.
        """
        from transformers.cache_utils import DynamicCache

        # 1. Embed
        hidden = self._embed(input_ids).to(torch.float16)   # [1, seq, hidden]
        seq_len = input_ids.shape[1]

        # Build position ids
        past_len = 0 if kv_cache is None else kv_cache.get_seq_length()
        position_ids = torch.arange(past_len, past_len + seq_len).unsqueeze(0)

        if kv_cache is None:
            kv_cache = DynamicCache()

        # 2. Layer-by-layer
        for i in range(self.n_layers):
            state = self._get_layer_state(i)
            self._skeleton.load_state_dict(state)

            out = self._skeleton(
                hidden_states   = hidden,
                position_ids    = position_ids,
                past_key_value  = kv_cache,
                output_attentions=False,
                use_cache       = True,
            )
            hidden = out[0]
            self._free_layer(i)

        # 3. Norm + head (only last token for decode efficiency)
        h_last  = self._norm(hidden[:, -1:, :])
        logits  = self._head(h_last).float().squeeze(0)   # [1, vocab]
        return logits, kv_cache

    # ── generation ────────────────────────────────────────────────────────────

    @torch.no_grad()
    def generate(
        self,
        messages: list[dict],
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        if not self._ready:
            raise RuntimeError("Call warm() first.")

        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids

        kv_cache = None
        generated: list[int] = []
        eos = self.tokenizer.eos_token_id

        # Prefill (process full prompt, build KV cache)
        logits, kv_cache = self._forward(input_ids, kv_cache)

        for _ in range(max_new_tokens):
            tok = _sample(logits[-1], temperature, top_p)
            if tok == eos:
                break
            generated.append(tok)
            logits, kv_cache = self._forward(
                torch.tensor([[tok]]), kv_cache
            )

        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()


# ── sampling ──────────────────────────────────────────────────────────────────

def _sample(logits: torch.Tensor, temperature: float, top_p: float) -> int:
    if temperature <= 0:
        return int(logits.argmax())
    logits = logits / temperature
    probs  = torch.softmax(logits, dim=-1)
    sorted_p, sorted_i = torch.sort(probs, descending=True)
    cum = torch.cumsum(sorted_p, dim=-1)
    mask = (cum - sorted_p) > top_p
    sorted_p[mask] = 0.0
    sorted_p /= sorted_p.sum()
    return int(sorted_i[torch.multinomial(sorted_p, 1)])
