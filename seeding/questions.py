"""Demo teams and the three demo MAIN questions with their test cases.

Extracted verbatim from seed.py; starter code blobs live in starters.py.
Each question dict carries a transient "_cases" key that seed.py pops and
posts to the test-cases endpoint.
"""

import json

from seeding.starters import DEBUG_STARTER, LEETCODE_STARTER, MATH_STARTER

TEAMS = [
    {"name": "Team Alpha", "passcode": "alpha123"},
    {"name": "Team Beta", "passcode": "beta123"},
    {"name": "Team Gamma", "passcode": "gamma123"},
]


def q(
    title,
    description,
    sub_type,
    points,
    starter,
    cases,
    compare_mode="TRIM",
    difficulty="MEDIUM",
    order=0,
):
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
            {
                "stdin": "1000\n0.05\n2",
                "expected_output": "1102.50",
                "is_hidden": False,
                "position": 0,
            },
            {"stdin": "500\n0.1\n3", "expected_output": "665.50", "is_hidden": True, "position": 1},
            {"stdin": "1000\n0\n5", "expected_output": "1000.00", "is_hidden": True, "position": 2},
            {
                "stdin": "250\n0.07\n10",
                "expected_output": "491.79",
                "is_hidden": True,
                "position": 3,
            },
        ],
        compare_mode="FLOAT",  # 0.30000000000000004 must not fail this
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
            {
                "stdin": "4\n2 7 11 15\n9",
                "expected_output": "0 1",
                "is_hidden": False,
                "position": 0,
            },
            {"stdin": "3\n3 2 4\n6", "expected_output": "1 2", "is_hidden": True, "position": 1},
            {
                "stdin": "5\n1 1 1 1 1\n2",
                "expected_output": "0 1",
                "is_hidden": True,
                "position": 2,
            },
            {
                "stdin": "6\n10 20 30 40 50 60\n100",
                "expected_output": "3 5",
                "is_hidden": True,
                "position": 3,
            },
        ],
        compare_mode="TRIM",
        difficulty="HARD",
        order=3,
    ),
]
