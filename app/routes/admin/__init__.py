"""Admin API — require header `admin-passcode` (see deps.py).

Split into one module per domain so every file stays small. This package
assembles the sub-routers into a single ``router`` that app/main.py mounts
at /api/admin, exactly as before:

    teams.py        create/list teams, add-time
    questions.py    create/patch questions
    testcases.py    test-case CRUD (admin sees hidden tests)
    submissions.py  submission list/detail, rejudge
    leaderboard.py  standings, judge health
    legacy.py       CHALLENGE / TIME_BOOST endpoints (unchanged legacy flow)
"""
from fastapi import APIRouter

from app.routes.admin.teams import router as teams_router
from app.routes.admin.questions import router as questions_router
from app.routes.admin.testcases import router as testcases_router
from app.routes.admin.submissions import router as submissions_router
from app.routes.admin.leaderboard import router as leaderboard_router
from app.routes.admin.legacy import router as legacy_router

router = APIRouter()
router.include_router(teams_router)
router.include_router(questions_router)
router.include_router(testcases_router)
router.include_router(submissions_router)
router.include_router(leaderboard_router)
router.include_router(legacy_router)
