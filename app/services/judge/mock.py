"""Mock backend - no Docker required.

Executes Python (and C/C++/Java if a compiler is installed) in a subprocess
with a timeout. This is NOT a sandbox - it only exists so the whole game
pipeline can be developed and tested without Docker.

Set JUDGE_BACKEND=judge0 before the event. Never run the mock on event day
with MOCK_EXECUTE_PYTHON=true.

The subprocess mechanics live in ``execution.py``; this module is only the
MockJudge facade behind the shared judge interface (run_batch / health).
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile

from app.core.config import settings
from app.services.judge.base import STATUS_INTERNAL_ERROR, JudgeJob, JudgeOutcome
from app.services.judge.execution import compile_and_run, execute


class MockJudge:
    def __init__(self):
        self._executors = {
            "python": self._run_python,
            "c": self._run_c,
            "cpp": self._run_cpp,
            "java": self._run_java,
        }

    async def run_batch(self, jobs: list[JudgeJob]) -> list[JudgeOutcome]:
        # Run sequentially; a real Judge0 parallelises in its worker pool.
        return [await asyncio.to_thread(self._run_one, job) for job in jobs]

    async def health(self) -> bool:
        return True

    async def languages(self) -> list[dict]:
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

    def _run_python(self, job: JudgeJob) -> JudgeOutcome:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "solution.py")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(job.source_code)
            return execute(
                [shutil.which("python3") or shutil.which("python") or "python3", path],
                job,
                tmp,
            )

    def _run_c(self, job: JudgeJob) -> JudgeOutcome:
        return compile_and_run(
            "solution.c",
            ["gcc", "solution.c", "-o", "prog"],
            ["./prog"],
            job,
        )

    def _run_cpp(self, job: JudgeJob) -> JudgeOutcome:
        return compile_and_run(
            "solution.cpp",
            ["g++", "solution.cpp", "-o", "prog"],
            ["./prog"],
            job,
        )

    def _run_java(self, job: JudgeJob) -> JudgeOutcome:
        return compile_and_run(
            "Main.java",
            ["javac", "Main.java"],
            ["java", "Main"],
            job,
        )
