"""Output comparison and MAIN-event scoring.

Judge0 compares stdout byte-exact, which fails a correct math answer that
prints ``0.30000000000000004`` instead of ``0.3``. So we treat Judge0's status
as authoritative for *errors* (compile / TLE / runtime), and use our own
comparator to decide *correctness*.
"""
from __future__ import annotations

import math
import re
from typing import List, Optional, Sequence

from app.models import CompareMode

_FLOAT_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


# ── normalisation ────────────────────────────────────────────────────────────

def _strip_trailing(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def normalise(text: Optional[str], mode: CompareMode) -> str:
    if text is None:
        return ""
    if mode == CompareMode.EXACT:
        return text
    if mode == CompareMode.TRIM:
        return _strip_trailing(text)
    if mode == CompareMode.TOKENS:
        return " ".join(text.split())
    if mode == CompareMode.FLOAT:
        return _strip_trailing(text)
    return text


def _float_compare(actual: str, expected: str, rel_tol: float = 1e-6) -> bool:
    a_tokens = _FLOAT_RE.findall(actual)
    e_tokens = _FLOAT_RE.findall(expected)
    if len(a_tokens) != len(e_tokens):
        return False

    # Compare the non-numeric scaffolding too (labels, structure).
    a_skeleton = _FLOAT_RE.sub("#", actual)
    e_skeleton = _FLOAT_RE.sub("#", expected)
    if a_skeleton != e_skeleton:
        return False

    for a, e in zip(a_tokens, e_tokens):
        try:
            if not math.isclose(float(a), float(e), rel_tol=rel_tol, abs_tol=1e-9):
                return False
        except ValueError:
            if a != e:
                return False
    return True


def outputs_match(actual: Optional[str], expected: Optional[str], mode: CompareMode) -> bool:
    if mode == CompareMode.FLOAT:
        if _float_compare(actual or "", expected or ""):
            return True
        return normalise(actual, CompareMode.TRIM) == normalise(expected, CompareMode.TRIM)
    return normalise(actual, mode) == normalise(expected, mode)


# ── scoring ──────────────────────────────────────────────────────────────────

def weighted_score(points: int, results: Sequence) -> int:
    """Partial credit from a list of objects with ``.is_hidden``, ``.passed``,
    ``.weight``.

    score = points * (weight of passed hidden tests / weight of all hidden tests)

    If a question has no hidden tests, every test counts. Returns an int.
    """
    hidden = [r for r in results if getattr(r, "is_hidden", True)]
    pool = hidden if hidden else list(results)
    if not pool:
        return 0

    total_weight = sum(float(getattr(r, "weight", 1.0) or 1.0) for r in pool)
    if total_weight <= 0:
        return 0

    passed_weight = sum(
        float(getattr(r, "weight", 1.0) or 1.0) for r in pool if getattr(r, "passed", False)
    )
    ratio = passed_weight / total_weight
    return int(round(points * ratio))


def count_passed(results: Sequence) -> int:
    return sum(1 for r in results if getattr(r, "passed", False))


def verdict_for(passed: int, total: int, judge_error: bool) -> str:
    from app.models import SubmissionVerdict

    if judge_error:
        return SubmissionVerdict.ERROR
    if total == 0:
        return SubmissionVerdict.FAILED
    if passed == total:
        return SubmissionVerdict.PASSED
    if passed > 0:
        return SubmissionVerdict.PARTIAL
    return SubmissionVerdict.FAILED


# ── what the team is allowed to see ──────────────────────────────────────────

def public_results(results: Sequence, include_hidden_io: bool = False) -> List[dict]:
    """Strip hidden test inputs/outputs before a response leaves the server."""
    out = []
    for r in results:
        hidden = bool(getattr(r, "is_hidden", True))
        row = {
            "passed": bool(getattr(r, "passed", False)),
            "judge_status": getattr(r, "judge_status", None),
            "judge_status_id": getattr(r, "judge_status_id", None),
            "time_seconds": getattr(r, "time_seconds", None),
            "memory_kb": getattr(r, "memory_kb", None),
            "is_hidden": hidden,
            "stdout": getattr(r, "stdout", None),
            "stderr": getattr(r, "stderr", None),
            "compile_output": getattr(r, "compile_output", None),
            "stdin": None,
            "expected_output": None,
        }
        if not hidden or include_hidden_io:
            row["stdin"] = getattr(r, "stdin", None)
            row["expected_output"] = getattr(r, "expected_output", None)
        else:
            # Hidden test: reveal that it exists and whether it passed, but never
            # the input or the expected answer.
            row["stdout"] = None
            row["stderr"] = None
        out.append(row)
    return out
