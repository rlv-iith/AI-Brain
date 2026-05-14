"""
Groq Full-Context Pipeline (active) — loads all knowledge/*.md files and
passes them as full system-prompt context to the LLM. No embedding model
needed; works within Render's 512 MB free tier.

TODO: RAG pipeline (commented out below) — re-enable when moving off free tier
or when knowledge base grows large enough that full-context hits token limits.
"""

from __future__ import annotations
import logging
from .knowledge_base import load_chunks

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self._context: str = ""

    def build(self):
        chunks = load_chunks()
        parts = [f"[{c['source']}]\n{c['text']}" for c in chunks]
        self._context = "\n\n---\n\n".join(parts)
        logger.info(f"Full-context pipeline ready — {len(chunks)} files loaded.")

    def build_prompt(self, query: str, history: list[dict], persona: str = "recruiter") -> list[dict]:
        persona_instructions = {
            "recruiter": (
                "You are speaking to a recruiter or hiring manager. "
                "Your goal is to pitch Lalith as a strong candidate for AI Engineering or Data Science roles. "
                "Highlight his technical depth, real-world projects, and internship experience. "
                "Be enthusiastic but factual. Keep answers concise and interview-ready."
            ),
            "competitor": (
                "You are speaking to another developer or tech enthusiast. "
                "Be honest and technical. Discuss trade-offs, architecture decisions, and what makes this work interesting. "
                "Lalith is not trying to impress — he is having a peer conversation."
            ),
            "professor": (
                "You are speaking to an academic or professor. "
                "Emphasise research experience, methodology, and learning outcomes. "
                "Connect projects to academic concepts where relevant."
            ),
        }
        persona_ctx = persona_instructions.get(persona, persona_instructions["recruiter"])
        system = (
            f"You are Lalith Vishnu R's personal AI pitch assistant, embedded in his portfolio website. "
            f"Visitors come here to learn about Lalith — who he is, what he has built, and why they should work with him. "
            f"{persona_ctx}\n\n"
            "Rules:\n"
            "- Answer only from the knowledge base below. Do not hallucinate experience or skills.\n"
            "- If something is not in the knowledge base, say so honestly rather than guessing.\n"
            "- Keep replies concise — 3 to 5 sentences unless a longer answer is clearly needed.\n"
            "- Speak in first person about Lalith (e.g. 'Lalith built...', 'He worked on...').\n\n"
            f"=== KNOWLEDGE BASE ===\n{self._context}\n=== END ==="
        )
        messages = [{"role": "system", "content": system}]
        for m in history[-6:]:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": query})
        return messages


# ── RAG pipeline (sentence-transformers + numpy cosine similarity) ────────────
# Uncomment when upgrading off Render free tier (needs ~400 MB for PyTorch).
#
# from __future__ import annotations
# import re
# import numpy as np
# from functools import lru_cache
#
# _EMBED_MODEL = "all-MiniLM-L6-v2"
# _CHUNK_SIZE  = 400
# _CHUNK_OVER  = 80
#
# def _split_text(text, size, overlap):
#     if len(text) <= size:
#         return [text]
#     parts, i = [], 0
#     while i < len(text):
#         parts.append(text[i : i + size])
#         i += size - overlap
#     return parts
#
# class RAGPipeline:
#     def __init__(self):
#         self._embedder = None
#         self._chunks = []
#         self._matrix = None
#
#     def build(self):
#         from sentence_transformers import SentenceTransformer
#         self._embedder = SentenceTransformer(_EMBED_MODEL)
#         raw = load_chunks()
#         sub_chunks = []
#         for c in raw:
#             for part in _split_text(c["text"], _CHUNK_SIZE, _CHUNK_OVER):
#                 sub_chunks.append({**c, "text": part})
#         texts = [c["text"] for c in sub_chunks]
#         vecs  = self._embedder.encode(texts, show_progress_bar=False, normalize_embeddings=True)
#         self._chunks = sub_chunks
#         self._matrix = np.array(vecs, dtype=np.float32)
#
#     def retrieve(self, query, top_k=4):
#         if self._matrix is None:
#             return ""
#         q_vec  = self._embedder.encode([query], normalize_embeddings=True)
#         scores = (self._matrix @ q_vec.T).squeeze()
#         top_idx = np.argsort(scores)[::-1][:top_k]
#         pieces = [f"[{self._chunks[i]['source']}]\n{self._chunks[i]['text']}" for i in top_idx]
#         return "\n\n---\n\n".join(pieces)
#
#     def build_prompt(self, query, history, persona="recruiter"):
#         context = self.retrieve(query)
#         system = (
#             "You are an AI assistant for Lalith Vishnu R's portfolio website. "
#             "Answer questions about Lalith based only on the context provided. "
#             "Be concise, factual, and friendly. "
#             f"Speak to a {persona}.\n\n=== CONTEXT ===\n{context}\n=== END CONTEXT ==="
#         )
#         messages = [{"role": "system", "content": system}]
#         for m in history[-6:]:
#             messages.append({"role": m["role"], "content": m["content"]})
#         messages.append({"role": "user", "content": query})
#         return messages
