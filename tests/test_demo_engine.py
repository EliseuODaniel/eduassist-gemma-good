from eduassist_gemma_good.demo_engine import DemoEngine


def test_public_question_uses_public_search() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("What documents do I need for enrollment?", "public")

    assert response.access_decision == "public"
    assert response.tool_results[0].call.name == "search_public_knowledge"


def test_guardian_student_plan_is_allowed() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Create a recovery study plan for my child.", "guardian_ana")

    assert response.access_decision == "protected_allowed"
    assert [result.call.name for result in response.tool_results] == [
        "get_student_snapshot",
        "build_study_plan",
    ]


def test_guardian_other_student_is_denied() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Show Mateus Rocha's attendance.", "guardian_ana")

    assert response.access_decision == "restricted_denied"
    assert response.tool_results[0].status == "denied"
