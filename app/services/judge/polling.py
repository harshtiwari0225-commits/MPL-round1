"""Batch polling loop and decoding helpers for the Judge0 client.

After POST /submissions/batch returns tokens, we poll
GET /submissions/batch?tokens=... until every token leaves the pending
state or the hard deadline (JUDGE0_TIMEOUT_SECONDS) passes.
"""

from __future__ import annotations

import asyncio
import base64

import httpx

from app.core.config import settings
from app.services.judge.base import (
    PENDING_STATUS_IDS,
    STATUS_INTERNAL_ERROR,
    JudgeOutcome,
)


async def poll_outcomes(
    outcomes: list[JudgeOutcome],
    base_url: str,
    headers: dict[str, str],
) -> list[JudgeOutcome]:
    deadline = asyncio.get_event_loop().time() + settings.JUDGE0_TIMEOUT_SECONDS
    pending = [o for o in outcomes if o.is_pending]

    async with httpx.AsyncClient(timeout=15.0) as client:
        while pending:
            if asyncio.get_event_loop().time() > deadline:
                for outcome in pending:
                    outcome.status_id = STATUS_INTERNAL_ERROR
                    outcome.status = "Internal Error"
                    outcome.message = "Judge0 polling timed out."
                break

            tokens = ",".join(o.token for o in pending if o.token)
            resp = await client.get(
                f"{base_url}/submissions/batch",
                params={
                    "tokens": tokens,
                    "base64_encoded": "true",
                    "fields": "token,status,stdout,stderr,compile_output,time,memory,message",
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json().get("submissions", [])

            by_token = {item.get("token"): item for item in data}
            for outcome in pending:
                item = by_token.get(outcome.token)
                if not item:
                    continue
                status_id = (item.get("status") or {}).get("id", 1)
                if status_id in PENDING_STATUS_IDS:
                    continue
                outcome.status_id = status_id
                outcome.status = (item.get("status") or {}).get("description", "")
                outcome.stdout = _b64decode(item.get("stdout"))
                outcome.stderr = _b64decode(item.get("stderr"))
                outcome.compile_output = _b64decode(item.get("compile_output"))
                outcome.message = item.get("message")
                outcome.time = _to_float(item.get("time"))
                outcome.memory = _to_float(item.get("memory"))

            pending = [o for o in outcomes if o.is_pending]
            if pending:
                await asyncio.sleep(settings.JUDGE0_POLL_INTERVAL)

    return outcomes


def _b64decode(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
