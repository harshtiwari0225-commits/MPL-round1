from app.models import CompareMode, TestCase
from app.services.judge import JudgeOutcome
from app.services.results import build_result
from app.services.scoring import outputs_match, score_submission


def test_outputs_match_exact():
    assert outputs_match("hello\n", "hello\n", CompareMode.EXACT)
    assert not outputs_match("hello", "hello\n", CompareMode.EXACT)


def test_outputs_match_trim():
    assert outputs_match("hello  \n", "hello", CompareMode.TRIM)
    assert not outputs_match("hello world", "hello", CompareMode.TRIM)


def test_outputs_match_tokens():
    assert outputs_match("  hello   world \n", "hello world\n", CompareMode.TOKENS)
    assert not outputs_match("hello world", "world hello", CompareMode.TOKENS)


def test_outputs_match_float():
    assert outputs_match("3.14159\n", "3.14159", CompareMode.FLOAT)
    assert outputs_match("3.1415926", "3.1415927", CompareMode.FLOAT)


def test_score_submission_partial_credit():
    tc1 = TestCase(id=1, is_hidden=False, weight=1, expected_output="1")
    tc2 = TestCase(id=2, is_hidden=True, weight=2, expected_output="2")
    tc3 = TestCase(id=3, is_hidden=True, weight=3, expected_output="3")

    r1 = build_result(
        tc1,
        JudgeOutcome(status_id=3, status="Accepted", stdout="1", stderr="", compile_output=""),
        CompareMode.EXACT,
        visible=True,
    )
    r2 = build_result(
        tc2,
        JudgeOutcome(status_id=3, status="Accepted", stdout="2", stderr="", compile_output=""),
        CompareMode.EXACT,
        visible=False,
    )
    r3 = build_result(
        tc3,
        JudgeOutcome(
            status_id=4,
            status="Wrong Answer",
            stdout="wrong",
            stderr="",
            compile_output="",
        ),
        CompareMode.EXACT,
        visible=False,
    )  # Failed

    # Total hidden weight = 2 + 3 = 5. Passed hidden weight = 2.
    # Score = 100 * (2 / 5) = 40.
    score, passed, total = score_submission(100, [r1, r2, r3], [tc1, tc2, tc3])
    assert score == 40
    assert passed == 2
    assert total == 3
