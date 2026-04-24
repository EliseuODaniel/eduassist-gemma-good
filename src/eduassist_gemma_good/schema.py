from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

AccessDecision = Literal["public", "protected_allowed", "restricted_denied"]
RuntimeMode = Literal["gemma", "fallback"]


@dataclass(frozen=True)
class Persona:
    key: str
    label: str
    role: str
    student_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Evidence:
    source_id: str
    title: str
    excerpt: str
    access: Literal["public", "protected"]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    proposed_by: RuntimeMode = "fallback"


@dataclass(frozen=True)
class ToolResult:
    call: ToolCall
    status: Literal["ok", "denied", "error"]
    payload: dict[str, Any]
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class AssistantResponse:
    question: str
    persona: Persona
    answer: str
    access_decision: AccessDecision
    runtime_mode: RuntimeMode
    tool_results: tuple[ToolResult, ...]
    evidence: tuple[Evidence, ...]
    safety_notes: tuple[str, ...] = ()
    structured_output: dict[str, Any] = field(default_factory=dict)


PERSONAS = {
    "public": Persona(
        key="public",
        label="Public visitor",
        role="anonymous",
        student_ids=(),
    ),
    "guardian_ana": Persona(
        key="guardian_ana",
        label="Marina Costa, guardian of Ana Luiza",
        role="guardian",
        student_ids=("stu_ana_luiza",),
    ),
    "teacher_8a": Persona(
        key="teacher_8a",
        label="Professor Rafael, 8A homeroom teacher",
        role="teacher",
        student_ids=("stu_ana_luiza", "stu_mateus_rocha"),
    ),
}
