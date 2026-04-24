from __future__ import annotations

from collections.abc import Iterable

from .data_store import DemoDataStore
from .policy import can_access_student, explain_denial
from .schema import Evidence, Persona, ToolCall, ToolResult

ALLOWED_TOOL_NAMES = {
    "search_public_knowledge",
    "get_student_snapshot",
    "build_study_plan",
    "deny_request",
}


def tool_schemas() -> list[dict]:
    return [
        {
            "name": "search_public_knowledge",
            "description": "Search synthetic public school policy documents.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
        {
            "name": "get_student_snapshot",
            "description": "Fetch a synthetic protected student support snapshot.",
            "parameters": {
                "type": "object",
                "properties": {"student_id": {"type": "string"}},
                "required": ["student_id"],
            },
        },
        {
            "name": "build_study_plan",
            "description": "Build a short support plan from an authorized student snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string"},
                    "focus": {"type": "string"},
                },
                "required": ["student_id", "focus"],
            },
        },
        {
            "name": "deny_request",
            "description": "Return a safe denial when access is not allowed.",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    ]


class ToolExecutor:
    def __init__(self, data_store: DemoDataStore) -> None:
        self.data_store = data_store

    def execute_all(self, calls: Iterable[ToolCall], persona: Persona) -> tuple[ToolResult, ...]:
        return tuple(self.execute(call, persona) for call in calls)

    def execute(self, call: ToolCall, persona: Persona) -> ToolResult:
        if call.name not in ALLOWED_TOOL_NAMES:
            return ToolResult(call, "error", {"error": f"Unknown tool: {call.name}"})
        if call.name == "search_public_knowledge":
            query = str(call.arguments.get("query", ""))
            evidence = self.data_store.search_public(query)
            return ToolResult(
                call,
                "ok",
                {"documents": [evidence_item.__dict__ for evidence_item in evidence]},
                evidence,
            )
        if call.name == "get_student_snapshot":
            return self._student_snapshot(call, persona)
        if call.name == "build_study_plan":
            return self._study_plan(call, persona)
        return ToolResult(call, "denied", {"reason": str(call.arguments.get("reason", ""))})

    def _student_snapshot(self, call: ToolCall, persona: Persona) -> ToolResult:
        student_id = str(call.arguments.get("student_id", ""))
        if not can_access_student(persona, student_id):
            return ToolResult(call, "denied", {"reason": explain_denial(persona, student_id)})
        student = self.data_store.get_student(student_id)
        evidence = (
            Evidence(
                source_id=f"student:{student_id}",
                title=f"Synthetic support snapshot for {student['name']}",
                excerpt=(
                    f"{student['name']} is in {student['grade_level']}. "
                    f"Attendance is {student['attendance_rate']}%. "
                    f"Current focus: {student['current_focus']}. "
                    f"Latest alert: {student['latest_alert']}."
                ),
                access="protected",
            ),
        )
        return ToolResult(call, "ok", {"student": student}, evidence)

    def _study_plan(self, call: ToolCall, persona: Persona) -> ToolResult:
        student_id = str(call.arguments.get("student_id", ""))
        focus = str(call.arguments.get("focus", "weekly support"))
        if not can_access_student(persona, student_id):
            return ToolResult(call, "denied", {"reason": explain_denial(persona, student_id)})
        student = self.data_store.get_student(student_id)
        plan = {
            "student_name": student["name"],
            "focus": focus,
            "steps": [
                f"Review {student['current_focus']} with a teacher-provided example.",
                "Complete one 20 minute practice block on two weekdays.",
                "Send one question to the school support channel before Friday.",
                "Ask the teacher to confirm whether the missing activity was recovered.",
            ],
        }
        evidence = (
            Evidence(
                source_id=f"plan:{student_id}",
                title=f"Synthetic support plan for {student['name']}",
                excerpt=" ".join(plan["steps"]),
                access="protected",
            ),
        )
        return ToolResult(call, "ok", {"plan": plan}, evidence)
