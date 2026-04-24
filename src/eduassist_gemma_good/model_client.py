from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .config import Settings
from .schema import Persona, RuntimeMode, ToolCall, ToolResult
from .tool_registry import is_planner_tool, tool_schemas

JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class ModelText:
    text: str
    runtime_mode: RuntimeMode


class GemmaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.gemma_api_key,
            base_url=settings.gemma_base_url,
            timeout=settings.gemma_request_timeout_seconds,
        )

    def chat(
        self,
        messages: Sequence[dict[str, str]],
        *,
        max_tokens: int = 700,
        temperature: float = 0.4,
    ) -> ModelText | None:
        try:
            response = self.client.chat.completions.create(
                model=self.settings.gemma_model,
                messages=list(messages),
                temperature=temperature,
                top_p=0.95,
                max_tokens=max_tokens,
            )
        except Exception:
            return None
        text = response.choices[0].message.content or ""
        if not text.strip():
            return None
        return ModelText(text=text.strip(), runtime_mode="gemma")


def parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    candidates = [stripped]
    match = JSON_OBJECT_RE.search(stripped)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def planner_prompt(
    question: str,
    persona: Persona,
    detected_student_id: str | None,
) -> list[dict[str, str]]:
    tool_text = json.dumps(tool_schemas(), indent=2)
    student_hint = detected_student_id or "none"
    return [
        {
            "role": "system",
            "content": (
                "You are Gemma 4 acting as a school-assistance tool planner. "
                "Return only compact JSON. Do not answer the user. "
                "Choose only from the provided tool names. The application will validate "
                "authorization before executing anything."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Persona: {persona.label} ({persona.role}).\n"
                f"Authorized synthetic student ids: {list(persona.student_ids)}.\n"
                f"Detected student id from text: {student_hint}.\n"
                f"Question: {question}\n\n"
                f"Available tools:\n{tool_text}\n\n"
                "Return JSON with this shape: "
                '{"tool_calls":[{"name":"...", "arguments":{}}], '
                '"safety_notes":["..."]}. '
                "Use deny_request for clearly unauthorized protected data. "
                "If the user says my child and exactly one synthetic student id is "
                "authorized, use that student id. "
                "If the user asks for a recovery, study, or support plan for an "
                "authorized student, include get_student_snapshot first and "
                "build_study_plan second."
            ),
        },
    ]


def composition_prompt(
    question: str,
    persona: Persona,
    results: Sequence[ToolResult],
) -> list[dict[str, str]]:
    result_payload = [
        {
            "tool": result.call.name,
            "status": result.status,
            "payload": result.payload,
            "evidence": [item.__dict__ for item in result.evidence],
        }
        for result in results
    ]
    return [
        {
            "role": "system",
            "content": (
                "You are Gemma 4 writing a school-assistance answer. "
                "Use only the validated tool results. If access was denied, do not reveal "
                "protected data. Keep the answer concise, helpful, and in the same language "
                "as the user's question when possible."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Persona: {persona.label}\n"
                f"Question: {question}\n"
                "Validated tool results:\n"
                f"{json.dumps(result_payload, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def calls_from_model_json(parsed: dict[str, Any]) -> tuple[ToolCall, ...]:
    raw_calls = parsed.get("tool_calls", [])
    if not isinstance(raw_calls, list):
        return ()
    calls: list[ToolCall] = []
    for raw_call in raw_calls:
        if not isinstance(raw_call, dict):
            continue
        name = raw_call.get("name")
        arguments = raw_call.get("arguments", {})
        if (
            not isinstance(name, str)
            or not is_planner_tool(name)
            or not isinstance(arguments, dict)
        ):
            continue
        calls.append(ToolCall(name=name, arguments=arguments, proposed_by="gemma"))
    return tuple(calls)
