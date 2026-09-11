"""Local subprocess execution helpers for the mock judge.

This is NOT a sandbox - it only exists so the whole game pipeline can be
developed and tested without Docker. Never use it on event day; switch to
JUDGE_BACKEND=judge0.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import List

from app.services.judge.base import (
    JudgeJob,
    JudgeOutcome,
    STATUS_ACCEPTED,
    STATUS_WRONG_ANSWER,
    STATUS_TIME_LIMIT,
    STATUS_COMPILATION_ERROR,
    STATUS_INTERNAL_ERROR,
)


def execute(argv: List[str], job: JudgeJob, cwd: str) -> JudgeOutcome:
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


def compile_and_run(source_name: str, compile_argv: List[str],
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
        return execute(run_argv, job, tmp)
