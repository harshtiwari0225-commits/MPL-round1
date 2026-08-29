from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Event Platform API"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:244901@localhost/MPLBE"
    ADMIN_PASSCODE: str = "admin123"
    EVENT_DURATION_SECONDS: int = 5400  # 1 hour 30 minutes

    class Config:
        env_file = ".env"

settings = Settings()
