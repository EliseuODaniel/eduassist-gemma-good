from eduassist_gemma_good.model_client import (
    calls_from_model_json,
    calls_from_model_text,
    parse_composition_json,
    parse_json_array,
    parse_json_object,
    parse_json_string_field,
    planner_prompt,
)
from eduassist_gemma_good.schema import PERSONAS


def test_planner_prompt_uses_gemma_native_function_calling_shape() -> None:
    prompt = planner_prompt("Create a plan for my child.", PERSONAS["guardian_ana"], None)

    assert [message["role"] for message in prompt] == ["user"]
    assert '"parameters"' in prompt[0]["content"]
    assert "Available functions" in prompt[0]["content"]


def test_tool_parser_accepts_single_gemma_function_call() -> None:
    calls = calls_from_model_json(
        {"name": "search_public_knowledge", "parameters": {"query": "enrollment"}}
    )

    assert len(calls) == 1
    assert calls[0].name == "search_public_knowledge"
    assert calls[0].arguments == {"query": "enrollment"}


def test_tool_parser_accepts_parameters_in_multi_call_shape() -> None:
    calls = calls_from_model_json(
        {
            "tool_calls": [
                {"name": "get_student_snapshot", "parameters": {"student_id": "stu_ana_luiza"}},
                {
                    "name": "build_study_plan",
                    "parameters": {
                        "student_id": "stu_ana_luiza",
                        "focus": "weekly recovery",
                    },
                },
            ]
        }
    )

    assert [call.name for call in calls] == ["get_student_snapshot", "build_study_plan"]


def test_json_array_parser_supports_direct_function_call_lists() -> None:
    parsed = parse_json_array('[{"name":"deny_request","parameters":{"reason":"restricted"}}]')

    assert isinstance(parsed, list)
    assert parsed[0]["name"] == "deny_request"


def test_tool_parser_accepts_native_gemma_tool_call_tokens() -> None:
    calls = calls_from_model_text(
        '<|tool_call>call:build_study_plan{student_id:<|"|>stu_ana_luiza<|"|>,'
        'focus:<|"|>weekly recovery<|"|>}<tool_call|><|tool_response>'
    )

    assert len(calls) == 1
    assert calls[0].name == "build_study_plan"
    assert calls[0].arguments == {
        "student_id": "stu_ana_luiza",
        "focus": "weekly recovery",
    }


def test_tool_parser_accepts_json_array_text() -> None:
    calls = calls_from_model_text(
        '[{"name":"deny_request","parameters":{"reason":"restricted request"}}]'
    )

    assert len(calls) == 1
    assert calls[0].name == "deny_request"


def test_structured_composer_json_is_validated() -> None:
    parsed = parse_json_object(
        """
        {
          "answer": "Use the school office.",
          "action_output": {
            "title": "Family guidance output",
            "checklist": ["Bring documents."],
            "plan": [],
            "message": "Hello, I need help.",
            "safety_note": "Public documents only."
          }
        }
        """
    )

    assert parsed is not None
    result = parse_composition_json(parsed)

    assert result is not None
    answer, structured = result
    assert answer == "Use the school office."
    assert structured["action_output"]["checklist"] == ["Bring documents."]


def test_json_string_field_parser_recovers_answer_from_truncated_composer_json() -> None:
    answer = parse_json_string_field(
        '{ "answer": "Bring a guardian ID and proof of residence.", "action_output": {',
        "answer",
    )

    assert answer == "Bring a guardian ID and proof of residence."
