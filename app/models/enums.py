"""All enums used by the ORM models.

Kept in one module so models and schemas can share them without cycles.
"""

import enum


class QuestionType(str, enum.Enum):
    MAIN = "MAIN"
    TIME_BOOST = "TIME_BOOST"
    CHALLENGE = "CHALLENGE"


class MainSubType(str, enum.Enum):
    """The three flavours of MAIN coding question."""

    DEBUGGING = "DEBUGGING"  # broken starter code, fix it
    MATH = "MATH"  # implement a formula / numeric routine
    LEETCODE = "LEETCODE"  # classic DSA problem


class CompareMode(str, enum.Enum):
    """How stdout is compared against the expected output.

    Judge0 compares byte-exact. We do our own comparison so that math
    questions are not failed by '0.30000000000000004' vs '0.3'.
    """

    EXACT = "EXACT"  # byte-for-byte
    TRIM = "TRIM"  # strip trailing whitespace on each line + trailing blank lines
    TOKENS = "TOKENS"  # whitespace-insensitive token compare
    FLOAT = "FLOAT"  # numeric compare with tolerance (1e-6 relative)


class QuestionDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class QuestionStateStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    SOLVED = "SOLVED"
    FAILED = "FAILED"


class ChallengeStatus(str, enum.Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"


class SubmissionVerdict(str, enum.Enum):
    QUEUED = "QUEUED"
    JUDGING = "JUDGING"
    PASSED = "PASSED"  # every hidden test accepted
    PARTIAL = "PARTIAL"  # some hidden tests accepted (partial credit)
    FAILED = "FAILED"  # ran, but no hidden test accepted
    ERROR = "ERROR"  # judge internal error / unreachable. No score change.
