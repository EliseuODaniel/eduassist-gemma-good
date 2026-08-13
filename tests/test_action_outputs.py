from eduassist_gemma_good.action_outputs import action_output_from_response
from eduassist_gemma_good.demo_engine import DemoEngine
from eduassist_gemma_good.schema import PERSONAS, AssistantResponse


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


def test_structured_gemma_action_output_takes_precedence() -> None:
    response = AssistantResponse(
        question="What documents do I need?",
        persona=PERSONAS["public"],
        answer="Bring documents.",
        access_decision="public",
        runtime_mode="gemma",
        tool_results=(),
        evidence=(),
        structured_output={
            "action_output": {
                "title": "Gemma structured output",
                "checklist": ["Collect the listed documents."],
                "plan": [],
                "message": "Hello, I need document help.",
                "safety_note": "Generated from validated tool results.",
            }
        },
    )

    output = action_output_from_response(response)

    assert output.title == "Gemma structured output"
    assert output.checklist == ("Collect the listed documents.",)
