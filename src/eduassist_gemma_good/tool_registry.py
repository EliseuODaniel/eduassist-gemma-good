from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AccessPolicy = Literal["public", "scoped_protected", "deny_only", "local_document"]
ToolStatus = Literal["active", "planned"]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    required: tuple[str, ...]
    output_schema: dict[str, Any]
    access_policy: AccessPolicy
    audit_label: str
    output_contract: str
    status: ToolStatus = "active"
    planner_enabled: bool = True
    examples: tuple[str, ...] = ()

    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": self.parameters,
            "required": list(self.required),
        }

    def planner_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema(),
        }


TOOL_REGISTRY: dict[str, ToolDefinition] = {
    "search_public_knowledge": ToolDefinition(
        name="search_public_knowledge",
        description="Search synthetic public school policy documents.",
        parameters={"query": {"type": "string"}},
        required=("query",),
        output_schema={
            "type": "object",
            "properties": {
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_id": {"type": "string"},
                            "title": {"type": "string"},
                            "excerpt": {"type": "string"},
                            "access": {"type": "string", "const": "public"},
                            "rank": {"type": "integer"},
                            "score": {"type": "number"},
                            "matched_terms": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "source_id",
                            "title",
                            "excerpt",
                            "access",
                            "rank",
                            "score",
                            "matched_terms",
                        ],
                    },
                }
            },
            "required": ["documents"],
        },
        access_policy="public",
        audit_label="Public school knowledge search",
        output_contract="Public evidence documents only",
        examples=("Enrollment document guidance", "Attendance policy lookup"),
    ),
    "get_student_snapshot": ToolDefinition(
        name="get_student_snapshot",
        description="Fetch a synthetic protected student support snapshot.",
        parameters={"student_id": {"type": "string"}},
        required=("student_id",),
        output_schema={
            "type": "object",
            "properties": {
                "student": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string"},
                        "name": {"type": "string"},
                        "grade_level": {"type": "string"},
                        "attendance_rate": {"type": "number"},
                        "current_focus": {"type": "string"},
                        "latest_alert": {"type": "string"},
                    },
                    "required": [
                        "student_id",
                        "name",
                        "grade_level",
                        "attendance_rate",
                        "current_focus",
                        "latest_alert",
                    ],
                }
            },
            "required": ["student"],
        },
        access_policy="scoped_protected",
        audit_label="Scoped student snapshot",
        output_contract="Protected synthetic student summary after persona authorization",
        examples=("Guardian asks about their child", "Teacher reviews assigned class support"),
    ),
    "build_study_plan": ToolDefinition(
        name="build_study_plan",
        description="Build a short support plan from an authorized student snapshot.",
        parameters={
            "student_id": {"type": "string"},
            "focus": {"type": "string"},
        },
        required=("student_id", "focus"),
        output_schema={
            "type": "object",
            "properties": {
                "plan": {
                    "type": "object",
                    "properties": {
                        "student_name": {"type": "string"},
                        "focus": {"type": "string"},
                        "steps": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["student_name", "focus", "steps"],
                }
            },
            "required": ["plan"],
        },
        access_policy="scoped_protected",
        audit_label="Authorized recovery plan",
        output_contract="Short protected support plan for an authorized student",
        examples=("Weekly recovery plan", "Teacher-supported remediation steps"),
    ),
    "deny_request": ToolDefinition(
        name="deny_request",
        description="Return a safe denial when access is not allowed.",
        parameters={"reason": {"type": "string"}},
        required=("reason",),
        output_schema={
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
        access_policy="deny_only",
        audit_label="Safe privacy denial",
        output_contract="Denial reason without protected evidence",
        examples=("Cross-student request", "Unknown protected student request"),
    ),
    "extract_notice_facts": ToolDefinition(
        name="extract_notice_facts",
        description="Extract dates, deadlines, documents, and contacts from a local notice.",
        parameters={
            "notice_text": {"type": "string"},
            "source_name": {"type": "string"},
        },
        required=("notice_text", "source_name"),
        output_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "dates": {"type": "array", "items": {"type": "string"}},
                "deadlines": {"type": "array", "items": {"type": "string"}},
                "required_documents": {"type": "array", "items": {"type": "string"}},
                "contacts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "dates", "deadlines", "required_documents", "contacts"],
        },
        access_policy="local_document",
        audit_label="Local notice fact extraction",
        output_contract="Structured facts from user-provided local document text",
        status="planned",
        planner_enabled=False,
        examples=("Enrollment notice PDF", "Recovery exam notice image OCR text"),
    ),
    "generate_family_checklist": ToolDefinition(
        name="generate_family_checklist",
        description="Turn extracted notice facts into plain-language next actions.",
        parameters={
            "title": {"type": "string"},
            "dates": {"type": "array", "items": {"type": "string"}},
            "deadlines": {"type": "array", "items": {"type": "string"}},
            "required_documents": {"type": "array", "items": {"type": "string"}},
            "contacts": {"type": "array", "items": {"type": "string"}},
        },
        required=("title",),
        output_schema={
            "type": "object",
            "properties": {
                "checklist": {"type": "array", "items": {"type": "string"}},
                "message": {"type": "string"},
                "safety_note": {"type": "string"},
            },
            "required": ["checklist", "message", "safety_note"],
        },
        access_policy="local_document",
        audit_label="Family checklist generator",
        output_contract="Plain-language checklist and school message draft",
        status="planned",
        planner_enabled=False,
        examples=("What to do today", "Message to school office"),
    ),
    "draft_school_message": ToolDefinition(
        name="draft_school_message",
        description="Draft a short message that a family can send to the school.",
        parameters={
            "context": {"type": "string"},
            "recipient": {"type": "string"},
        },
        required=("context", "recipient"),
        output_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "tone": {"type": "string"},
            },
            "required": ["message", "tone"],
        },
        access_policy="local_document",
        audit_label="School message draft",
        output_contract="Family-facing message draft based on validated local context",
        status="planned",
        planner_enabled=False,
        examples=("Ask about missing documents", "Request recovery exam support"),
    ),
}

ACTIVE_TOOL_NAMES = frozenset(
    name for name, definition in TOOL_REGISTRY.items() if definition.status == "active"
)
PLANNER_TOOL_NAMES = frozenset(
    name
    for name, definition in TOOL_REGISTRY.items()
    if definition.status == "active" and definition.planner_enabled
)


def tool_definition(name: str) -> ToolDefinition | None:
    return TOOL_REGISTRY.get(name)


def is_active_tool(name: str) -> bool:
    return name in ACTIVE_TOOL_NAMES


def is_planner_tool(name: str) -> bool:
    return name in PLANNER_TOOL_NAMES


def tool_schemas() -> list[dict[str, Any]]:
    return [
        definition.planner_schema()
        for definition in TOOL_REGISTRY.values()
        if definition.name in PLANNER_TOOL_NAMES
    ]
