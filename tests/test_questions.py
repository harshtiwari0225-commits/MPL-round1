import pytest

from app.models import CompareMode, Question, QuestionType, TestCase


@pytest.mark.asyncio
async def test_get_nonexistent_question(client):
    response = await client.get("/api/questions/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_question_and_sample_tests(client, db_session):
    question = Question(
        title="Sample Question",
        description="Calculate something",
        type=QuestionType.MAIN,
        points=100,
        compare_mode=CompareMode.EXACT,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    tc_sample = TestCase(
        question_id=question.id,
        stdin="1 2\n",
        expected_output="3\n",
        is_hidden=False,
        position=0,
    )
    tc_hidden = TestCase(
        question_id=question.id,
        stdin="3 4\n",
        expected_output="7\n",
        is_hidden=True,
        position=1,
    )
    db_session.add_all([tc_sample, tc_hidden])
    await db_session.commit()

    # Get question detail
    resp = await client.get(f"/api/questions/{question.id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Sample Question"

    # Get sample tests (should include tc_sample but NOT tc_hidden)
    resp_samples = await client.get(f"/api/questions/{question.id}/sample-tests")
    assert resp_samples.status_code == 200
    samples = resp_samples.json()
    assert len(samples) == 1
    assert samples[0]["stdin"] == "1 2\n"
