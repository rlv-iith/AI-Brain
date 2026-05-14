"""
RAG pipeline — embeds knowledge chunks, retrieves top-k on query.
Uses sentence-transformers (all-MiniLM-L6-v2, ~80 MB) for embeddings.
No external vector DB needed; cosine similarity over numpy arrays.
"""

from __future__ import annotations
import logging
import re
import numpy as np
from functools import lru_cache
from .knowledge_base import load_chunks

logger = logging.getLogger(__name__)

_EMBED_MODEL = "all-MiniLM-L6-v2"
_CHUNK_SIZE  = 400   # chars per sub-chunk
_CHUNK_OVER  = 80    # overlap


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    """Split long text into overlapping char-level chunks."""
    if len(text) <= size:
        return [text]
    parts, i = [], 0
    while i < len(text):
        parts.append(text[i : i + size])
        i += size - overlap
    return parts


class RAGPipeline:
    def __init__(self):
        self._embedder = None
        self._chunks: list[dict] = []
        self._matrix: np.ndarray | None = None

    def build(self):
        """Load knowledge files, split, embed. Call once at startup."""
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model…")
        self._embedder = SentenceTransformer(_EMBED_MODEL)

        raw = load_chunks()
        sub_chunks = []
        for c in raw:
            for part in _split_text(c["text"], _CHUNK_SIZE, _CHUNK_OVER):
                sub_chunks.append({**c, "text": part})

        logger.info(f"Embedding {len(sub_chunks)} chunks…")
        texts = [c["text"] for c in sub_chunks]
        vecs  = self._embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        self._chunks = sub_chunks
        self._matrix = np.array(vecs, dtype=np.float32)
        logger.info("RAG index ready.")

    def retrieve(self, query: str, top_k: int = 4) -> str:
        """Return top-k relevant chunks concatenated as context string."""
        if self._matrix is None:
            return ""
        q_vec = self._embedder.encode([query], normalize_embeddings=True)
        scores = (self._matrix @ q_vec.T).squeeze()
        top_idx = np.argsort(scores)[::-1][:top_k]
        pieces = []
        for i in top_idx:
            c = self._chunks[i]
            pieces.append(f"[{c['source']}]\n{c['text']}")
        return "\n\n---\n\n".join(pieces)

    def build_prompt(self, query: str, history: list[dict], persona: str = "recruiter") -> str:
        context = self.retrieve(query)
        system = (
            "You are an AI assistant for Lalith Vishnu R's portfolio website. "
            "Answer questions about Lalith based only on the context provided. "
            "Be concise, factual, and friendly. If the answer is not in the context, say so honestly. "
            f"Speak to a {persona}.\n\n"
            f"=== CONTEXT ===\n{context}\n=== END CONTEXT ==="
        )
        messages = [{"role": "system", "content": system}]
        for m in history[-6:]:   # last 6 turns
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": query})
        return messages
