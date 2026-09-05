# MPL Event Platform — Backend

FastAPI + SQLAlchemy(async) + Judge0.

Three round types exist in the game: **MAIN** (coding, Judge0-graded), **CHALLENGE**
and **BID** (both single-response). **This build implements MAIN only** — challenge
and bid are untouched, as agreed.

---

## 1. Run it locally Docker yet to be implemented)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./mpl.db
ADMIN_PASSCODE=admin123
EVENT_DURATION_SECONDS=7200
JUDGE_BACKEND=mock          # runs your code locally, no Docker
MOCK_EXECUTE_PYTHON=true
SUBMIT_COOLDOWN_SECONDS=5
```

Then:

```powershell
uvicorn app.main:app --reload --port 8000     # terminal 1
python seed.py                                # terminal 2
```

Open:

- API docs → http://localhost:8000/docs
- Leaderboard → http://localhost:8000/api/admin/leaderboard

The frontend pages hardcode `http://localhost:8000`, so keep the API on that port.

The MAIN round console is `frontend/main.html` — a Monaco code editor with
language switching, Run Samples / Submit, per-test results and a live clock:

```powershell
cd frontend
python -m http.server 5500
# then open http://localhost:5500/main.html
```

Monaco is loaded from a CDN. If the venue has no internet the page
automatically falls back to a plain text editor — the code still runs and
scores normally. To make Monaco work offline, download
`monaco-editor@0.52.2/min/vs` into `frontend/vendor/monaco/` and point the two
CDN URLs in `main.html` at that folder.

Whenever the schema changes during development:

```powershell
python reset_db.py
python seed.py
```

---

## 2. Switching to real Judge0

```powershell
docker compose -f docker-compose.judge0.yml up -d
curl http://127.0.0.1:2358/languages          # wait until this answers
```

Then in `.env`:

```env
JUDGE_BACKEND=judge0
JUDGE0_URL=http://127.0.0.1:2358
JUDGE0_AUTH_TOKEN=<same value as AUTHN_TOKEN in the compose file>
MOCK_EXECUTE_PYTHON=false
```

Verify: `GET /api/admin/judge/health` with the `admin-passcode` header.

**Nothing else changes.** Every route talks to `get_judge()`, so the swap is one
env var.

> The compose file here is a trimmed starting point — compare it with the official
> Judge0 compose file before the event and keep the image at **v1.13.1+**.

---

## 3. How MAIN works

Each team gets **3 questions**, one of each sub-type, each with its own points:

| Sub-type | What it is |
|---|---|
| `DEBUGGING` | Broken starter code in the editor; fix it |
| `MATH` | Implement a formula; compared with float tolerance |
| `LEETCODE` | Classic DSA problem |

Languages: **Python, C, C++, Java** (configurable per question via `allowed_languages`).

### Scoring

- **Partial credit** — pass 20% of the hidden tests, get 20% of the points
- **Unlimited attempts**, no negative marking
- A team's score for a question is the **best** score across all attempts
- Points are only ever added when the best score improves (delta, not the raw score)

### Run vs Submit

| | `/api/main/run` | `/api/main/submit` |
|---|---|---|
| Tests used | visible only | visible + hidden |
| Writes score | never | yes |
| Counts as attempt | no | yes |
| Cooldown | none | `SUBMIT_COOLDOWN_SECONDS` |

### Who decides what

- **Judge0** is authoritative for *errors*: compile error, TLE, runtime error
- **Our comparator** is authoritative for *correctness*, using the question's
  `compare_mode` (`EXACT` / `TRIM` / `TOKENS` / `FLOAT`). So `0.30000000000000004`
  passes against an expected `0.3` on a FLOAT question, and a trailing newline
  never fails a TRIM question.

### Failure policy

| Situation | Behaviour |
|---|---|
| Judge0 unreachable | Submission stored as `ERROR`, no score change, team retries |
| Judge0 status 13 (internal error) | No score change; use `POST /api/admin/submissions/{id}/rejudge` |
| Team clock expired | `403` on run and submit |
| Admin adds minutes | `POST /api/admin/teams/{id}/add-time` (use `0` for all teams) |

---

## 4. Endpoints

### Team (requires `X-Team-Token`, issued at login)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | returns `session_token` |
| GET | `/api/main/questions` | the 3 questions, visible tests, starter code, your best score |
| POST | `/api/main/run` | run against sample tests |
| POST | `/api/main/submit` | run against all tests, award partial credit |
| GET | `/api/main/submissions` | your own history |
| GET | `/api/main/clock` | your remaining time |

### Admin (requires `admin-passcode` header)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/admin/teams` | create team |
| GET | `/api/admin/teams` | list teams |
| POST | `/api/admin/teams/{id}/add-time` | add minutes (`id=0` = all teams) |
| POST | `/api/admin/questions` | create question |
| PATCH | `/api/admin/questions/{id}` | edit any question field |
| POST | `/api/admin/questions/{id}/test-cases?replace=true` | bulk-add test cases |
| GET | `/api/admin/questions/{id}/test-cases` | list (includes hidden) |
| DELETE | `/api/admin/test-cases/{id}` | delete one |
| GET | `/api/admin/submissions` | all submissions |
| GET | `/api/admin/submissions/{id}` | one submission + per-test detail |
| POST | `/api/admin/submissions/{id}/rejudge` | re-run and rescore |
| GET | `/api/admin/leaderboard` | standings |
| GET | `/api/admin/judge/health` | is the judge up? |

---

## 5. Security notes

- Hidden test inputs and expected outputs **never** leave the server. The submit
  response blanks `stdin`, `expected_output` and `stdout` for hidden rows (you
  still see *that* a hidden test passed or failed).
- `GET /api/questions/{id}` no longer returns `test_cases` — it used to hand the
  whole test bank to anyone.
- Team routes require `X-Team-Token`. The two legacy routes
  `GET /api/teams/{id}/status` and `/time-remaining` still take a raw id with no
  credential — the challenge/boost pages depend on them. Migrate those pages to
  the token and then lock them down.
- Move the DB password and admin passcode out of `app/core/config.py` before the
  event; `.env` is gitignored, the committed defaults are not a secret any more.

---

## 6. Known gaps (deliberately not done yet)

- CHALLENGE and BID rounds — untouched, per your instruction
- Legacy `/api/teams/{id}/*` IDOR
- No Alembic migrations — `reset_db.py` is the dev workflow
- No rate limiting beyond the per-question submit cooldown
- No plagiarism / copy-paste detection
