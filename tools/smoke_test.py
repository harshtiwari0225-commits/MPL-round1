#!/usr/bin/env python3
"""Behavioural smoke test for the MPL API (original vs refactored parity tool).

Usage: python smoke.py http://127.0.0.1:8000 > out.json

Exercises auth, guards, run/submit scoring, partial credit, cooldown, rejudge,
admin CRUD, legacy boost/challenge flows and static serving. Volatile values
(timestamps, tokens, remaining seconds) are masked so two fresh, identically
seeded servers must produce byte-identical output.
"""

import json
import re
import sys
import time

import requests

BASE = sys.argv[1].rstrip("/")
ADMIN = {"admin-passcode": "admin123", "Content-Type": "application/json"}
OUT = []

TS = re.compile(r"\d{4}-\d{2}-\d{2}[T ][\d:.]+")
MASK_KEYS_TS = {
    "timer_start_time",
    "created_at",
    "finished_at",
    "first_solved_at",
    "last_submission_at",
}
MASK_KEYS_N = {"seconds_remaining"}


def norm(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "session_token":
                out[k] = "<TOKEN>"
            elif k == "main_question_id":
                out[k] = "<RAND>"  # random.choice() at first login, by design
            elif k in MASK_KEYS_TS:
                out[k] = "<TS>" if v is not None else None
            elif k in MASK_KEYS_N and isinstance(v, (int, float)):
                out[k] = "<N>"
            else:
                out[k] = norm(v)
        return out
    if isinstance(obj, list):
        return [norm(x) for x in obj]
    if isinstance(obj, str):
        s = TS.sub("<TS>", obj)
        s = re.sub(r"Please wait \d+s", "Please wait <N>s", s)
        s = re.sub(r"/tmp/tmp[\w_]+", "<TMP>", s)  # random mkdtemp names in tracebacks
        return s
    return obj


def step(name, method, path, body=None, headers=None, params=None, raw=False):
    try:
        r = requests.request(
            method, BASE + path, json=body, headers=headers or {}, params=params, timeout=90
        )
        if raw:
            data = {"len": len(r.content), "ctype": r.headers.get("content-type")}
        else:
            try:
                data = r.json()
            except Exception:
                data = r.text[:300]
        OUT.append([name, r.status_code, norm(data)])
        return r, data
    except Exception as exc:  # connection errors etc.
        OUT.append([name, None, f"EXC {exc}"])
        return None, None


# ── solutions ────────────────────────────────────────────────────────────────
Q1_BUGGY = "n = int(input())\ntotal = 0\nfor i in range(1, n):\n    total += i\nprint(total)\n"
Q1_FIXED = "n = int(input())\nprint(sum(range(1, n + 1)))\n"
Q2_RAW_FLOAT = (
    "p = float(input())\nr = float(input())\nt = float(input())\nprint(p * (1 + r) ** t)\n"
)
Q3_TWOSUM = (
    "n = int(input())\na = list(map(int, input().split()))\ntarget = int(input())\n"
    "seen = {}\nfor i, x in enumerate(a):\n    if target - x in seen:\n"
    "        print(seen[target - x], i)\n        break\n    seen[x] = i\n"
)
BIG_SOURCE = "#" * 70000 + "\nprint(1)\n"


def sub(qid, lang, code):
    return {"question_id": qid, "language": lang, "source_code": code}


# ── basics ───────────────────────────────────────────────────────────────────
step("root", "GET", "/")
step("health", "GET", "/health")
step("ui_index", "GET", "/ui/index.html", raw=True)
step("ui_main", "GET", "/ui/main.html", raw=True)

# ── auth ─────────────────────────────────────────────────────────────────────
step("login_bad", "POST", "/api/auth/login", body={"name": "Team Alpha", "passcode": "nope"})
_, login = step(
    "login", "POST", "/api/auth/login", body={"name": "Team Alpha", "passcode": "alpha123"}
)
TOKEN = login["session_token"]
AUTH = {"X-Team-Token": TOKEN}

step("questions_noauth", "GET", "/api/main/questions")
step("questions_badauth", "GET", "/api/main/questions", headers={"X-Team-Token": "bogus"})
step("questions", "GET", "/api/main/questions", headers=AUTH)
step("question_public", "GET", "/api/questions/2")
step("sample_tests", "GET", "/api/questions/2/sample-tests")
step("question_404", "GET", "/api/questions/999")

# ── legacy team routes ───────────────────────────────────────────────────────
step("legacy_status", "GET", "/api/teams/1/status")
step("legacy_time", "GET", "/api/teams/1/time-remaining")
step("legacy_404", "GET", "/api/teams/999/status")

# ── run / submit ─────────────────────────────────────────────────────────────
step("run_buggy", "POST", "/api/main/run", sub(1, "python", Q1_BUGGY), headers=AUTH)
step("run_fixed", "POST", "/api/main/run", sub(1, "python", Q1_FIXED), headers=AUTH)
step("run_no_samples_q", "POST", "/api/main/run", sub(999, "python", Q1_FIXED), headers=AUTH)
step("submit_buggy", "POST", "/api/main/submit", sub(1, "python", Q1_BUGGY), headers=AUTH)
step("submit_cooldown", "POST", "/api/main/submit", sub(1, "python", Q1_FIXED), headers=AUTH)
time.sleep(6)
step("submit_fixed", "POST", "/api/main/submit", sub(1, "python", Q1_FIXED), headers=AUTH)
step(
    "submit_math_rawfloat", "POST", "/api/main/submit", sub(2, "python", Q2_RAW_FLOAT), headers=AUTH
)
step("submit_twosum", "POST", "/api/main/submit", sub(3, "python", Q3_TWOSUM), headers=AUTH)
step("submit_bigsource", "POST", "/api/main/submit", sub(1, "python", BIG_SOURCE), headers=AUTH)
step("submit_badlang", "POST", "/api/main/submit", sub(1, "ruby", Q1_FIXED), headers=AUTH)
step("submit_lang_alias", "POST", "/api/main/run", sub(1, "Python3", Q1_FIXED), headers=AUTH)
step("submit_compile_error", "POST", "/api/main/run", sub(1, "python", "def f(:\n"), headers=AUTH)

step("my_submissions", "GET", "/api/main/submissions", headers=AUTH)
step("my_submissions_q1", "GET", "/api/main/submissions", headers=AUTH, params={"question_id": 1})
step("clock", "GET", "/api/main/clock", headers=AUTH)

# ── admin ────────────────────────────────────────────────────────────────────
step("leaderboard", "GET", "/api/admin/leaderboard")
step("admin_badauth", "GET", "/api/admin/teams", headers={"admin-passcode": "wrong"})
step("admin_teams", "GET", "/api/admin/teams", headers=ADMIN)
step("judge_health", "GET", "/api/admin/judge/health", headers=ADMIN)
step("q1_testcases", "GET", "/api/admin/questions/1/test-cases", headers=ADMIN)
step("admin_submissions", "GET", "/api/admin/submissions", headers=ADMIN)
step("admin_submission_detail", "GET", "/api/admin/submissions/2", headers=ADMIN)
step("admin_submission_404", "GET", "/api/admin/submissions/999", headers=ADMIN)
step("rejudge_run_400", "POST", "/api/admin/submissions/2/rejudge", headers=ADMIN)
step("rejudge_scored", "POST", "/api/admin/submissions/4/rejudge", headers=ADMIN)
step("addtime", "POST", "/api/admin/teams/1/add-time", body={"seconds": 120}, headers=ADMIN)
step("addtime_zero_400", "POST", "/api/admin/teams/1/add-time", body={"seconds": 0}, headers=ADMIN)
step("clock_after_addtime", "GET", "/api/main/clock", headers=AUTH)
step("patch_q1_points", "PATCH", "/api/admin/questions/1", body={"points": 350}, headers=ADMIN)
time.sleep(6)  # clear the per-question submit cooldown so this really re-scores
step("resubmit_q1_higher", "POST", "/api/main/submit", sub(1, "python", Q1_FIXED), headers=AUTH)

# ── legacy boost / challenge flows ───────────────────────────────────────────
step(
    "create_boost_q",
    "POST",
    "/api/admin/questions",
    body={
        "title": "Boost: ASCII sum",
        "description": "Sum the bytes.",
        "test_cases": "[]",
        "type": "TIME_BOOST",
        "difficulty": "EASY",
        "reward_value": 300,
    },
    headers=ADMIN,
)
step(
    "assign_boost",
    "POST",
    "/api/admin/teams/2/assign-boost",
    body={"question_id": 4},
    headers=ADMIN,
)
step(
    "assign_boost_dup",
    "POST",
    "/api/admin/teams/2/assign-boost",
    body={"question_id": 4},
    headers=ADMIN,
)
step("beta_status", "GET", "/api/teams/2/status")
step(
    "mark_boost_solved",
    "POST",
    "/api/admin/review/mark-solved",
    body={"team_id": 2, "question_id": 4},
    headers=ADMIN,
)
step(
    "create_challenge_q",
    "POST",
    "/api/admin/questions",
    body={
        "title": "Challenge: reverse",
        "description": "Reverse it.",
        "test_cases": "[]",
        "type": "CHALLENGE",
        "difficulty": "HARD",
        "reward_value": 250,
    },
    headers=ADMIN,
)
step(
    "create_session",
    "POST",
    "/api/admin/challenge/create",
    body={"question_id": 5, "team1_id": 1, "team2_id": 2},
    headers=ADMIN,
)
step("alpha_status_session", "GET", "/api/teams/1/status")
step(
    "mark_challenge_won",
    "POST",
    "/api/admin/review/mark-solved",
    body={"team_id": 1, "question_id": 5},
    headers=ADMIN,
)
step(
    "mark_main_info",
    "POST",
    "/api/admin/review/mark-solved",
    body={"team_id": 1, "question_id": 1},
    headers=ADMIN,
)
step("leaderboard_final", "GET", "/api/admin/leaderboard")
step("submit_nonmain_400", "POST", "/api/main/submit", sub(4, "python", "print(1)\n"), headers=AUTH)

# ── test-case CRUD ───────────────────────────────────────────────────────────
step(
    "add_testcase",
    "POST",
    "/api/admin/questions/1/test-cases",
    body=[
        {"stdin": "7", "expected_output": "28", "is_hidden": False, "weight": 1.0, "position": 9}
    ],
    params={"replace": "false"},
    headers=ADMIN,
)
step("q1_testcases_after_add", "GET", "/api/admin/questions/1/test-cases", headers=ADMIN)
step("delete_testcase", "DELETE", "/api/admin/test-cases/13", headers=ADMIN)
step("delete_testcase_404", "DELETE", "/api/admin/test-cases/999", headers=ADMIN)
step("add_testcase_q404", "POST", "/api/admin/questions/999/test-cases", body=[], headers=ADMIN)

# ── token rotation ───────────────────────────────────────────────────────────
_, login2 = step(
    "relogin", "POST", "/api/auth/login", body={"name": "Team Alpha", "passcode": "alpha123"}
)
step("clock_oldtoken_401", "GET", "/api/main/clock", headers=AUTH)
step("clock_newtoken", "GET", "/api/main/clock", headers={"X-Team-Token": login2["session_token"]})

print(json.dumps(OUT, indent=1))
