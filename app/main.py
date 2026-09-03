from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database import engine, Base
from app.routes import auth, teams, admin, questions, main as main_round
import contextlib

# Import models so that Base.metadata is fully populated before create_all.
from app import models  # noqa: F401


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """Return JSON instead of an HTML 500 so seed.py and the UI can cope."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)[:300]},
    )


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(questions.router, prefix="/api/questions", tags=["questions"])
app.include_router(main_round.router, prefix="/api/main", tags=["main"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
def read_root():
    return {
        "message": "Event Platform API is running",
        "judge_backend": settings.JUDGE_BACKEND,
        "event_duration_seconds": settings.EVENT_DURATION_SECONDS,
    }


@app.get("/health")
def health():
    return {"status": "ok"}
