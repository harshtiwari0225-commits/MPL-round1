# Refactor notes — ≤200-line file structure

This folder is a **structural refactor** of `MPL-round1`. No endpoint, request
shape, response shape, scoring rule, or game behaviour was changed. Every
backend Python file is now within 200 lines (largest: 173).

## What was split, and how

| Before (lines) | After | Rule used |
|---|---|---|
| `app/models.py` (234) | `app/models/` package: `enums.py`, `team.py`, `question.py`, `progress.py`, `submission.py`, `challenge.py` | one module per aggregate |
| `app/schemas.py` (200) | `app/schemas/` package: `questions.py`, `teams.py`, `submissions.py`, `admin.py` | one module per domain |
| `app/services/judge.py` (510) | `app/services/judge/` package: `base.py`, `execution.py`, `mock.py`, `client.py`, `polling.py` | DTOs / subprocess helpers / two backends / polling loop |
| `app/routes/main.py` (457) | thin `routes/main.py` (101) + services: `arena.py`, `judging.py`, `validation.py`, `progress.py`, `results.py`, `questions.py` | route = HTTP shell, service = pipeline |
| `app/routes/admin.py` (538) | `app/routes/admin/` package: `deps.py`, `teams.py`, `questions.py`, `testcases.py`, `submissions.py`, `leaderboard.py`, `legacy.py` + `services/rejudge.py` | one module per domain; rejudge pipeline moved to a service |
| `seed.py` (333) | thin `seed.py` (85) + `seeding/starters.py`, `seeding/questions.py` | data blobs out of the entry point |

`app/main.py`, `database.py`, `core/config.py`, `routes/auth.py`,
`routes/questions.py`, `routes/teams.py`, `services/access.py`,
`services/scoring.py` (only `score_submission()` added, moved verbatim from
the old `routes/main.py::_score`), `reset_db.py`, `create_team.py`, the whole
`frontend/`, `docs/`, and the compose file are unchanged.

## Why imports still work

Each new package has an `__init__.py` that re-exports the old public names, so
**every existing import statement in the codebase (and any external script)
keeps working unchanged**:

```python
from app.models import Team, Question, TestCase  # same as before
from app.schemas import SubmissionOut, TeamLogin  # same as before
from app.services.judge import JudgeJob, get_judge  # same as before
from app.routes import admin  # admin.router assembled in __init__
```

`app/main.py` was not touched: it still does `from app import models`
(registers all tables on `Base.metadata`) and mounts `admin.router` at
`/api/admin`.

## Where the logic went (route → service map)

| Old location | New location |
|---|---|
| `routes/main.py::_judge` | `services/judging.py::judge_submission` |
| `routes/main.py::list_main_questions` body | `services/arena.py::team_question_views` |
| `routes/main.py::_score` | `services/scoring.py::score_submission` |
| `routes/main.py::_build_result` | `services/results.py::build_result` |
| `routes/main.py::_get_state` | `services/progress.py::get_state` |
| `routes/main.py` best-score delta block | `services/progress.py::apply_score` |
| `routes/main.py` judge-error attempt block | `services/progress.py::record_error_attempt` |
| `routes/main.py::_allowed_languages` / `_starter_code` | `services/questions.py` (+ `starter_bundle`) |
| `routes/main.py` inline guards (404/400/413/429, case selection) | `services/validation.py` |
| `routes/admin.py::rejudge` body | `services/rejudge.py::rejudge_submission` |
| `routes/admin.py::verify_admin` | `routes/admin/deps.py` |
| `services/judge.py::MockJudge._execute/_compile_and_run` | `services/judge/execution.py::execute/compile_and_run` |
| `services/judge.py::Judge0Client._poll` | `services/judge/polling.py::poll_outcomes` |
| `seed.py` starter blobs / question payloads | `seeding/starters.py` / `seeding/questions.py` |

Bodies were moved verbatim; only names/imports changed (`_score` →
`score_submission`, `_build_result` → `build_result`, etc.). The rejudge score
reconciliation intentionally keeps its own (slightly different) best-score
logic, exactly as before — it was not unified with `apply_score`.

## Verified how

1. `python -m compileall` on the whole tree — clean.
2. Line-count audit — every `.py` ≤ 200 (max 173).
3. **Behavioural diff**: the original and refactored apps were both booted
   (SQLite + mock judge, Python execution on) and driven through the same
   ~45-step API script: login/token rotation, 401/403/400/413/429 guards,
   questions payload (hidden tests stripped), Run vs Submit, partial credit on
   the FLOAT question, best-score delta, rejudge (incl. 400 on a Run),
   add-time, leaderboard, judge health, test-case CRUD, legacy
   boost/challenge/mark-solved flows, `/ui` static serving. Normalised
   responses (timestamps/tokens/volatile seconds masked) are identical.

## Frontend

`frontend/*.html` were deliberately **not** touched (they are frontend, not
backend files). They are single-page files far above 200 lines; splitting them
is a separate task if you want the same rule applied there.
