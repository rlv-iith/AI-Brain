"""
One-time model setup script.
Downloads Phi-3.5-Mini from HuggingFace and saves each transformer layer
as an individual .pt shard file in model_shards/.

Run from the 05/ folder:
    python scripts/setup.py

What it creates:
    model_shards/
    ├── embed.pt         ← nn.Embedding weights   (~12 MB)
    ├── layer_00.pt      ← Phi3DecoderLayer 0     (~226 MB)
    ├── ...
    ├── layer_31.pt      ← Phi3DecoderLayer 31
    ├── norm.pt          ← RMSNorm weights         (~6 KB)
    └── lm_head.pt       ← Linear output head      (~12 MB)

Total: ~7.5 GB on disk
RAM needed during split: ~8 GB (model loaded in fp16)

This is the AirLLM technique:
  Instead of loading 7.5 GB all at once during inference,
  each 226 MB layer is loaded, processed, and freed.
  Peak inference RAM ≈ embed + 1 layer + KV cache ≈ ~500 MB.
"""

import gc
import sys
from pathlib import Path

# Run from 05/ directory
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import torch
from transformers import AutoModelForCausalLM, AutoConfig

MODEL_ID  = "microsoft/Phi-3.5-mini-instruct"
SHARD_DIR = ROOT / "model_shards"


def split_and_save():
    SHARD_DIR.mkdir(exist_ok=True)

    print(f"Downloading {MODEL_ID} (this may take a while on first run)…")
    print("Tip: model is cached in ~/.cache/huggingface after first download.\n")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype     = torch.float16,
        low_cpu_mem_usage = True,   # materialises weights one-by-one → lower peak RAM
        trust_remote_code = True,
    )
    model.eval()

    n = model.config.num_hidden_layers
    print(f"Model loaded: {n} transformer layers.\n")

    # ── embedding ─────────────────────────────────────────────────────────────
    p = SHARD_DIR / "embed.pt"
    if not p.exists():
        torch.save(model.model.embed_tokens.state_dict(), p)
        print(f"  saved embed.pt  ({p.stat().st_size // 1_048_576} MB)")

    # ── transformer layers ────────────────────────────────────────────────────
    for i, layer in enumerate(model.model.layers):
        p = SHARD_DIR / f"layer_{i:02d}.pt"
        if not p.exists():
            torch.save(layer.state_dict(), p)
            mb = p.stat().st_size // 1_048_576
            print(f"  saved layer_{i:02d}.pt  ({mb} MB)  [{i+1}/{n}]")

    # ── norm + lm_head ────────────────────────────────────────────────────────
    for name, module in [("norm", model.model.norm), ("lm_head", model.lm_head)]:
        p = SHARD_DIR / f"{name}.pt"
        if not p.exists():
            torch.save(module.state_dict(), p)
            print(f"  saved {name}.pt")

    total_mb = sum(f.stat().st_size for f in SHARD_DIR.glob("*.pt")) // 1_048_576
    print(f"\nAll shards saved → {SHARD_DIR}")
    print(f"Total size: {total_mb} MB")

    # Free the full model from RAM now that shards are on disk
    del model
    gc.collect()
    print("\nFull model freed from RAM.")
    print("You can now start the server: uvicorn server:app --reload --port 8000")


if __name__ == "__main__":
    split_and_save()
