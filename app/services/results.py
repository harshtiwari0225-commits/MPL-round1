"""Mapping judge outcomes onto stored SubmissionResult rows.

Extracted verbatim from the old routes/main.py so the submit pipeline and
the admin rejudge pipeline build results identically.
"""
from __future__ import annotations

from typing import List

from app.models import CompareMode, SubmissionResult, TestCase
from app.services import scoring
from app.services.judge.base import JudgeOutcome

# Judge0 decides errors (compile / TLE / runtime / internal). We decide
# correctness with our own comparator so floats and trailing whitespace
# behave sensibly.
ERROR_STATUS_IDS = {5, 6, 7, 8, 9, 10, 11, 12, 13, 14}


def build_result(
    case: TestCase, outcome: JudgeOutcome, mode: CompareMode, visible: bool
) -> SubmissionResult:
    """Map one Judge0 outcome onto a stored result."""
    status_id = outcome.status_id
    passed = False
    error_statuses = ERROR_STATUS_IDS

    if status_id not in error_statuses:
        # Judge0 is authoritative for ERRORS. Correctness is decided here, with the
        # question's compare_mode, so trailing newlines and float formatting
        # cannot fail an otherwise correct answer.
        passed = scoring.outputs_match(outcome.stdout, case.expected_output, mode)

    return SubmissionResult(
        test_case_id=case.id,
        is_hidden=case.is_hidden,
        passed=bool(passed) and status_id not in error_statuses,
        judge_status_id=status_id,
        judge_status=outcome.status,
        stdout=outcome.stdout,
        stderr=outcome.stderr,
        compile_output=outcome.compile_output,
        # Hidden test inputs/answers are stored for admin/rejudge but are never
        # returned to the team - see scoring.public_results().
        expected_output=case.expected_output,
        stdin=case.stdin,
        time_seconds=outcome.time,
        memory_kb=outcome.memory,
    )


def propagate_compile_error(
    results: List[SubmissionResult], outcomes: List[JudgeOutcome]
) -> None:
    """A compilation error affects every test; surface it once."""
    compile_errors = [o for o in outcomes if o.status_id == 6]
    if compile_errors:
        for r in results:
            r.compile_output = r.compile_output or compile_errors[0].compile_output
