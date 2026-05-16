"""
Portfolio AI Brain — FastAPI server
────────────────────────────────────
Routes:
  GET  /health          → system status + which providers are live
  POST /chat            → main chat endpoint (RAG + LLM router)
  GET  /competition     → last COMPETE round results (diagnostic)

Quick start:
  pip install -r requirements.txt
  cp .env.example .env   # fill in API keys
  python scripts/setup.py          # one-time: download + shard the model
  uvicorn server:app --reload --port 8000
"""

from __future__ import annotations
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from brain.rag      import RAGPipeline
from brain.router   import route
from brain.providers import available_cloud_providers

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── globals ───────────────────────────────────────────────────────────────────

rag    = RAGPipeline()
engine = None        # set during lifespan if shards exist
_last_competition: list = []

# ── lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build RAG index (sentence-transformers, fast)
    logger.info("Building RAG index from knowledge/…")
    rag.build()

    # Try to warm the local SLM (optional — skip if shards not present)
    global engine
    try:
        from brain.engine import LayerWiseEngine
        low_mem = os.getenv("LOW_MEMORY", "false").lower() == "true"
        _engine = LayerWiseEngine(low_memory=low_mem)
        if _engine.shards_exist():
            logger.info(f"Warming local SLM (low_memory={low_mem})…")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _engine.warm)
            engine = _engine
            logger.info("Local SLM ready.")
        else:
            logger.info("No model shards found — local SLM disabled. Cloud providers only.")
    except Exception as e:
        logger.warning(f"Local SLM unavailable: {e}")

    yield   # ← server runs here

    logger.info("Shutting down.")


# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Portfolio AI Brain", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "http://localhost:5173"), "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── schemas ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:  str
    history:  list[dict] = []
    persona:  str        = "recruiter"   # recruiter | professor | tech_head


class ChatResponse(BaseModel):
    reply:       str
    provider:    str
    latency_ms:  float
    competition: list = []


# ── routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    cloud = available_cloud_providers()
    return {
        "status":          "ok",
        "local_slm":       engine is not None and engine.is_ready(),
        "cloud_providers": cloud,
        "router_mode":     os.getenv("ROUTER_MODE", "RACE"),
        "rag_chunks":      len(rag._chunks),
    }


async def _log_to_backend(data: dict):
    backend_url = os.getenv("BACKEND_URL", "").rstrip("/")
    if not backend_url:
        return
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(f"{backend_url}/ai-log", json=data)
    except Exception:
        pass


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Empty message")

    messages = rag.build_prompt(req.message, req.history, req.persona)

    local_fn = None
    if engine and engine.is_ready():
        def _local_generate(msgs):
            return engine.generate(msgs)
        local_fn = _local_generate

    result = await route(messages, local_fn=local_fn)

    global _last_competition
    _last_competition = result.get("competition", [])

    providers_tried = ",".join(r["provider"] for r in result.get("competition", []))
    asyncio.create_task(_log_to_backend({
        "token":           getattr(req, "token", ""),
        "session_id":      getattr(req, "session_id", ""),
        "query":           req.message[:150],
        "provider":        result["provider"],
        "mode":            os.getenv("ROUTER_MODE", "RACE"),
        "latency_ms":      result["latency_ms"],
        "providers_tried": providers_tried,
        "reply_preview":   result["reply"][:100],
    }))

    return ChatResponse(
        reply      = result["reply"],
        provider   = result["provider"],
        latency_ms = result["latency_ms"],
        competition= result.get("competition", []),
    )


@app.get("/competition")
def competition():
    """Returns the full provider comparison from the last COMPETE round."""
    return {"results": _last_competition}
