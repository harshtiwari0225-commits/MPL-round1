"""Code-execution sandbox client.

Two interchangeable backends:

  * ``MockJudge``   - runs code locally (no Docker). Development only.
  * ``Judge0Client`` - talks to a self-hosted Judge0 CE instance. Event day.

Switch with the ``JUDGE_BACKEND`` env var ("mock" | "judge0"). Nothing else in
the codebase knows which one is in use.

Judge0 status ids (see docs/MPL_Judge0_Overview.md):
    1 In Queue | 2 Processing | 3 Accepted | 4 Wrong Answer | 5 TLE
    6 Compilation Error | 7-12 Runtime Error | 13 Internal Error | 14 Exec Format
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

# Status ids we treat as "keep polling"
PENDING_STATUS_IDS = (1, 2)
STATUS_ACCEPTED = 3
STATUS_WRONG_ANSWER = 4
STATUS_TIME_LIMIT = 5
STATUS_COMPILATION_ERROR = 6
STATUS_INTERNAL_ERROR = 13


# ─────────────────────────────────────────────────────────────────────────────
# Data transfer objects
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class JudgeJob:
    """One test case: run `source_code` with `stdin`, compare to `expected_output`."""
    source_code: str
    language: str                 # our key: python / c / cpp / java
    stdin: str = ""
    expected_output: str = ""
    cpu_time_limit: float = 5.0
    wall_time_limit: float = 10.0
    memory_limit_kb: int = 256_000


@dataclass
class JudgeOutcome:
    status_id: int
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    time: Optional[float] = None
    memory: Optional[float] = None
    message: Optional[str] = None
    token: Optional[str] = None

    @property
    def is_pending(self) -> bool:
        return self.status_id in PENDING_STATUS_IDS

    @property
    def accepted(self) -> bool:
        return self.status_id == STATUS_ACCEPTED


# ─────────────────────────────────────────────────────────────────────────────
# Mock backend - no Docker required
# ─────────────────────────────────────────────────────────────────────────────

class MockJudge:
    """Local stand-in for Judge0.

    Executes Python (and C/C++/Java if a compiler is installed) in a subprocess
    with a timeout. This is NOT a sandbox - it only exists so the whole game
    pipeline can be developed and tested without Docker.

    Set JUDGE_BACKEND=judge0 before the event. Never run the mock on event day
    with MOCK_EXECUTE_PYTHON=true.
    """

    def __init__(self):
        self._executors = {
            "python": self._run_python,
            "c": self._run_c,
            "cpp": self._run_cpp,
            "java": self._run_java,
        }

    async def run_batch(self, jobs: List[JudgeJob]) -> List[JudgeOutcome]:
        # Run sequentially; a real Judge0 parallelises in its worker pool.
        return [await asyncio.to_thread(self._run_one, job) for job in jobs]

    async def health(self) -> bool:
        return True

    async def languages(self) -> List[Dict]:
        return [
            {"id": lid, "name": name}
            for lid, (key, name) in zip(
                settings.FALLBACK_LANGUAGE_IDS.values(), settings.LANGUAGE_NAMES.items()
            )
        ]

    # -- internals ------------------------------------------------------------

    def _run_one(self, job: JudgeJob) -> JudgeOutcome:
        if job.language not in self._executors:
            return JudgeOutcome(
                status_id=STATUS_INTERNAL_ERROR,
                status="Internal Error",
                message=(
                    f"Mock judge: unsupported language '{job.language}'. "
                    "Supported: python, c, cpp, java."
                ),
            )

        if not settings.MOCK_EXECUTE_PYTHON:
            return JudgeOutcome(
                status_id=STATUS_INTERNAL_ERROR,
                status="Internal Error",
                message=(
                    "Mock judge is configured not to execute code "
                    "(MOCK_EXECUTE_PYTHON=false). Set JUDGE_BACKEND=judge0."
                ),
            )

        try:
            return self._executors[job.language](job)
        except Exception as exc:  # never let a sandbox glitch kill the request
            return JudgeOutcome(
                status_id=STATUS_INTERNAL_ERROR,
                status="Internal Error",
                message=f"Mock judge failure: {exc}",
            )

    def _execute(self, argv: List[str], job: JudgeJob, cwd: str) -> JudgeOutcome:
        timeout = max(1.0, float(job.cpu_time_limit or 5.0))
        try:
            proc = subprocess.run(
                argv,
                input=job.stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
            )
        except subprocess.TimeoutExpired:
            return JudgeOutcome(
                status_id=STATUS_TIME_LIMIT,
                status="Time Limit Exceeded",
                stderr=f"Execution exceeded {timeout}s",
                time=timeout,
            )

        if proc.returncode != 0:
            stderr = proc.stderr or ""
            # A Python SyntaxError is a compile failure, not a runtime crash.
            # Judge0 reports it as status 6, so the mock does too.
            if "SyntaxError" in stderr or "IndentationError" in stderr:
                return JudgeOutcome(
                    status_id=STATUS_COMPILATION_ERROR,
                    status="Compilation Error",
                    compile_output=stderr,
                )
            return JudgeOutcome(
                status_id=11,  # NZEC
                status="Runtime Error (NZEC)",
                stdout=proc.stdout,
                stderr=stderr,
            )

        # Mimic Judge0 with expected_output set: byte-exact compare, so the
        # caller's own tolerant comparator is the one that rescues floats and
        # trailing whitespace. Do not "help" by trimming here.
        if (proc.stdout or "") == (job.expected_output or ""):
            return JudgeOutcome(
                status_id=STATUS_ACCEPTED,
                status="Accepted",
                stdout=proc.stdout,
                stderr=proc.stderr or None,
                time=0.0,
            )

        return JudgeOutcome(
            status_id=STATUS_WRONG_ANSWER,
            status="Wrong Answer",
            stdout=proc.stdout,
            stderr=proc.stderr or None,
            time=0.0,
        )

    def _run_python(self, job: JudgeJob) -> JudgeOutcome:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "solution.py")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(job.source_code)
            return self._execute(
                [shutil.which("python3") or shutil.which("python") or "python3", path],
                job,
                tmp,
            )

    def _compile_and_run(self, source_name: str, compile_argv: List[str],
                         run_argv: List[str], job: JudgeJob) -> JudgeOutcome:
        compiler = compile_argv[0]
        if shutil.which(compiler) is None:
            return JudgeOutcome(
                status_id=STATUS_INTERNAL_ERROR,
                status="Internal Error",
                message=(
                    f"Mock judge: '{compiler}' is not installed on this machine, so "
                    f"{job.language} cannot be executed locally. Use JUDGE_BACKEND=judge0."
                ),
            )
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, source_name)
            with open(src, "w", encoding="utf-8") as fh:
                fh.write(job.source_code)

            comp = subprocess.run(
                compile_argv, capture_output=True, text=True, cwd=tmp, timeout=60
            )
            if comp.returncode != 0:
                return JudgeOutcome(
                    status_id=STATUS_COMPILATION_ERROR,
                    status="Compilation Error",
                    compile_output=(comp.stdout or "") + (comp.stderr or ""),
                )
            return self._execute(run_argv, job, tmp)

    def _run_c(self, job: JudgeJob) -> JudgeOutcome:
        return self._compile_and_run(
            "solution.c",
            ["gcc", "solution.c", "-o", "prog"],
            ["./prog"],
            job,
        )

    def _run_cpp(self, job: JudgeJob) -> JudgeOutcome:
        return self._compile_and_run(
            "solution.cpp",
            ["g++", "solution.cpp", "-o", "prog"],
            ["./prog"],
            job,
        )

    def _run_java(self, job: JudgeJob) -> JudgeOutcome:
        return self._compile_and_run(
            "Main.java",
            ["javac", "Main.java"],
            ["java", "Main"],
            job,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Judge0 backend - the real thing
# ─────────────────────────────────────────────────────────────────────────────

class Judge0Client:
    """HTTP client for a self-hosted Judge0 CE instance.

    Uses POST /submissions/batch to run every test case in one request, then
    polls GET /submissions/batch until all tokens leave the pending state.
    """

    def __init__(self):
        self.base_url = settings.JUDGE0_URL.rstrip("/")
        self._language_ids: Dict[str, int] = {}
        self._languages_loaded = False

    # -- language resolution --------------------------------------------------

    async def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if settings.JUDGE0_AUTH_TOKEN:
            headers["X-Auth-Token"] = settings.JUDGE0_AUTH_TOKEN
        return headers

    async def ensure_languages(self) -> Dict[str, int]:
        """Resolve our language keys -> Judge0 ids by NAME.

        Language ids differ between Judge0 versions, so we never hard-code them
        as the primary source of truth.
        """
        if self._languages_loaded:
            return self._language_ids

        resolved: Dict[str, int] = {}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.base_url}/languages", headers=await self._headers()
                )
                resp.raise_for_status()
                available = resp.json()

            for key, wanted in settings.LANGUAGE_NAMES.items():
                match = next(
                    (lang for lang in available if lang.get("name") == wanted), None
                )
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

    async def languages(self) -> List[Dict]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/languages", headers=await self._headers()
            )
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

    def _payload(self, job: JudgeJob, language_id: int) -> Dict:
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

    async def run_batch(self, jobs: List[JudgeJob]) -> List[JudgeOutcome]:
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
        tokens: List[Optional[str]] = []
        batch: List[Dict] = []
        index_map: List[int] = []
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

        outcomes: List[JudgeOutcome] = []
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
                outcomes.append(
                    JudgeOutcome(status_id=1, status="In Queue", token=tokens[i])
                )

        return await self._poll(outcomes)

    async def _poll(self, outcomes: List[JudgeOutcome]) -> List[JudgeOutcome]:
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
                    f"{self.base_url}/submissions/batch",
                    params={
                        "tokens": tokens,
                        "base64_encoded": "true",
                        "fields": "token,status,stdout,stderr,compile_output,time,memory,message",
                    },
                    headers=await self._headers(),
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


def _b64decode(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return value


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

_client = None


def get_judge():
    """Return the configured judge backend (cached)."""
    global _client
    if _client is None:
        if settings.JUDGE_BACKEND.lower() == "judge0":
            _client = Judge0Client()
        else:
            _client = MockJudge()
    return _client


def reset_judge() -> None:
    global _client
    _client = None
