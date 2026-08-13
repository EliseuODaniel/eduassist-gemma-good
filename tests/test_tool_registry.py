from eduassist_gemma_good.demo_engine import DemoEngine
from eduassist_gemma_good.tool_registry import (
    ACTIVE_TOOL_NAMES,
    PLANNER_TOOL_NAMES,
    TOOL_REGISTRY,
    is_active_tool,
    is_planner_tool,
    tool_definition,
    tool_schemas,
)


def test_active_tool_names_match_runtime_executor_surface() -> None:
    assert ACTIVE_TOOL_NAMES == {
        "search_public_knowledge",
        "get_student_snapshot",
        "build_study_plan",
        "deny_request",
    }

    for tool_name in ACTIVE_TOOL_NAMES:
        assert is_active_tool(tool_name)
        assert is_planner_tool(tool_name)


def test_planner_schemas_are_generated_from_registry() -> None:
    schemas = tool_schemas()
    schema_by_name = {schema["name"]: schema for schema in schemas}

    assert set(schema_by_name) == PLANNER_TOOL_NAMES
    assert schema_by_name["build_study_plan"]["parameters"]["required"] == [
        "student_id",
        "focus",
    ]
    assert schema_by_name["search_public_knowledge"]["description"] == (
        TOOL_REGISTRY["search_public_knowledge"].description
    )
    public_document_schema = TOOL_REGISTRY["search_public_knowledge"].output_schema["properties"][
        "documents"
    ]["items"]
    assert {"rank", "score", "matched_terms"} <= set(public_document_schema["required"])


def test_planned_notice_tools_are_registered_but_not_planner_enabled() -> None:
    planned_names = {
        "draft_school_message",
        "extract_notice_facts",
        "generate_family_checklist",
    }

    assert planned_names <= set(TOOL_REGISTRY)
    assert planned_names.isdisjoint(ACTIVE_TOOL_NAMES)
    assert planned_names.isdisjoint(PLANNER_TOOL_NAMES)
    assert planned_names.isdisjoint({schema["name"] for schema in tool_schemas()})


def test_registered_tools_have_audit_and_contract_metadata() -> None:
    for tool_name in TOOL_REGISTRY:
        definition = tool_definition(tool_name)

        assert definition is not None
        assert definition.audit_label
        assert definition.access_policy in {
            "deny_only",
            "local_document",
            "public",
            "scoped_protected",
        }
        assert definition.input_schema()["properties"]
        assert definition.output_schema["properties"]
        assert definition.output_contract


def test_student_snapshot_payload_matches_registry_contract() -> None:
    engine = DemoEngine(use_llm=False)

    response = engine.answer("Show Ana Luiza grades.", "guardian_ana")
    snapshot = response.tool_results[0].payload["student"]

    assert response.tool_results[0].call.name == "get_student_snapshot"
    assert snapshot["student_id"] == "stu_ana_luiza"
