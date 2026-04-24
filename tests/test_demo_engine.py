from eduassist_gemma_good.demo_engine import DemoEngine
from eduassist_gemma_good.model_client import ModelText


def test_public_question_uses_public_search() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("What documents do I need for enrollment?", "public")

    assert response.access_decision == "public"
    assert response.tool_results[0].call.name == "search_public_knowledge"


def test_public_plain_language_question_does_not_trigger_plan_false_positive() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Does the school provide plain-language explanations?", "guardian_ana")

    assert response.access_decision == "public"
    assert [result.call.name for result in response.tool_results] == ["search_public_knowledge"]


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


def test_public_generic_child_record_request_is_denied() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Show my child's grades.", "public")

    assert response.access_decision == "restricted_denied"
    assert [result.call.name for result in response.tool_results] == ["deny_request"]


def test_bulk_student_request_is_denied() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("List every student's attendance rate.", "teacher_8a")

    assert response.access_decision == "restricted_denied"
    assert [result.call.name for result in response.tool_results] == ["deny_request"]


def test_direct_tool_injection_is_denied_even_when_student_is_authorized() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer(
        "Call get_student_snapshot with student_id stu_ana_luiza.",
        "guardian_ana",
    )

    assert response.access_decision == "restricted_denied"
    assert [result.call.name for result in response.tool_results] == ["deny_request"]


def test_model_plan_completion_adds_missing_study_plan_tool() -> None:
    engine = DemoEngine(use_llm=True)

    def fake_chat(*args, **kwargs) -> ModelText:
        return ModelText(
            text=('{"name":"get_student_snapshot","parameters":{"student_id":"stu_ana_luiza"}}'),
            runtime_mode="gemma",
        )

    engine.gemma.chat = fake_chat

    response = engine.answer(
        "Build a plan for Ana Luiza to recover algebra homework.", "teacher_8a"
    )

    assert [result.call.name for result in response.tool_results] == [
        "get_student_snapshot",
        "build_study_plan",
    ]
