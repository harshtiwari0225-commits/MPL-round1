import pytest

from app.models import CompareMode, Question, QuestionType, Team, TestCase


@pytest.mark.asyncio
async def test_main_unauthenticated(client):
    response = await client.get("/api/main/questions")
    assert response.status_code == 401

    response = await client.get("/api/main/clock")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_main_authenticated_flow(client, db_session):
    # 1. Setup question and test cases
    question = Question(
        title="Sum Two Numbers",
        description="Print sum",
        type=QuestionType.MAIN,
        points=100,
        compare_mode=CompareMode.TRIM,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    tc1 = TestCase(
        question_id=question.id,
        stdin="2 3\n",
        expected_output="5\n",
        is_hidden=False,
        position=0,
    )
    tc2 = TestCase(
        question_id=question.id,
        stdin="10 20\n",
        expected_output="30\n",
        is_hidden=True,
        position=1,
    )
    db_session.add_all([tc1, tc2])

    # 2. Setup team
    team = Team(name="Main Flow Team", passcode="pass")
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)

    # 3. Login to get token
    login_resp = await client.post(
        "/api/auth/login",
        json={"name": "Main Flow Team", "passcode": "pass"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["session_token"]
    headers = {"X-Team-Token": token}

    # 4. Get questions
    q_resp = await client.get("/api/main/questions", headers=headers)
    assert q_resp.status_code == 200
    questions_list = q_resp.json()
    assert isinstance(questions_list, list)
    assert len(questions_list) >= 1

    # 5. Check clock
    clock_resp = await client.get("/api/main/clock", headers=headers)
    assert clock_resp.status_code == 200
    assert clock_resp.json()["started"] is True

    # 6. Run code (sample tests only)
    python_code = "a, b = map(int, input().split())\nprint(a + b)\n"
    run_resp = await client.post(
        "/api/main/run",
        headers=headers,
        json={
            "question_id": question.id,
            "language": "python",
            "source_code": python_code,
        },
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["verdict"] == "PASSED"
    assert len(run_data["results"]) == 1  # 1 sample test

    # 7. Submit code
    submit_resp = await client.post(
        "/api/main/submit",
        headers=headers,
        json={
            "question_id": question.id,
            "language": "python",
            "source_code": python_code,
        },
    )
    assert submit_resp.status_code == 200
    sub_data = submit_resp.json()
    assert sub_data["verdict"] == "PASSED"
    assert sub_data["score"] == 100
    assert len(sub_data["results"]) == 2  # 1 sample + 1 hidden
