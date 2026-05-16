"""
LLM Router — three modes:

  SINGLE   → use first available provider from ACTIVE_PROVIDERS
  RACE     → fire all providers concurrently, return first success
  COMPETE  → fire all providers concurrently, collect all, log + return best

'best' in COMPETE mode = longest coherent reply (simple heuristic;
swap in an LLM-judge or embedding similarity if you want real scoring).
"""

from __future__ import annotations
import asyncio
import logging
import os
from .providers import available_cloud_providers, call_provider, ProviderResult

logger = logging.getLogger(__name__)

async def route(messages: list[dict], local_fn=None, mode: str | None = None) -> dict:
    """
    Returns:
        {
            "reply":     str,
            "provider":  str,
            "latency_ms": float,
            "competition": [ProviderResult, ...]  # COMPETE mode only
        }
    """
    MODE = (mode or os.getenv("ROUTER_MODE", "RACE")).upper()
    cloud = available_cloud_providers()

    if MODE == "SINGLE":
        # Try local first, then cloud providers in order
        if local_fn:
            try:
                loop  = asyncio.get_event_loop()
                reply = await loop.run_in_executor(None, local_fn, messages)
                return {"reply": reply, "provider": "local", "latency_ms": 0, "competition": []}
            except Exception as e:
                logger.warning(f"Local engine failed: {e}")

        for name in cloud:
            res = await call_provider(name, messages)
            if res.ok:
                return {"reply": res.reply, "provider": res.provider,
                        "latency_ms": res.latency, "competition": [res]}
        return _empty("all providers failed")

    if MODE == "RACE":
        return await _race(messages, local_fn, cloud)

    if MODE == "COMPETE":
        return await _compete(messages, local_fn, cloud)

    return _empty(f"unknown ROUTER_MODE: {MODE}")


# ── RACE ──────────────────────────────────────────────────────────────────────

async def _race(messages, local_fn, cloud: list[str]) -> dict:
    """Return as soon as the first provider responds successfully."""
    tasks = {asyncio.create_task(call_provider(n, messages), name=n): n for n in cloud}

    if local_fn:
        async def _local():
            loop  = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, local_fn, messages)
            return ProviderResult("local", reply, 0)
        tasks[asyncio.create_task(_local(), name="local")] = "local"

    pending = set(tasks)
    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for t in done:
            try:
                res: ProviderResult = t.result()
                if res.ok and res.reply:
                    # Cancel remaining tasks (fire-and-forget)
                    for p in pending:
                        p.cancel()
                    logger.info(f"RACE winner: {res.provider} ({res.latency:.0f} ms)")
                    return {"reply": res.reply, "provider": res.provider,
                            "latency_ms": res.latency, "competition": [res]}
            except Exception as e:
                logger.warning(f"Task error: {e}")

    return _empty("all providers failed or cancelled")


# ── COMPETE ───────────────────────────────────────────────────────────────────

async def _compete(messages, local_fn, cloud: list[str]) -> dict:
    """Fire all providers, collect all results, log timing + quality."""
    coros = [call_provider(n, messages) for n in cloud]

    if local_fn:
        async def _local():
            loop  = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, local_fn, messages)
            return ProviderResult("local", reply, 0)
        coros.append(_local())

    results: list[ProviderResult] = await asyncio.gather(*coros, return_exceptions=False)

    ok = [r for r in results if r.ok and r.reply]
    if not ok:
        return _empty("all providers failed")

    # Simple quality heuristic: longest coherent reply wins
    best = max(ok, key=lambda r: len(r.reply))

    _log_competition(ok)
    return {
        "reply":       best.reply,
        "provider":    best.provider,
        "latency_ms":  best.latency,
        "competition": [
            {"provider": r.provider, "latency_ms": round(r.latency),
             "chars": len(r.reply), "ok": r.ok}
            for r in results
        ],
    }


def _log_competition(results: list[ProviderResult]):
    rows = sorted(results, key=lambda r: r.latency)
    logger.info("── COMPETE results ──────────────────")
    for r in rows:
        logger.info(f"  {r.provider:<12}  {r.latency:>6.0f} ms  {len(r.reply):>4} chars")
    logger.info("─────────────────────────────────────")


def _empty(reason: str) -> dict:
    logger.error(f"Router: {reason}")
    return {"reply": "Sorry, all AI providers are currently unavailable. Try again shortly.",
            "provider": "none", "latency_ms": 0, "competition": []}
