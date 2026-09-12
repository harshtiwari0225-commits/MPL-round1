from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Event Platform API"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:244901@localhost/mplbe"
    ADMIN_PASSCODE: str = "admin123"

    # ── Event clock ──────────────────────────────────────────────────────────
    # 120 minutes. Admin can add extra minutes per team (extra_time_seconds).
    EVENT_DURATION_SECONDS: int = 7200

    # ── Judge (code execution sandbox) ───────────────────────────────────────
    # "mock"   -> local fake judge, no Docker needed. For development only.
    # "judge0" -> real Judge0 CE instance (self-hosted). Use this on event day.
    JUDGE_BACKEND: str = "mock"

    JUDGE0_URL: str = "http://judge0:2358"
    JUDGE0_AUTH_TOKEN: str = ""          # X-Auth-Token header, set even on internal network
    JUDGE0_TIMEOUT_SECONDS: float = 30.0  # hard cap for one full batch of test cases
    JUDGE0_POLL_INTERVAL: float = 0.4

    # DEV ONLY: lets the mock judge really execute python locally so you can
    # develop questions without Docker. NEVER enable on event day.
    MOCK_EXECUTE_PYTHON: bool = True

    # ── Limits / guardrails ──────────────────────────────────────────────────
    DEFAULT_CPU_TIME_LIMIT: float = 5.0        # seconds per test case
    DEFAULT_WALL_TIME_LIMIT: float = 10.0
    DEFAULT_MEMORY_LIMIT_KB: int = 256_000
    MAX_SOURCE_BYTES: int = 64_000
    SUBMIT_COOLDOWN_SECONDS: int = 5           # protects the judge queue, NOT an attempt limit

    # ── Languages ────────────────────────────────────────────────────────────
    # Our key -> the Judge0 language name we look for in GET /languages.
    # Language IDs differ between Judge0 versions, so we resolve by NAME at
    # startup and only fall back to these hard-coded IDs if that fails.
    LANGUAGE_NAMES: Dict[str, str] = {
        "python": "Python (3.8.1)",
        "c": "C (GCC 9.2.0)",
        "cpp": "C++ (GCC 9.2.0)",
        "java": "Java (OpenJDK 13.0.1)",
    }
    FALLBACK_LANGUAGE_IDS: Dict[str, int] = {
        "python": 71,
        "c": 50,
        "cpp": 54,
        "java": 62,
    }

    class Config:
        env_file = ".env"


settings = Settings()
