#!/usr/bin/env python3
"""
MPL Event Platform — Seed Script
Creates dummy teams & questions for development/testing.

Usage:
    python seed.py
    python seed.py --url http://your-server:8000
"""
import requests
import json
import sys

BASE_URL = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--url" else "http://localhost:8000"
ADMIN_HEADERS = {"admin-passcode": "admin123", "Content-Type": "application/json"}

TEAMS = [
    {"name": "Team Alpha", "passcode": "alpha123"},
    {"name": "Team Beta",  "passcode": "beta123"},
    {"name": "Team Gamma", "passcode": "gamma123"},
]

QUESTIONS = [
    # MAIN
    {
        "title": "Design a URL Shortener Service",
        "description": (
            "Design and implement a URL shortener service (similar to bit.ly).\n\n"
            "Your solution must support:\n"
            "  1. Shortening a long URL to a unique 6-character alphanumeric code.\n"
            "  2. Resolving a short code back to the original URL.\n"
            "  3. Tracking total visit count per short URL.\n"
            "  4. Graceful handling of invalid / duplicate URLs.\n\n"
            "Bonus:\n"
            "  - Implement URL expiry (links expire after 30 days).\n"
            "  - Add a custom alias feature.\n\n"
            "Deliverable: A working script/service with a demo showing all four features."
        ),
        "test_cases": json.dumps([
            {"id": 1, "input": "shorten('https://example.com/very/long/path?param=value')", "expected": "6-char code e.g. 'aB3xYz'"},
            {"id": 2, "input": "resolve('aB3xYz')", "expected": "Original URL"},
            {"id": 3, "input": "shorten('not-a-valid-url')", "expected": "ValueError or error message"},
            {"id": 4, "input": "visit_count after 3 resolves", "expected": "3"},
        ]),
        "type": "MAIN",
        "difficulty": "MEDIUM",
        "reward_value": 0,
    },
    # TIME BOOST 1
    {
        "title": "FizzBuzz Pro  (+5 min)",
        "description": (
            "Write fizzbuzz_pro(n) returning strings for 1..n:\n"
            "  - Multiple of 3 -> 'Fizz'\n"
            "  - Multiple of 5 -> 'Buzz'\n"
            "  - Multiple of 7 -> 'Boom'\n"
            "  - Combinations: FizzBuzz, FizzBoom, BuzzBoom, FizzBuzzBoom\n"
            "  - Otherwise -> str(number)"
        ),
        "test_cases": json.dumps([
            {"id": 1, "input": "fizzbuzz_pro(15)", "expected": '["1","2","Fizz","4","Buzz","Fizz","Boom","8","Fizz","Buzz","11","Fizz","13","Boom","FizzBuzz"]'},
            {"id": 2, "input": "fizzbuzz_pro(21)[20]", "expected": "'FizzBoom'"},
            {"id": 3, "input": "fizzbuzz_pro(105)[104]", "expected": "'FizzBuzzBoom'"},
        ]),
        "type": "TIME_BOOST",
        "difficulty": "EASY",
        "reward_value": 300,
    },
    # TIME BOOST 2
    {
        "title": "Matrix Spiral Traversal  (+10 min)",
        "description": (
            "Given an m x n matrix, return all elements in clockwise spiral order.\n\n"
            "Example:\n"
            "  Input:  [[1,2,3],[4,5,6],[7,8,9]]\n"
            "  Output: [1,2,3,6,9,8,7,4,5]\n\n"
            "Constraints: 1<=m,n<=10, -100<=values<=100\n"
            "Bonus: Also implement counter-clockwise spiral."
        ),
        "test_cases": json.dumps([
            {"id": 1, "input": "spiral([[1,2,3],[4,5,6],[7,8,9]])", "expected": "[1,2,3,6,9,8,7,4,5]"},
            {"id": 2, "input": "spiral([[1,2],[3,4]])", "expected": "[1,2,4,3]"},
            {"id": 3, "input": "spiral([[1,2,3,4]])", "expected": "[1,2,3,4]"},
        ]),
        "type": "TIME_BOOST",
        "difficulty": "EASY",
        "reward_value": 600,
    },
    # CHALLENGE
    {
        "title": "Implement an LRU Cache",
        "description": (
            "Design and implement a Least Recently Used (LRU) Cache.\n\n"
            "API:\n"
            "  LRUCache(capacity)  - Initialize\n"
            "  get(key)            - Return value or -1\n"
            "  put(key, value)     - Insert/update, evict LRU if over capacity\n\n"
            "Both get() and put() MUST run in O(1) time!\n\n"
            "Example:\n"
            "  cache = LRUCache(2)\n"
            "  cache.put(1,1); cache.put(2,2); cache.get(1)  -> 1\n"
            "  cache.put(3,3); cache.get(2)  -> -1 (evicted)"
        ),
        "test_cases": json.dumps([
            {"id": 1, "input": "cap=2; put(1,1), put(2,2), get(1), put(3,3), get(2)", "expected": "get(1)=1, get(2)=-1"},
            {"id": 2, "input": "cap=1; put(2,1), get(2), put(3,2), get(2), get(3)", "expected": "1, -1, 2"},
        ]),
        "type": "CHALLENGE",
        "difficulty": "HARD",
        "reward_value": 500,
    },
]


def api_post(path, data):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=data, headers=ADMIN_HEADERS, timeout=10)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: Cannot reach {BASE_URL}. Start server: uvicorn app.main:app --reload")
        sys.exit(1)


def main():
    print("=" * 50)
    print("  MPL Event Platform — Seed Script")
    print(f"  Target: {BASE_URL}")
    print("=" * 50)

    print("\nCreating teams...")
    team_ids = []
    for team in TEAMS:
        code, res = api_post("/api/admin/teams", team)
        if code == 200:
            tid = res.get("id")
            team_ids.append(tid)
            print(f"  OK  {team['name']} (id={tid}) passcode: {team['passcode']}")
        else:
            print(f"  WARN  {team['name']}: {res}")

    print("\nCreating questions...")
    boost_ids = []
    for q in QUESTIONS:
        code, res = api_post("/api/admin/questions", q)
        if code == 200:
            qid = res.get("id")
            print(f"  OK  [{q['type']}] {q['title']} (id={qid})")
            if q["type"] == "TIME_BOOST":
                boost_ids.append(qid)
        else:
            print(f"  WARN  {q['title']}: {res}")

    if team_ids and boost_ids:
        print("\nAssigning time boost questions to all teams...")
        for tid in team_ids:
            for qid in boost_ids:
                code, res = api_post(f"/api/admin/teams/{tid}/assign-boost", {"question_id": qid})
                print(f"  {'OK' if code == 200 else 'WARN'}  Team {tid} <- Question {qid}")

    print("\n" + "=" * 50)
    print("Done! Test credentials:")
    for t in TEAMS:
        print(f"  {t['name']:<14} passcode: {t['passcode']}")
    print(f"\n  API Docs -> {BASE_URL}/docs")
    print("  Frontend -> open frontend/index.html")
    print("=" * 50)


if __name__ == "__main__":
    main()
