from eduassist_gemma_good.action_outputs import action_output_from_response
from eduassist_gemma_good.demo_engine import DemoEngine


def test_public_response_becomes_family_checklist() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("What documents do I need for enrollment?", "public")
    output = action_output_from_response(response)

    assert output.title == "Family guidance output"
    assert output.checklist
    assert "public" in output.safety_note.lower()
    assert response.question in output.message


def test_study_plan_response_becomes_action_plan() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Create a recovery study plan for my child.", "guardian_ana")
    output = action_output_from_response(response)

    assert output.title == "Recovery plan output"
    assert len(output.plan) == 4
    assert "Ana Luiza" in output.message


def test_denied_response_becomes_privacy_output() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Can you show me another student's grades?", "guardian_ana")
    output = action_output_from_response(response)

    assert output.title == "Privacy protection output"
    assert "Do not reveal protected student details." in output.checklist
    assert "authorized" in output.message
