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
import json
import sys

import requests

BASE_URL = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--url" else "http://localhost:8000"
ADMIN_HEADERS = {"admin-passcode": "admin123", "Content-Type": "application/json"}

TEAMS = [
    {"name": "Team Alpha", "passcode": "alpha123"},
    {"name": "Team Beta", "passcode": "beta123"},
    {"name": "Team Gamma", "passcode": "gamma123"},
]

# ─────────────────────────────────────────────────────────────────────────────
# Q1 - DEBUGGING: the code runs but is wrong. Fix it.
# ─────────────────────────────────────────────────────────────────────────────

DEBUG_STARTER = {
    "python": (
        "# Sum of every integer from 1 to n.\n"
        "# This solution is WRONG - fix it.\n"
        "n = int(input())\n"
        "total = 0\n"
        "for i in range(1, n):\n"
        "    total += i\n"
        "print(total)\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    int total = 0;\n"
        "    for (int i = 1; i < n; i++) total += i;\n"
        "    printf(\"%d\\n\", total);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    int total = 0;\n"
        "    for (int i = 1; i < n; i++) total += i;\n"
        "    cout << total << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        int total = 0;\n"
        "        for (int i = 1; i < n; i++) total += i;\n"
        "        System.out.println(total);\n"
        "    }\n"
        "}\n"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Q2 - MATH: implement from scratch. Compared with float tolerance.
# ─────────────────────────────────────────────────────────────────────────────

MATH_STARTER = {
    "python": (
        "# Compound interest: A = P * (1 + r) ** t\n"
        "# Read P, r and t, one per line. Print A to 2 decimal places.\n"
        "p = float(input())\n"
        "r = float(input())\n"
        "t = float(input())\n"
        "\n"
        "# TODO: implement\n"
        "print(\"0.00\")\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "#include <math.h>\n"
        "int main(void) {\n"
        "    double p, r, t;\n"
        "    scanf(\"%lf %lf %lf\", &p, &r, &t);\n"
        "    /* TODO: compute A = p * pow(1 + r, t) */\n"
        "    printf(\"%.2f\\n\", 0.0);\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <iomanip>\n"
        "#include <cmath>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    double p, r, t;\n"
        "    cin >> p >> r >> t;\n"
        "    // TODO: compute A = p * pow(1 + r, t)\n"
        "    cout << fixed << setprecision(2) << 0.0 << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        double p = sc.nextDouble();\n"
        "        double r = sc.nextDouble();\n"
        "        double t = sc.nextDouble();\n"
        "        // TODO: compute A = p * Math.pow(1 + r, t)\n"
        "        System.out.printf(\"%.2f%n\", 0.0);\n"
        "    }\n"
        "}\n"
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Q3 - LEETCODE: classic two-sum.
# ─────────────────────────────────────────────────────────────────────────────

LEETCODE_STARTER = {
    "python": (
        "# Two Sum.\n"
        "# Line 1: n        Line 2: n integers        Line 3: target\n"
        "# Print the two 0-based indices i j (i < j) whose values sum to target.\n"
        "n = int(input())\n"
        "nums = list(map(int, input().split()))\n"
        "target = int(input())\n"
        "\n"
        "# TODO: implement\n"
        "print(\"0 1\")\n"
    ),
    "c": (
        "#include <stdio.h>\n"
        "int main(void) {\n"
        "    int n; scanf(\"%d\", &n);\n"
        "    int a[1000];\n"
        "    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n"
        "    int target; scanf(\"%d\", &target);\n"
        "    /* TODO */\n"
        "    printf(\"0 1\\n\");\n"
        "    return 0;\n"
        "}\n"
    ),
    "cpp": (
        "#include <iostream>\n"
        "#include <vector>\n"
        "using namespace std;\n"
        "int main() {\n"
        "    int n; cin >> n;\n"
        "    vector<int> a(n);\n"
        "    for (int i = 0; i < n; i++) cin >> a[i];\n"
        "    int target; cin >> target;\n"
        "    // TODO\n"
        "    cout << \"0 1\" << endl;\n"
        "    return 0;\n"
        "}\n"
    ),
    "java": (
        "import java.util.Scanner;\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int n = sc.nextInt();\n"
        "        int[] a = new int[n];\n"
        "        for (int i = 0; i < n; i++) a[i] = sc.nextInt();\n"
        "        int target = sc.nextInt();\n"
        "        // TODO\n"
        "        System.out.println(\"0 1\");\n"
        "    }\n"
        "}\n"
    ),
}


def q(title, description, sub_type, points, starter, cases, compare_mode="TRIM",
      difficulty="MEDIUM", order=0):
    return {
        "title": title,
        "description": description,
        "test_cases": "[]",
        "type": "MAIN",
        "difficulty": difficulty,
        "reward_value": 0,
        "sub_type": sub_type,
        "starter_code": json.dumps(starter),
        "allowed_languages": json.dumps(["python", "c", "cpp", "java"]),
        "compare_mode": compare_mode,
        "points": points,
        "cpu_time_limit": 5.0,
        "wall_time_limit": 10.0,
        "memory_limit_kb": 256000,
        "order_index": order,
        "_cases": cases,
    }


QUESTIONS = [
    q(
        "Debug: Sum 1..N",
        "The program below should print the sum of every integer from 1 to n.\n"
        "It runs without crashing, but the answer is wrong. Find the bug and fix it.\n\n"
        "Input:  one integer n\n"
        "Output: the sum of 1..n",
        "DEBUGGING",
        300,
        DEBUG_STARTER,
        [
            {"stdin": "5", "expected_output": "15", "is_hidden": False, "position": 0},
            {"stdin": "10", "expected_output": "55", "is_hidden": True, "position": 1},
            {"stdin": "1", "expected_output": "1", "is_hidden": True, "position": 2},
            {"stdin": "100", "expected_output": "5050", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="EASY",
        order=1,
    ),
    q(
        "Math: Compound Interest",
        "Compute compound interest:  A = P * (1 + r)^t\n\n"
        "Input:  P, r and t (one per line)\n"
        "Output: A rounded to exactly 2 decimal places",
        "MATH",
        400,
        MATH_STARTER,
        [
            {"stdin": "1000\n0.05\n2", "expected_output": "1102.50", "is_hidden": False, "position": 0},
            {"stdin": "500\n0.1\n3", "expected_output": "665.50", "is_hidden": True, "position": 1},
            {"stdin": "1000\n0\n5", "expected_output": "1000.00", "is_hidden": True, "position": 2},
            {"stdin": "250\n0.07\n10", "expected_output": "491.79", "is_hidden": True, "position": 3},
        ],
        compare_mode="FLOAT",   # 0.30000000000000004 must not fail this
        difficulty="MEDIUM",
        order=2,
    ),
    q(
        "Leetcode: Two Sum",
        "Given an array and a target, print the two 0-based indices i j (i < j)\n"
        "whose values add up to the target.\n\n"
        "Input:  line 1: n\n"
        "        line 2: n space-separated integers\n"
        "        line 3: target\n"
        "Output: the two indices separated by a space",
        "LEETCODE",
        500,
        LEETCODE_STARTER,
        [
            {"stdin": "4\n2 7 11 15\n9", "expected_output": "0 1", "is_hidden": False, "position": 0},
            {"stdin": "3\n3 2 4\n6", "expected_output": "1 2", "is_hidden": True, "position": 1},
            {"stdin": "5\n1 1 1 1 1\n2", "expected_output": "0 1", "is_hidden": True, "position": 2},
            {"stdin": "6\n10 20 30 40 50 60\n100", "expected_output": "3 5", "is_hidden": True, "position": 3},
        ],
        compare_mode="TRIM",
        difficulty="HARD",
        order=3,
    ),
]


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
