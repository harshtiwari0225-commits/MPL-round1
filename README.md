# MPL Event Platform

Backend: FastAPI + SQLAlchemy (async) + PostgreSQL. Code judging: Judge0 CE.
Frontend: static HTML pages, served by the API itself.

**Read §2 before you trust anything here.** It states exactly what has been
tested and what has not.

---

## 1. The game

Three round types exist in MPL:

| Round | Format |
|---|---|---|
| **MAIN** | Coding arena, 3 questions, auto-graded by Judge0 |
| **CHALLENGE** | Single response |
| **BID** | Single response + points wager |

MAIN is split into three question sub-types, one each:

| Sub-type | Meaning |
|---|---|
| `DEBUGGING` | Broken starter code in the editor; fix it |
| `MATH` | Implement a formula; compared with float tolerance |
| `LEETCODE` | Classic DSA problem |

---

## 2. Honest status — read this first

### ✅ Tested and working

Verified by running the API and by executing the frontend's real JavaScript
against a live server:

- Login, session tokens, clock start
- All 3 questions load with per-language starter code
- Run / Submit, partial credit, best-score-wins, no negative marking
- All four output comparators (`EXACT` / `TRIM` / `TOKENS` / `FLOAT`)
- Compilation errors, timeouts, unsupported languages
- Hidden test inputs and answers never leave the server
- Cross-team isolation, 401/403/429 handling
- Admin: test-case CRUD, rejudge, add-time, leaderboard

### ⚠️ NOT verified — needs real hardware

| # | Risk | Detail |
|---|---|---|
| 1 | **The Judge0 client has never talked to a real Judge0** | It was written against the documented API. No Docker was available where it was developed. Language IDs, base64 encoding, batch and polling shapes are plausible but **unproven**. Budget setup time. |
| 2 | **Only Python has ever been executed** | C, C++ and Java paths are written but never compiled or run. |
| 3 | **No load test** | ~10 teams × 4 members was the design target; all testing was sequential. |
| 4 | **`docker-compose.judge0.yml` is untested** | A trimmed starting point. Compare against the official Judge0 compose file before the event. |

### 🔒 Known limitations (by design, for now)

- **The mock judge is not a sandbox.** With `JUDGE_BACKEND=mock` it runs Python
  in a subprocess on your own machine. Fine for your own code while developing;
  never use it on event day.
- **Legacy IDOR remains**: `GET /api/teams/{id}/status` and
  `/time-remaining` take a raw team id with no credential. The challenge and
  boost pages depend on them. Migrate those pages to `X-Team-Token`, then lock
  them down.
- **No database migrations.** Schema changes require `python reset_db.py`.
  Fine before the event; destructive during it.
- **No rate limiting** beyond the per-question submit cooldown.
- **No plagiarism / copy-paste detection.**
- **Committed secrets**: `app/core/config.py` still holds a default DB URL and
  admin passcode. `.env` is gitignored — but rotate before the event.

---

## 3. Repository structure

```
app/
  main.py              FastAPI app, CORS, static mount at /ui, lifespan
  database.py          async engine, session factory, Base
  models.py            ORM models (all tables)
  schemas.py           Pydantic request/response models
  core/
    config.py          all settings, read from .env
  routes/
    auth.py            POST /api/auth/login
    main.py            MAIN round: questions, run, submit, clock
    questions.py       public question reads (hidden tests stripped)
    teams.py           legacy status + time-remaining (IDOR, see §2)
    admin.py           teams, questions, test cases, submissions,
                       rejudge, leaderboard, add-time, judge health
  services/
    judge.py           MockJudge + Judge0Client behind one interface
    scoring.py         output comparison + partial-credit maths
    access.py          team token auth + clock helpers

frontend/
  index.html           arena hub
  main.html            MAIN round coding console  ← the editor
  boost.html           time boost page (legacy round)
  challenge.html       challenge page (legacy round)
  admin.html           admin panel

seed.py                demo teams + 3 demo questions with test cases
reset_db.py            drop and recreate all tables (dev)
create_team.py         CLI to add one team
docker-compose.judge0.yml   Judge0 CE stack
docs/                  MPL_Judge0_Overview.md
```

### Data model

| Table | Purpose |
|---|---|
| `teams` | name, passcode, `session_token`, points, `timer_start_time`, `extra_time_seconds` |
| `questions` | MAIN / TIME_BOOST / CHALLENGE; `sub_type`, `starter_code` (JSON per language), `compare_mode`, `points`, limits |
| `test_cases` | per question: `stdin`, `expected_output`, `is_hidden`, `weight` |
| `team_question_states` | per team per question: `best_score`, `attempts`, status. **Unique on (team_id, question_id)** |
| `submissions` | one Run or Submit: source, language, verdict, score, `score_delta` |
| `submission_results` | per-test outcome: status, stdout, stderr, compile output |
| `challenge_sessions` | legacy head-to-head (unused by MAIN) |

---

## 4. Running the backend locally

### First time

```powershell
cd D:\projects\MPL_BE
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Every time

```powershell
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### One-time database setup

```powershell
python reset_db.py     # creates all tables (DESTRUCTIVE - only during setup)
python seed.py         # 3 demo teams + 3 demo questions
```

After that, re-running `seed.py` is safe — existing teams and questions are
skipped. It is **not** safe to run `reset_db.py` once the event has started.

### Using PostgreSQL instead of SQLite

SQLite needs no setup and is fine for development. For the event, use Postgres
so foreign keys are actually enforced:

```powershell
psql -U postgres -c "CREATE DATABASE mplbe;"
```

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mplbe
```

⚠️ Use lowercase `mplbe` in **both** places. Postgres folds unquoted names to
lowercase, so a database created as `MPLBE` is really `mplbe`, and connecting
to `MPLBE` then fails.

### Health checks

```
http://localhost:8000/                        → service info
http://localhost:8000/health                  → {"status":"ok"}
http://localhost:8000/docs                    → interactive API docs
```

---

## 5. Running the frontend locally

**The API serves the frontend.** No second server, no Live Server, no CORS.

```
http://localhost:8000/ui/main.html      coding console
http://localhost:8000/ui/index.html     arena hub
http://localhost:8000/ui/admin.html     admin panel
```

If you would rather run a static server while editing HTML/CSS (Live Server,
`python -m http.server 5500`, etc.), that still works — the pages detect
`localhost` and point API calls at port 8000 automatically. But **keep the API
on port 8000.**

### Demo credentials

| Team | Passcode |
|---|---|
| Team Alpha | `alpha123` |
| Team Beta | `beta123` |
| Team Gamma | `gamma123` |

Admin passcode: `admin123`

---

## 6. Environment variables

Copy `.env.example` to `.env`. All settings:

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | postgres… | SQLAlchemy async URL |
| `ADMIN_PASSCODE` | `admin123` | **Change before the event** |
| `EVENT_DURATION_SECONDS` | `7200` | 120 minutes |
| `JUDGE_BACKEND` | `mock` | `mock` or `judge0` |
| `JUDGE0_URL` | `http://judge0:2358` | Judge0 base URL |
| `JUDGE0_AUTH_TOKEN` | empty | `X-Auth-Token` sent to Judge0 |
| `JUDGE0_TIMEOUT_SECONDS` | `30` | hard cap for one test batch |
| `JUDGE0_POLL_INTERVAL` | `0.4` | seconds between polls |
| `MOCK_EXECUTE_PYTHON` | `true` | **dev only** — really runs Python locally |
| `DEFAULT_CPU_TIME_LIMIT` | `5` | seconds per test case |
| `DEFAULT_WALL_TIME_LIMIT` | `10` | seconds wall clock |
| `DEFAULT_MEMORY_LIMIT_KB` | `256000` | ~250 MB |
| `MAX_SOURCE_BYTES` | `64000` | source size cap |
| `SUBMIT_COOLDOWN_SECONDS` | `5` | guard for the judge queue, **not** an attempt limit |

---

## 7. API reference

### Team routes — require header `X-Team-Token` (returned by login)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | returns `session_token`; starts the clock on first login |
| GET | `/api/main/questions` | the 3 questions, visible tests, starter code, your best score |
| POST | `/api/main/run` | run against sample tests only — **never scores** |
| POST | `/api/main/submit` | run all tests, award partial credit |
| GET | `/api/main/submissions` | your own history |
| GET | `/api/main/clock` | your remaining time |
| GET | `/api/questions/{id}` | public question (no test cases) |
| GET | `/api/questions/{id}/sample-tests` | visible tests only |

### Admin routes — require header `admin-passcode`

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/admin/teams` | create team |
| GET | `/api/admin/teams` | list teams |
| POST | `/api/admin/teams/{id}/add-time` | add seconds (`id=0` = every team) |
| POST | `/api/admin/questions` | create question |
| PATCH | `/api/admin/questions/{id}` | edit any question field |
| POST | `/api/admin/questions/{id}/test-cases?replace=true` | bulk-add test cases |
| GET | `/api/admin/questions/{id}/test-cases` | list (includes hidden) |
| DELETE | `/api/admin/test-cases/{id}` | delete one |
| GET | `/api/admin/submissions` | all submissions |
| GET | `/api/admin/submissions/{id}` | one submission + per-test detail |
| POST | `/api/admin/submissions/{id}/rejudge` | re-run and rescore |
| GET | `/api/admin/leaderboard` | standings (no auth) |
| GET | `/api/admin/judge/health` | is the judge up? **Check this on event day.** |

Legacy routes still present for the challenge/boost pages:
`POST /api/admin/challenge/create`, `POST /api/admin/teams/{id}/assign-boost`,
`POST /api/admin/review/mark-solved`.

### How grading works

- **Judge0 is authoritative for errors** (compile error, TLE, runtime error).
- **Our comparator is authoritative for correctness**, using the question's
  `compare_mode`. So `0.30000000000000004` passes an expected `0.3` on a
  `FLOAT` question, and a trailing newline never fails a `TRIM` question.
- **Partial credit**: `points × passed_hidden_weight / total_hidden_weight`.
- **Unlimited attempts, no negative marking.** A team's score for a question is
  the **best** score across all attempts; points increase only by the
  improvement delta.
- Judge0 status 13 (internal error) never changes a score — use rejudge.

---

## 8. Setting up Judge0 — for whoever owns the machine

**This is the one part that cannot be done by copy-pasting from this repo.**
Read §2 risk #1 first: the client is written but unproven.

### 8.1 Requirements

- Docker Desktop (Windows: WSL 2 backend enabled)
- ~8 GB RAM free, ~6 GB disk
- A machine that will **stay awake for the whole event** — set power options to
  never sleep, and disable sleep on lid close

### 8.2 Start it

```powershell
cd D:\projects\MPL_BE
docker compose -f docker-compose.judge0.yml up -d
```

First boot pulls several GB and runs a DB migration. **Wait 60–90 seconds**, then:

```powershell
curl http://127.0.0.1:2358/languages
```

A JSON list of languages means it is alive. If it fails, wait another 60s.

### 8.3 Point the API at it

In `.env`:

```env
JUDGE_BACKEND=judge0
JUDGE0_URL=http://127.0.0.1:2358
JUDGE0_AUTH_TOKEN=<same value as AUTHN_TOKEN in the compose file>
MOCK_EXECUTE_PYTHON=false
```

Restart the API, then verify:

```powershell
curl -H "admin-passcode: admin123" http://localhost:8000/api/admin/judge/health
```

You want `"healthy": true` **and** a resolved language map such as:

```json
{"languages": {"python": 71, "c": 50, "cpp": 54, "java": 62}}
```

Language IDs are resolved **by name** from `GET /languages`, with a hard-coded
fallback table, because IDs differ between Judge0 versions.

### 8.4 Prove all four languages

Open `http://localhost:8000/ui/main.html`, log in, and submit a known-good
solution in **Python, C, C++ and Java**. All four must come back `PASSED`.

### 8.5 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `docker compose` not recognised | Docker not running | Start Docker Desktop first |
| `/languages` times out | Still migrating | Wait 60–90s and retry |
| `healthy: false` | Wrong URL or Judge0 down | `docker compose ps`, check logs |
| "No Judge0 language id resolved for X" | Name mismatch | Run `curl http://127.0.0.1:2358/languages`, compare names to `LANGUAGE_NAMES` in `app/core/config.py`, adjust and restart |
| Every submit returns `ERROR` | Client/contract mismatch | Check the API log for the Judge0 HTTP error — that message will point at the fix in `app/services/judge.py` |
| Everything queues forever | Workers not running | `docker compose ps` — `judge0-workers` must be up |
| Compile errors in C/C++ on Windows | — | Expected if you have no local compiler under `mock`; under `judge0` the sandbox provides them |

### 8.6 Security notes for the event

- Keep Judge0 bound to `127.0.0.1`. **Do not publish port 2358** to the venue
  network — only the FastAPI process should reach it.
- Use Judge0 **v1.13.1 or newer**.
- Set a real `JUDGE0_AUTH_TOKEN` / `AUTHN_TOKEN` even on an internal network.
- Compare `docker-compose.judge0.yml` with the official compose file before the
  event; ours is trimmed.

---

## 9. The code editor — `frontend/main.html`

### What it does

- Monaco editor with syntax highlighting; language switcher (Python / C / C++ / Java)
- Three question tabs showing sub-type, points, attempts and best score
- Problem statement and sample tests panel
- **▶ Run Samples** (visible tests, never scores) and **⚡ Submit** (all tests)
- `Ctrl+Enter` submits
- Per-test results: pass/fail, judge status, and for sample tests
  input / expected / your output; hidden tests show pass or fail only
- Live countdown clock, points and best-score pills
- **Drafts persist** per question *and* per language in `localStorage`, so
  switching tabs or languages never loses work

### Honest state of the editor

**Verified** by executing the page's real JavaScript against a live API:
login → questions load → starter code loads per language → submit buggy code
fails → submit correct code scores → switching questions and languages swaps
the starter code → Run Samples works independently of scoring.

**Not verified / known gaps:**

| Gap | Detail |
|---|---|
| **Monaco needs the internet** | It loads from jsDelivr. If that is blocked or slow (8s timeout), the page silently falls back to a plain textarea. Code still runs and scores normally. To go fully offline, download `monaco-editor@0.52.2/min/vs` into `frontend/vendor/monaco/` and repoint the two CDN URLs. |
| **Never executed C/C++/Java** | Only Python has ever run. Under `judge0` all four should work; unproven. |
| **Session is per tab** | The token lives in `sessionStorage`. Opening a second tab means logging in again. |
| **Not designed for phones** | It's a desktop layout. |
| **The clock does not auto-submit** | At 0:00 the API rejects new submits with 403, but nothing is submitted on your behalf. |
| **Old `main.html` is gone** | Replaced by this console. The previous version is in git history. |

---

## 10. Event-day checklist

**The day before**

- [ ] `docker compose -f docker-compose.judge0.yml up -d`
- [ ] `curl http://127.0.0.1:2358/languages` answers
- [ ] `.env` has `JUDGE_BACKEND=judge0` and `MOCK_EXECUTE_PYTHON=false`
- [ ] `GET /api/admin/judge/health` → healthy, with all 4 language IDs
- [ ] Submit a known-good solution in **all four languages**
- [ ] Load your real questions and hidden tests
- [ ] Power settings: never sleep, lid close does nothing
- [ ] Run a rehearsal with 3–4 people submitting at once

**On the day**

- [ ] Start Judge0, wait for `/languages`, then start the API
- [ ] `GET /api/admin/judge/health` one more time
- [ ] `reset_db.py` + `seed.py` **before** doors open — never during
- [ ] Keep `/api/admin/leaderboard` open for the projector
- [ ] If Judge0 dies: submissions return `ERROR` with no score change. Fix it,
      then use `POST /api/admin/submissions/{id}/rejudge` on affected attempts.

---

## 11. Adding real questions

Use the admin API rather than editing `seed.py`:

```powershell
# 1. create
curl -X POST http://localhost:8000/api/admin/questions `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '{"title":"Two Sum","description":"...","type":"MAIN","sub_type":"LEETCODE",
       "points":500,"compare_mode":"TRIM",
       "allowed_languages":"[\"python\",\"c\",\"cpp\",\"java\"]"}'

# 2. test cases - is_hidden:false shows as a sample in the editor
curl -X POST "http://localhost:8000/api/admin/questions/1/test-cases?replace=true" `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '[{"stdin":"4\n2 7 11 15\n9","expected_output":"0 1","is_hidden":false,"position":0},
       {"stdin":"3\n3 2 4\n6","expected_output":"1 2","is_hidden":true,"position":1}]'

# 3. starter code, one entry per language
curl -X PATCH http://localhost:8000/api/admin/questions/1 `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '{"starter_code":"{\"python\":\"n=int(input())\\n\",\"cpp\":\"#include <iostream>\\n\"}"}'
```

**Guidelines**

- Use `compare_mode: "FLOAT"` for anything numeric
- Always include at least one **visible** test so Run Samples does something
- 3–5 hidden tests is plenty — each is a separate sandbox run
- Write starter code for all four languages
- Questions must read stdin and write stdout

---

## 12. Working on this repo

```powershell
git fetch origin
git checkout arena/01a04cdf-test-be
git pull origin arena/01a04cdf-test-be
```

`main` still holds the original code. Open a pull request from
`arena/01a04cdf-test-be` when the MAIN round is proven end to end.
