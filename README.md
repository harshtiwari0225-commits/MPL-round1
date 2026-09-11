# MPL Round 1 — Event Platform

FastAPI + SQLAlchemy (async) backend for the MPL technical round. Untrusted
team code is executed by a self-hosted Judge0 CE sandbox; a static HTML
frontend is served by the API itself. PostgreSQL is the event database,
SQLite is supported for development.

This folder contains the restructured backend: every Python module is under
200 lines, with logic moved into `app/services/` and `app/routes/` packages.
`REFACTOR_NOTES.md` maps each old file to its new location and records the
verification method. The Judge0 design contract is `docs/MPL_Judge0_Overview.md`
(referenced by section number below).

All commands in this README target Windows (PowerShell; `cmd` differences are
noted inline). macOS/Linux equivalents are summarised at the end of §2.

---

## 1. Folder structure

```
app/
  main.py                FastAPI app: CORS, static mount at /ui, router wiring
  database.py            async engine, session factory, Base
  core/
    config.py            all settings, loaded from .env
  models/                ORM models, one module per aggregate
    enums.py             QuestionType, CompareMode, SubmissionVerdict, ...
    team.py              Team
    question.py          Question, TestCase
    progress.py          TeamQuestionState
    submission.py        Submission, SubmissionResult
    challenge.py         ChallengeSession
    __init__.py          re-exports every model (existing import paths unchanged)
  schemas/               Pydantic schemas, one module per domain
    questions.py  teams.py  submissions.py  admin.py  __init__.py
  routes/
    auth.py              POST /api/auth/login
    main.py              MAIN round endpoints (thin; logic lives in services/)
    questions.py         public question reads (hidden tests stripped)
    teams.py             legacy status + time-remaining (unauthenticated; see §7)
    admin/               admin API, one module per domain
      deps.py            admin-passcode header check
      teams.py           create/list teams, add-time
      questions.py       create/patch questions
      testcases.py       test-case CRUD (admin sees hidden tests)
      submissions.py     submission list/detail, rejudge
      leaderboard.py     standings, judge health
      legacy.py          challenge/boost endpoints (unchanged legacy flow)
      __init__.py        assembles the sub-routers into one router
  services/
    judge/               MockJudge and Judge0Client behind one interface
      base.py            JudgeJob/JudgeOutcome DTOs + status-id constants
      execution.py       local subprocess helpers (mock backend only)
      mock.py            MockJudge
      client.py          Judge0Client: batch submit over HTTP
      polling.py         batch polling loop + base64 decoding
      __init__.py        get_judge()/reset_judge() factory + re-exports
    scoring.py           output comparison (4 modes) + partial-credit maths
    access.py            team-token auth + clock helpers
    questions.py         starter-code / allowed-language helpers
    validation.py        run/submit guards (404/400/413/429 before executing)
    progress.py          TeamQuestionState rows + best-score accounting
    results.py           judge outcome -> SubmissionResult mapping
    arena.py             builds the GET /api/main/questions payload
    judging.py           the run/submit pipeline
    rejudge.py           the admin rejudge pipeline

frontend/
  index.html             arena hub
  main.html              MAIN round coding console (the editor)
  challenge.html         challenge page (legacy round)
  boost.html             time-boost page (legacy round)
  admin.html             admin panel (predates the current admin API)

seed.py                  seeding entry point: seeds via the admin API
seeding/                 seed data (starters.py, questions.py)
reset_db.py              drop and recreate all tables (development only)
create_team.py           CLI to add one team
tools/
  smoke_test.py          65-step end-to-end regression against a running API
docs/
  MPL_Judge0_Overview.md Judge0 design contract (workflow, security, decisions)
docker-compose.judge0.yml  Judge0 CE stack (server, workers, Postgres, Redis)
.env.example             configuration template
REFACTOR_NOTES.md        old -> new file map for the restructure
```

`.idea/` (JetBrains settings) was carried over from the original repository
and can be deleted.

---

## 2. Running in development

Requirements: Windows 10/11, Python 3.11 or newer (tested on 3.13; check with
`python --version`). No Docker and no Postgres needed — the default judge
backend is `mock`. If `python` is not recognised, use the `py` launcher in its
place throughout (`py -m venv .venv`, `py seed.py`, ...).

```powershell
cd path\to\MPL-round1-refactored

# 1. virtual environment + dependencies
python -m venv .venv
.venv\Scripts\Activate.ps1           # cmd: .venv\Scripts\activate.bat
pip install -r requirements.txt

# 2. configuration
Copy-Item .env.example .env          # cmd: copy .env.example .env
```

If activation fails with "running scripts is disabled on this system", allow
local scripts for your user once, then activate again:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Edit `.env` for zero-setup development: comment out the PostgreSQL
`DATABASE_URL` line and uncomment the SQLite line
(`DATABASE_URL=sqlite+aiosqlite:///./mpl.db`). The remaining defaults
(`JUDGE_BACKEND=mock`, `MOCK_EXECUTE_PYTHON=true`) are correct for development.

```powershell
# 3. database (first time, or to wipe state)
python reset_db.py                   # creates all tables — destructive
python seed.py                       # 3 demo teams + 3 MAIN questions

# 4. start the API (run from this folder root)
uvicorn app.main:app --reload --port 8000
```

Verify:

| URL | Expected |
|---|---|
| `http://localhost:8000/health` | `{"status":"ok"}` |
| `http://localhost:8000/docs` | interactive API docs |
| `http://localhost:8000/ui/main.html` | coding console |

Demo credentials — teams `Team Alpha` / `alpha123`, `Team Beta` / `beta123`,
`Team Gamma` / `gamma123`; admin passcode `admin123`.

End-to-end behavioural snapshot of the running API:

```powershell
python reset_db.py                      # the tool expects a freshly seeded DB
python seed.py
python tools\smoke_test.py http://127.0.0.1:8000 | Out-File -Encoding utf8 snapshot.json
```

`Out-File -Encoding utf8` avoids Windows PowerShell 5.1's default UTF-16
redirect, keeping snapshots comparable across runs and machines.

It records 65 steps — login, question loading, run, submit, partial credit,
resubmit after an admin edit, cooldown, rejudge, leaderboard, access control,
static serving — with volatile values masked (timestamps, tokens, remaining
seconds). Two fresh, identically seeded servers must produce byte-identical
output; this is how the restructure was proven behaviourally identical to the
original backend. Re-running against a used database will differ legitimately,
because scores and timers have moved.

**PostgreSQL** (event configuration): create the database once
(`psql -U postgres -c "CREATE DATABASE mplbe;"` — `psql` is on the PATH after
a default PostgreSQL for Windows installation) and keep the PostgreSQL
`DATABASE_URL` in `.env`. The database name must be lowercase in both places —
Postgres folds unquoted identifiers, so a database created as `MPLBE` is
really `mplbe`.

Re-running `seed.py` is idempotent (existing rows are skipped). Never run
`reset_db.py` once the event has started; there are no migrations.

macOS/Linux: identical procedure except `source .venv/bin/activate`,
`cp .env.example .env`, and forward-slash paths (`tools/smoke_test.py`).

---

## 3. Judge0 integration — status and remaining work

The sandbox contract is `docs/MPL_Judge0_Overview.md`. The client is
implemented in `app/services/judge/`, selected by `JUDGE_BACKEND`.

**The Judge0 path has never been executed against a real Judge0 instance.**
Docker was unavailable in the development environment, so all verification
(mock backend, 65-step parity suite) covered everything except the HTTP
contract with Judge0 itself. Treat §3.2 as mandatory pre-event work.

### 3.1 Implemented, per the overview plan

| Plan requirement | Where | Status |
|---|---|---|
| Batch submit, base64-encoded, `expected_output` always sent for official submits (§3.2, §8) | `judge/client.py` | implemented, unproven against a live instance |
| Token polling ~300–500 ms with hard timeout; timeout → Internal Error, never a team failure (§7.4, §7.7) | `judge/polling.py` (0.4 s interval, 30 s cap) | implemented, unproven |
| Only status id 3 scores; id 13 → `ERROR`, score untouched, admin rejudge (§3.3, §7.7) | `judge/base.py`, `services/results.py`, `services/rejudge.py` | implemented, verified (mock) |
| Language IDs resolved by name from `GET /languages`, hard-coded fallback only if that fails (§2 — IDs differ between versions) | `judge/client.py::ensure_languages`, `core/config.py` | implemented, unproven |
| Explicit output-comparison policy, per question: `EXACT` / `TRIM` / `TOKENS` / `FLOAT` (§7.5) | `services/scoring.py` | implemented, verified (mock) |
| Run = sample tests, never scores; Submit = all tests, may score (§4) | `services/judging.py`, `services/validation.py` | implemented, verified (mock) |
| Hidden tests never leave the server; Judge0 never faces the browser (§4, §7.1) | `services/arena.py`, `services/access.py` | implemented, verified |
| Source-size cap and submit cooldown in FastAPI (§7.6) | `MAX_SOURCE_BYTES` (64 KB), `SUBMIT_COOLDOWN_SECONDS` (5 s) | implemented |
| Internal-network binding, image pinned ≥ v1.13.1, auth-token support (§6.4, §7.1, §7.6) | `docker-compose.judge0.yml` (`127.0.0.1:2358`, `judge0/judge0:1.13.1`, `AUTHN_HEADER`) | partial — see items 2, 4, 5 below |

### 3.2 Remaining before event day

1. **CRITICAL — Prove the wire contract.** Language IDs, base64 encoding and
   the batch/polling payload shapes are written against the documented Judge0
   API but have never been exercised. Run the bring-up in §3.3 on the event
   machine and budget time for contract mismatches.
2. **CRITICAL — Sandbox network is not disabled.** The compose file does not
   set an isolate network-off flag; Overview §7.6 requires "sandbox network
   disabled". Diff `docker-compose.judge0.yml` against the official v1.13.1
   compose file and add the missing isolation settings.
3. **CRITICAL — Only Python has ever executed.** C, C++ and Java compile/run
   paths are implemented but untested (the mock backend executes Python only).
   Submit a known-good solution in all four languages before the event.
4. **HIGH — The compose stack has never been started.** It is a trimmed
   variant. Verify it boots, then tune `WORKERS_COUNT`, `MAX_QUEUE_SIZE` and
   the worker limits for the venue machine.
5. **HIGH — `AUTHN_TOKEN` is a placeholder** (`change-me-to-something-long`).
   Replace it and set the same value as `JUDGE0_AUTH_TOKEN` in `.env`
   (Overview §7.6 requires a token even on an internal network).
6. **MEDIUM — Limits are uncalibrated.** Language start-up costs differ;
   measure real runtimes on event hardware and adjust
   `DEFAULT_WALL_TIME_LIMIT` / per-question limits (Overview §6.7).
7. **MEDIUM — Cooldown is 5 s; the plan suggests 10–15 s per question**
   (§6.7). The original value was kept deliberately during the refactor;
   raise `SUBMIT_COOLDOWN_SECONDS` if the judge queue saturates.
8. **MEDIUM — No load test.** Design volume is 1,000–3,000 runs in two hours
   (§5). Rehearse with several teams submitting concurrently.
9. **MEDIUM — Switch the event database to PostgreSQL.** SQLite is a
   development convenience only (see §2).

### 3.3 Event-day bring-up

Host requirements: Docker Desktop with the WSL 2 backend enabled, roughly
8 GB free RAM and 6 GB disk, and a power plan that keeps the machine awake
for the whole event (never sleep; closing the lid does nothing).

Shell note: in Windows PowerShell 5.1, `curl` is an alias for
`Invoke-WebRequest`, which does not accept the flags used here. All examples
use `curl.exe`, bundled with Windows 10 and later.

```powershell
docker compose -f docker-compose.judge0.yml up -d
# first boot pulls several GB and runs a DB migration — wait 60-90 s
curl.exe http://127.0.0.1:2358/languages    # a JSON list means it is alive
```

Then in `.env`:

```env
JUDGE_BACKEND=judge0
JUDGE0_URL=http://127.0.0.1:2358
JUDGE0_AUTH_TOKEN=<same value as AUTHN_TOKEN in the compose file>
MOCK_EXECUTE_PYTHON=false
```

Restart the API and verify:

```powershell
curl.exe -H "admin-passcode: admin123" http://localhost:8000/api/admin/judge/health
# expect "healthy": true plus a resolved language map, e.g.
# {"backend":"judge0","healthy":true,"languages":{"python":71,"c":50,"cpp":54,"java":62}}
# (IDs vary between Judge0 versions — they are resolved by name at runtime)
```

Finally, from `/ui/main.html`, submit a known-good solution in Python, C,
C++ and Java — all four must return `PASSED` — and load the real questions
and hidden tests before doors open.

Failure policy on the day (Overview §7.7): if Judge0 becomes unreachable,
submissions finish as `ERROR` with no score change and the event continues.
After recovery, rescore affected attempts with
`POST /api/admin/submissions/{id}/rejudge`.

Troubleshooting:

| Symptom | Likely cause | Fix |
|---|---|---|
| `/languages` times out | still migrating | wait 60–90 s, retry |
| `healthy: false` | wrong URL or Judge0 down | `docker compose ps`, inspect logs |
| "No Judge0 language id resolved for X" | language-name mismatch | compare the output of `curl.exe http://127.0.0.1:2358/languages` with `LANGUAGE_NAMES` in `app/core/config.py` |
| every submit returns `ERROR` | client/contract mismatch | inspect the API log for the Judge0 HTTP error; the fix is in `app/services/judge/` |
| submissions queue forever | workers not running | `docker compose ps` — `judge0-workers` must be up |

---

## 4. Configuration

All settings load from `.env` (template: `.env.example`).

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | postgres… | SQLAlchemy async URL (SQLite supported) |
| `ADMIN_PASSCODE` | `admin123` | admin header value — change before the event |
| `EVENT_DURATION_SECONDS` | `7200` | per-team clock, started at first login |
| `JUDGE_BACKEND` | `mock` | `mock` (development) or `judge0` (event) |
| `JUDGE0_URL` | `http://judge0:2358` | Judge0 base URL |
| `JUDGE0_AUTH_TOKEN` | empty | sent as `X-Auth-Token` |
| `JUDGE0_TIMEOUT_SECONDS` | `30` | hard cap for one batch of test cases |
| `JUDGE0_POLL_INTERVAL` | `0.4` | seconds between polls |
| `MOCK_EXECUTE_PYTHON` | `true` | dev only — really executes Python locally |
| `DEFAULT_CPU_TIME_LIMIT` | `5` | seconds per test case |
| `DEFAULT_WALL_TIME_LIMIT` | `10` | wall-clock seconds |
| `DEFAULT_MEMORY_LIMIT_KB` | `256000` | ~250 MB |
| `MAX_SOURCE_BYTES` | `64000` | source size cap (413 above it) |
| `SUBMIT_COOLDOWN_SECONDS` | `5` | queue guard (429), not an attempt limit |

---

## 5. API surface

Team routes — header `X-Team-Token` (issued by login; rotated on re-login):

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | returns `session_token`; starts the clock on first login |
| GET | `/api/main/questions` | the 3 questions, visible tests, starter code, best scores |
| POST | `/api/main/run` | sample tests only — never scores |
| POST | `/api/main/submit` | all tests, partial credit, best-score-wins |
| GET | `/api/main/submissions` | own history |
| GET | `/api/main/clock` | remaining time |
| GET | `/api/questions/{id}` | public question (no test cases) |
| GET | `/api/questions/{id}/sample-tests` | visible tests only |

Admin routes — header `admin-passcode`:

| Method | Path | Purpose |
|---|---|---|
| POST / GET | `/api/admin/teams` | create / list teams |
| POST | `/api/admin/teams/{id}/add-time` | add seconds (`id=0` = every team) |
| POST / PATCH | `/api/admin/questions`, `/api/admin/questions/{id}` | create / edit |
| POST / GET | `/api/admin/questions/{id}/test-cases` | bulk-add (`?replace=true`) / list incl. hidden |
| DELETE | `/api/admin/test-cases/{id}` | delete one |
| GET | `/api/admin/submissions`, `/api/admin/submissions/{id}` | all / one with per-test detail |
| POST | `/api/admin/submissions/{id}/rejudge` | re-run and rescore |
| GET | `/api/admin/leaderboard` | standings (no auth) |
| GET | `/api/admin/judge/health` | judge status + resolved language IDs |

Grading rules: Judge0 is authoritative for execution errors (compile error,
TLE, runtime error); the app comparator is authoritative for correctness via
the question's `compare_mode`. Partial credit is
`points × passed_hidden_weight / total_hidden_weight`. Attempts are unlimited
with no negative marking; a question's score is the best across attempts and
team points increase only by the improvement delta.

---

## 6. Frontend

The API serves `frontend/` at `/ui` — no second server and no CORS
configuration required. `main.html` is the MAIN-round console: Monaco editor
(CDN-loaded, with an automatic plain-textarea fallback offline), per-language
starter code, Run/Submit, per-test results (hidden tests reveal pass/fail
only), countdown clock, and drafts persisted per question and language in
`localStorage`. Sessions live in `sessionStorage`, so each browser tab logs in
separately. `admin.html` predates the current admin API and(hidden tests reveal pass/fail
only), countdown clock, and drafts persisted per question and language in
`localStorage`. Sessions live in `sessionStorage`, so each browser tab logs in
separately. `admin.html` predates the current admin API and is partially
stale; the admin endpoints in §5 are the supported surface.

---

## 7. Known limitations

- The mock judge is **not a sandbox** — with `MOCK_EXECUTE_PYTHON=true` it
  runs Python in a local subprocess. Development only.
- `FLOAT` comparison quirk (pre-existing, identical in the original repo):
  the skeleton check in `_float_compare` includes trailing newlines, so a
  correct `print()` output can fail a seeded expected value stored without a
  trailing newline; the `TRIM` fallback only rescues byte-identical results.
- Legacy IDOR: `GET /api/teams/{id}/status` and `/time-remaining` take a raw
  team id with no credential. The challenge/boost pages depend on them;
  migrate those pages to `X-Team-Token`, then lock the routes down.
- No database migrations — schema changes require `reset_db.py` (destructive).
- No rate limiting beyond the submit cooldown.
- `app/core/config.py` carries default secrets (DB URL, admin passcode).
  `.env` overrides them and is gitignored; rotate both before the event.

---

## 8. Adding real questions

Use the admin API rather than editing `seed.py`. Examples are PowerShell;
inside the single-quoted `-d` argument, every JSON `"` is written `\"` and
every literal backslash of the JSON text is doubled — copy them verbatim.

```powershell
# 1. create the question
curl.exe -X POST http://localhost:8000/api/admin/questions `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '{\"title\":\"Two Sum\",\"description\":\"...\",\"type\":\"MAIN\",\"sub_type\":\"LEETCODE\",
       \"points\":500,\"compare_mode\":\"TRIM\",
       \"allowed_languages\":\"[\\\"python\\\",\\\"c\\\",\\\"cpp\\\",\\\"java\\\"]\"}'

# 2. test cases — is_hidden:false shows as a sample in the editor
curl.exe -X POST "http://localhost:8000/api/admin/questions/1/test-cases?replace=true" `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '[{\"stdin\":\"4\n2 7 11 15\n9\",\"expected_output\":\"0 1\",\"is_hidden\":false,\"position\":0},
       {\"stdin\":\"3\n3 2 4\n6\",\"expected_output\":\"1 2\",\"is_hidden\":true,\"position\":1}]'

# 3. starter code, one entry per language
curl.exe -X PATCH http://localhost:8000/api/admin/questions/1 `
  -H "admin-passcode: admin123" -H "Content-Type: application/json" `
  -d '{\"starter_code\":\"{\\\"python\\\":\\\"n=int(input())\\n\\\",\\\"cpp\\\":\\\"#include <iostream>\\n\\\"}\"}'
```

Guidelines: use `compare_mode: "FLOAT"` for numeric output; include at least
one visible test so Run Samples is meaningful; 3–5 hidden tests suffice (each
is a separate sandbox run); provide starter code for all four allowed
languages; questions must read stdin and write stdout (Overview §6.3).
