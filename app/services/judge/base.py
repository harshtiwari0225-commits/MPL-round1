"""Shared DTOs and Judge0 status constants.

Judge0 status ids (see docs/MPL_Judge0_Overview.md):
    1 In Queue | 2 Processing | 3 Accepted | 4 Wrong Answer | 5 TLE
    6 Compilation Error | 7-12 Runtime Error | 13 Internal Error | 14 Exec Format
"""

from __future__ import annotations

from dataclasses import dataclass

# Status ids we treat as "keep polling"
PENDING_STATUS_IDS = (1, 2)
STATUS_ACCEPTED = 3
STATUS_WRONG_ANSWER = 4
STATUS_TIME_LIMIT = 5
STATUS_COMPILATION_ERROR = 6
STATUS_INTERNAL_ERROR = 13


@dataclass
class JudgeJob:
    """One test case: run `source_code` with `stdin`, compare to `expected_output`."""

    source_code: str
    language: str  # our key: python / c / cpp / java
    stdin: str = ""
    expected_output: str = ""
    cpu_time_limit: float = 5.0
    wall_time_limit: float = 10.0
    memory_limit_kb: int = 256_000


@dataclass
class JudgeOutcome:
    status_id: int
    status: str
    stdout: str | None = None
    stderr: str | None = None
    compile_output: str | None = None
    time: float | None = None
    memory: float | None = None
    message: str | None = None
    token: str | None = None

    @property
    def is_pending(self) -> bool:
        return self.status_id in PENDING_STATUS_IDS

    @property
    def accepted(self) -> bool:
        return self.status_id == STATUS_ACCEPTED
