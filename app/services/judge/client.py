"""Judge0 backend - the real thing.

HTTP client for a self-hosted Judge0 CE instance. Uses
POST /submissions/batch to run every test case in one request, then polls
GET /submissions/batch (see polling.py) until all tokens leave the pending
state.
"""

from __future__ import annotations

import base64

import httpx

from app.core.config import settings
from app.services.judge.base import STATUS_INTERNAL_ERROR, JudgeJob, JudgeOutcome
from app.services.judge.polling import poll_outcomes


class Judge0Client:
    def __init__(self):
        self.base_url = settings.JUDGE0_URL.rstrip("/")
        self._language_ids: dict[str, int] = {}
        self._languages_loaded = False

    # -- language resolution --------------------------------------------------

    async def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if settings.JUDGE0_AUTH_TOKEN:
            headers["X-Auth-Token"] = settings.JUDGE0_AUTH_TOKEN
        return headers

    async def ensure_languages(self) -> dict[str, int]:
        """Resolve our language keys -> Judge0 ids by NAME.

        Language ids differ between Judge0 versions, so we never hard-code them
        as the primary source of truth.
        """
        if self._languages_loaded:
            return self._language_ids

        resolved: dict[str, int] = {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/languages", headers=await self._headers())
                resp.raise_for_status()
                available = resp.json()

            for key, wanted in settings.LANGUAGE_NAMES.items():
                match = next((lang for lang in available if lang.get("name") == wanted), None)
                if match is None:
                    # fall back to a looser prefix match, e.g. "Python (3"
                    prefix = wanted.split("(")[0].strip().lower()
                    match = next(
                        (
                            lang
                            for lang in available
                            if lang.get("name", "").lower().startswith(prefix)
                        ),
                        None,
                    )
                if match:
                    resolved[key] = int(match["id"])
        except Exception:
            resolved = {}

        # Last resort: the hard-coded table.
        for key, fallback in settings.FALLBACK_LANGUAGE_IDS.items():
            resolved.setdefault(key, fallback)

        self._language_ids = resolved
        self._languages_loaded = True
        return resolved

    async def languages(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/languages", headers=await self._headers())
            resp.raise_for_status()
            return resp.json()

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/about", headers=await self._headers())
                return resp.status_code == 200
        except Exception:
            return False

    # -- submission -----------------------------------------------------------

    def _payload(self, job: JudgeJob, language_id: int) -> dict:
        return {
            "language_id": language_id,
            "source_code": base64.b64encode(job.source_code.encode()).decode(),
            "stdin": base64.b64encode(job.stdin.encode()).decode(),
            # Judge0 compares this byte-exact; we ALSO compare ourselves with the
            # question's compare_mode so floats/whitespace don't cause false WAs.
            "expected_output": base64.b64encode(job.expected_output.encode()).decode(),
            "cpu_time_limit": job.cpu_time_limit,
            "wall_time_limit": job.wall_time_limit,
            "memory_limit": job.memory_limit_kb,
            "redirect_stderr_to_stdout": False,
        }

    async def run_batch(self, jobs: list[JudgeJob]) -> list[JudgeOutcome]:
        if not jobs:
            return []

        ids = await self.ensure_languages()
        payloads = []
        for job in jobs:
            language_id = ids.get(job.language)
            if language_id is None:
                payloads.append(None)
            else:
                payloads.append(self._payload(job, language_id))

        # Unsupported language -> synthetic outcome, don't call Judge0 for it.
        tokens: list[str | None] = []
        batch: list[dict] = []
        index_map: list[int] = []
        for i, payload in enumerate(payloads):
            if payload is None:
                tokens.append(None)
            else:
                index_map.append(i)
                batch.append(payload)
                tokens.append("__pending__")

        if batch:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.base_url}/submissions/batch",
                    params={"base64_encoded": "true", "wait": "false"},
                    json={"submissions": batch},
                    headers=await self._headers(),
                )
                resp.raise_for_status()
                created = resp.json()
            for slot, item in zip(index_map, created):
                tokens[slot] = item.get("token")

        outcomes: list[JudgeOutcome] = []
        for i, job in enumerate(jobs):
            if tokens[i] is None:
                outcomes.append(
                    JudgeOutcome(
                        status_id=STATUS_INTERNAL_ERROR,
                        status="Internal Error",
                        message=f"No Judge0 language id resolved for '{job.language}'.",
                    )
                )
            else:
                outcomes.append(JudgeOutcome(status_id=1, status="In Queue", token=tokens[i]))

        return await poll_outcomes(outcomes, self.base_url, await self._headers())
