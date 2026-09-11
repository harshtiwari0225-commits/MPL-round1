#!/usr/bin/env python3
"""MPL Event Platform - seed script.

Creates demo teams and the three MAIN questions (debugging, math, leetcode)
with both visible and hidden test cases.

Usage:
    python seed.py
    python seed.py --url http://localhost:8000

Re-running is safe: existing teams/questions are skipped and test cases are
replaced.
"""
import sys

import requests

from seeding.questions import QUESTIONS, TEAMS

BASE_URL = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--url" else "http://localhost:8000"
ADMIN_HEADERS = {"admin-passcode": "admin123", "Content-Type": "application/json"}


def api_call(method, path, data=None, params=None):
    """Never explode on a non-JSON response (the old seeder did)."""
    try:
        r = requests.request(
            method, f"{BASE_URL}{path}", json=data, params=params,
            headers=ADMIN_HEADERS, timeout=30,
        )
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot reach {BASE_URL}. Start the server with: "
              "uvicorn app.main:app --reload")
        sys.exit(1)

    try:
        body = r.json()
    except ValueError:
        body = {"detail": r.text[:200]}
    return r.status_code, body


def main():
    print("=" * 60)
    print("  MPL Event Platform - Seed Script")
    print(f"  Target: {BASE_URL}")
    print("=" * 60)

    print("\nCreating teams...")
    for team in TEAMS:
        code, res = api_call("POST", "/api/admin/teams", team)
        if code == 200:
            print(f"  OK    {team['name']} (id={res.get('id')}) passcode: {team['passcode']}")
        else:
            print(f"  SKIP  {team['name']}: {res.get('detail', res)}")

    print("\nCreating MAIN questions...")
    for question in QUESTIONS:
        cases = question.pop("_cases")
        code, res = api_call("POST", "/api/admin/questions", question)
        if code != 200:
            print(f"  FAIL  {question['title']}: {res}")
            continue

        qid = res["id"]
        code, res = api_call(
            "POST", f"/api/admin/questions/{qid}/test-cases", cases, params={"replace": "true"}
        )
        status = "OK" if code == 200 else "FAIL"
        print(f"  {status}   [{question['sub_type']:<9}] {question['title']} "
              f"(id={qid}, {len(cases)} tests, {question['points']} pts)")

    print("\n" + "=" * 60)
    print("Done! Team credentials:")
    for t in TEAMS:
        print(f"  {t['name']:<14} passcode: {t['passcode']}")
    print(f"\n  API docs    -> {BASE_URL}/docs")
    print(f"  Leaderboard -> {BASE_URL}/api/admin/leaderboard")
    print("=" * 60)


if __name__ == "__main__":
    main()
