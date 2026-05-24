"""
RAG Pipeline — always builds fullcontext index (no ML needed).
Also builds a semantic index when RAG_MODE=semantic (requires torch).

  Cloud LLMs  → fullcontext: entire knowledge base injected as system prompt.
  Local SLM   → semantic: only the top-k relevant chunks are retrieved,
                keeping the prompt small enough for a tiny context window.
"""

from __future__ import annotations
import logging
import os
import re
from .knowledge_base import load_chunks

logger = logging.getLogger(__name__)
RAG_MODE = os.getenv("RAG_MODE", "fullcontext").lower()

_CHUNK_SIZE = 400
_CHUNK_OVER = 80


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    parts, i = [], 0
    while i < len(text):
        parts.append(text[i : i + size])
        i += size - overlap
    return parts


_PERSONA_INSTRUCTIONS = {
    "recruiter": (
        "You are speaking to a recruiter or hiring manager. "
        "Pitch Lalith as a strong candidate for AI Engineering or Data Science roles. "
        "Highlight technical depth, real-world projects, and internship experience. "
        "Be enthusiastic but factual. Keep answers concise and interview-ready."
    ),
    "competitor": (
        "You are speaking to another developer or tech enthusiast. "
        "Be honest and technical. Discuss trade-offs and architecture decisions. "
        "Lalith is having a peer conversation, not trying to impress."
    ),
    "professor": (
        "You are speaking to an academic or professor. "
        "Emphasise research experience, methodology, and learning outcomes. "
        "Connect projects to academic concepts where relevant."
    ),
}


class RAGPipeline:
    def __init__(self):
        self._context: str = ""         # fullcontext mode
        self._chunks: list[dict] = []   # semantic mode
        self._embedder = None           # semantic mode
        self._matrix = None             # semantic mode

    # ── build ──────────────────────────────────────────────────────────────────

    def build(self):
        chunks = load_chunks()
        self._build_fullcontext(chunks)          # always — cloud path needs this
        if RAG_MODE == "semantic":
            self._build_semantic(chunks)         # additionally — local SLM path

    def _build_fullcontext(self, chunks):
        parts = [f"[{c['source']}]\n{c['text']}" for c in chunks]
        self._context = "\n\n---\n\n".join(parts)
        logger.info(f"Full-context pipeline ready — {len(chunks)} files loaded.")

    def _build_semantic(self, chunks):
        import numpy as np
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model for semantic RAG…")
        self._embedder = SentenceTransformer("all-MiniLM-L6-v2")

        sub: list[dict] = []
        for c in chunks:
            for part in _split_text(c["text"], _CHUNK_SIZE, _CHUNK_OVER):
                sub.append({**c, "text": part})

        self._chunks = sub
        vecs = self._embedder.encode(
            [c["text"] for c in sub],
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        self._matrix = np.array(vecs, dtype=np.float32)
        logger.info(f"Semantic RAG ready — {len(sub)} chunks indexed.")

    # ── retrieve ───────────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 4, fullcontext: bool = False) -> str:
        if not fullcontext and self._matrix is not None:
            import numpy as np
            q = self._embedder.encode([query], normalize_embeddings=True)
            scores = (self._matrix @ q.T).squeeze()
            top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            pieces = [f"[{self._chunks[i]['source']}]\n{self._chunks[i]['text']}" for i in top_idx]
            return "\n\n---\n\n".join(pieces)
        return self._context

    # ── build_prompt ───────────────────────────────────────────────────────────

    def build_prompt(self, query: str, history: list[dict], persona: str = "recruiter", fullcontext: bool = False) -> list[dict]:
        context = self.retrieve(query, fullcontext=fullcontext)
        persona_ctx = _PERSONA_INSTRUCTIONS.get(persona, _PERSONA_INSTRUCTIONS["recruiter"])

        context_label = "KNOWLEDGE BASE" if fullcontext or self._matrix is None else "RETRIEVED CONTEXT"

        system = (
            "You are Lalith Vishnu R's personal AI pitch assistant, embedded in his portfolio website. "
            "Visitors come here to learn about Lalith — who he is, what he has built, and why they should work with him. "
            f"{persona_ctx}\n\n"
            "Rules:\n"
            "- Answer only from the knowledge base below. Do not hallucinate experience or skills.\n"
            "- If something is not in the knowledge base, say so honestly rather than guessing.\n"
            "- Keep replies concise — 3 to 5 sentences unless a longer answer is clearly needed.\n"
            "- Speak about Lalith in third person (e.g. 'Lalith built…', 'He worked on…').\n\n"
            f"=== {context_label} ===\n{context}\n=== END ==="
        )

        messages = [{"role": "system", "content": system}]
        for m in history[-6:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": query})
        return messages
