"""
Cloud LLM providers — each returns (reply_text, latency_ms).
Add a key to .env and the provider is automatically available.
"""

from __future__ import annotations
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    provider: str
    reply:    str
    latency:  float          # ms
    error:    str  = ""
    ok:       bool = True


# ── individual providers ──────────────────────────────────────────────────────

async def _call_groq(messages: list[dict]) -> ProviderResult:
    import httpx
    key   = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "max_tokens": 512},
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()
        return ProviderResult("groq", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("groq", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_gemini(messages: list[dict]) -> ProviderResult:
    import httpx
    key   = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    # Convert OpenAI-style messages → Gemini parts
    sys_parts = [m["content"] for m in messages if m["role"] == "system"]
    chat_msgs = [{"role": "model" if m["role"] == "assistant" else "user",
                  "parts": [{"text": m["content"]}]}
                 for m in messages if m["role"] != "system"]
    body = {"contents": chat_msgs}
    if sys_parts:
        body["systemInstruction"] = {"parts": [{"text": "\n".join(sys_parts)}]}
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": key},
                json=body,
            )
            r.raise_for_status()
            reply = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return ProviderResult("gemini", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("gemini", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_mistral(messages: list[dict]) -> ProviderResult:
    import httpx
    key   = os.getenv("MISTRAL_API_KEY", "")
    model = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "max_tokens": 512},
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()
        return ProviderResult("mistral", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("mistral", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_openrouter(messages: list[dict]) -> ProviderResult:
    import httpx
    key   = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}",
                         "HTTP-Referer": "https://portfolio.rlv.dev"},
                json={"model": model, "messages": messages, "max_tokens": 512},
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()
        return ProviderResult("openrouter", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("openrouter", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_cerebras(messages: list[dict]) -> ProviderResult:
    import httpx
    key   = os.getenv("CEREBRAS_API_KEY", "")
    model = os.getenv("CEREBRAS_MODEL", "llama3.1-8b")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "max_tokens": 512},
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()
        return ProviderResult("cerebras", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("cerebras", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_anthropic(messages: list[dict]) -> ProviderResult:
    import anthropic as _ant
    key   = os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    sys_msg = next((m["content"] for m in messages if m["role"] == "system"), None)
    chat    = [m for m in messages if m["role"] != "system"]
    t0 = time.time()
    try:
        client = _ant.AsyncAnthropic(api_key=key)
        resp   = await client.messages.create(
            model=model, max_tokens=512,
            system=sys_msg or "",
            messages=chat,
        )
        reply = resp.content[0].text.strip()
        return ProviderResult("anthropic", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("anthropic", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_home_pc(messages: list[dict]) -> ProviderResult:
    """Ollama on home PC via Cloudflare Tunnel."""
    import httpx
    url   = os.getenv("HOME_PC_URL", "").rstrip("/")
    model = os.getenv("HOME_PC_MODEL", "llama3.2")
    if not url:
        return ProviderResult("home_pc", "", 0, "HOME_PC_URL not set", ok=False)
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{url}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            r.raise_for_status()
            reply = r.json()["message"]["content"].strip()
        return ProviderResult("home_pc", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("home_pc", "", (time.time() - t0) * 1000, str(e), ok=False)


async def _call_xai(messages: list[dict]) -> ProviderResult:
    """xAI Grok — OpenAI-compatible API (key starts with xai-)"""
    import httpx
    key   = os.getenv("XAI_API_KEY", "")
    model = os.getenv("XAI_MODEL", "grok-3-mini")
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "max_tokens": 512},
            )
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"].strip()
        return ProviderResult("xai", reply, (time.time() - t0) * 1000)
    except Exception as e:
        return ProviderResult("xai", "", (time.time() - t0) * 1000, str(e), ok=False)


# ── registry ──────────────────────────────────────────────────────────────────

_CLOUD_PROVIDERS: dict[str, callable] = {
    "groq":        _call_groq,
    "gemini":      _call_gemini,
    "mistral":     _call_mistral,
    "openrouter":  _call_openrouter,
    "cerebras":    _call_cerebras,
    "anthropic":   _call_anthropic,
    "xai":         _call_xai,
    "home_pc":     _call_home_pc,
}


def available_cloud_providers() -> list[str]:
    """Return providers that have an API key set in env."""
    active = [p.strip() for p in os.getenv("ACTIVE_PROVIDERS", "groq,gemini").split(",")]
    ready  = []
    for p in active:
        if p == "home_pc" and os.getenv("HOME_PC_URL"):
            ready.append(p)
        elif p in _CLOUD_PROVIDERS and os.getenv(f"{p.upper()}_API_KEY"):
            ready.append(p)
    return ready


async def call_provider(name: str, messages: list[dict]) -> ProviderResult:
    fn = _CLOUD_PROVIDERS.get(name)
    if fn is None:
        return ProviderResult(name, "", 0, f"Unknown provider: {name}", ok=False)
    return await fn(messages)
