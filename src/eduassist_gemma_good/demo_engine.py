from __future__ import annotations

from collections.abc import Sequence

from .config import Settings, load_settings
from .data_store import DemoDataStore
from .model_client import (
    GemmaClient,
    calls_from_model_text,
    composition_prompt,
    parse_composition_json,
    parse_json_object,
    planner_prompt,
)
from .policy import infer_access_intent
from .schema import (
    PERSONAS,
    AssistantResponse,
    Evidence,
    Persona,
    RuntimeMode,
    ToolCall,
    ToolResult,
)
from .text_utils import normalize_text, tokens
from .tools import ToolExecutor


class DemoEngine:
    def __init__(self, settings: Settings | None = None, *, use_llm: bool | None = None) -> None:
        self.settings = settings or load_settings()
        self.use_llm = (
            self.settings.gemma_enable_planner or self.settings.gemma_enable_composer
            if use_llm is None
            else use_llm
        )
        self.data_store = DemoDataStore(self.settings.data_dir)
        self.executor = ToolExecutor(self.data_store)
        self.gemma = GemmaClient(self.settings)

    def answer(self, question: str, persona_key: str = "public") -> AssistantResponse:
        persona = PERSONAS[persona_key]
        detected_student_id = self.data_store.find_student_by_text(question)
        calls, planning_mode, safety_notes = self._plan(question, persona, detected_student_id)
        results = self.executor.execute_all(calls, persona)
        answer, composition_mode, structured_output = self._compose(question, persona, results)
        evidence = tuple(item for result in results for item in result.evidence)
        access_decision = self._access_decision(results, evidence, question)
        runtime_mode: RuntimeMode = (
            "gemma" if "gemma" in {planning_mode, composition_mode} else "fallback"
        )
        return AssistantResponse(
            question=question,
            persona=persona,
            answer=answer,
            access_decision=access_decision,
            runtime_mode=runtime_mode,
            tool_results=results,
            evidence=evidence,
            safety_notes=tuple(safety_notes),
            structured_output=structured_output,
        )

    def _plan(
        self,
        question: str,
        persona: Persona,
        detected_student_id: str | None,
    ) -> tuple[tuple[ToolCall, ...], RuntimeMode, tuple[str, ...]]:
        if self.use_llm and self.settings.gemma_enable_planner:
            response = self.gemma.chat(
                planner_prompt(question, persona, detected_student_id),
                max_tokens=350,
                temperature=0.0,
            )
            if response is not None:
                calls = calls_from_model_text(response.text)
                if calls:
                    parsed = parse_json_object(response.text) or {}
                    notes = parsed.get("safety_notes", [])
                    if not isinstance(notes, list):
                        notes = []
                    return (
                        self._complete_model_plan(question, calls),
                        "gemma",
                        tuple(str(note) for note in notes),
                    )
        fallback_note = (
            "Gemma planner unavailable or returned an invalid tool plan; "
            "deterministic router used.",
        )
        return (
            self._fallback_plan(question, persona, detected_student_id),
            "fallback",
            fallback_note,
        )

    def _fallback_plan(
        self,
        question: str,
        persona: Persona,
        detected_student_id: str | None,
    ) -> tuple[ToolCall, ...]:
        normalized = normalize_text(question)
        normalized_tokens = tokens(question)
        target_student_id = detected_student_id
        if (
            target_student_id is None
            and persona.student_ids
            and (
                any(phrase in normalized for phrase in ("my child", "minha filha", "meu filho"))
                or {"ana", "grades", "notas"} & normalized_tokens
            )
        ):
            target_student_id = persona.student_ids[0]

        cross_student_terms = ("another student", "other student", "colega", "outro")
        if any(term in normalized for term in cross_student_terms):
            return (
                ToolCall(
                    "deny_request",
                    {
                        "reason": (
                            "The request asks for protected data outside "
                            "the selected persona scope."
                        )
                    },
                ),
            )

        if target_student_id and target_student_id not in persona.student_ids:
            return (
                ToolCall(
                    "deny_request",
                    {"reason": "The selected persona is not authorized for the requested student."},
                ),
            )

        if target_student_id:
            calls = [ToolCall("get_student_snapshot", {"student_id": target_student_id})]
            planning_terms = {
                "plan",
                "study",
                "plano",
                "estudo",
                "recover",
                "recovery",
                "recuperar",
                "recuperacao",
            }
            if planning_terms & normalized_tokens:
                calls.append(
                    ToolCall(
                        "build_study_plan",
                        {"student_id": target_student_id, "focus": "weekly academic recovery"},
                    )
                )
            return tuple(calls)

        return (ToolCall("search_public_knowledge", {"query": question}),)

    def _complete_model_plan(
        self,
        question: str,
        calls: tuple[ToolCall, ...],
    ) -> tuple[ToolCall, ...]:
        call_names = [call.name for call in calls]
        if "build_study_plan" in call_names or "get_student_snapshot" not in call_names:
            return calls

        planning_terms = {
            "plan",
            "study",
            "plano",
            "estudo",
            "recover",
            "recovery",
            "recuperar",
            "recuperacao",
        }
        if not (planning_terms & tokens(question)):
            return calls

        snapshot_call = next(call for call in calls if call.name == "get_student_snapshot")
        student_id = snapshot_call.arguments.get("student_id")
        if not isinstance(student_id, str) or not student_id:
            return calls

        return (
            *calls,
            ToolCall(
                "build_study_plan",
                {"student_id": student_id, "focus": "weekly academic recovery"},
            ),
        )

    def _compose(
        self,
        question: str,
        persona: Persona,
        results: Sequence[ToolResult],
    ) -> tuple[str, RuntimeMode, dict]:
        if self.use_llm and self.settings.gemma_enable_composer:
            response = self.gemma.chat(
                composition_prompt(question, persona, results),
                max_tokens=420,
                temperature=0.2,
            )
            if response is not None:
                parsed = parse_json_object(response.text)
                if self.settings.gemma_enable_structured_composer and parsed:
                    structured = parse_composition_json(parsed)
                    if structured is not None:
                        answer, structured_output = structured
                        return answer, "gemma", structured_output
                return response.text, "gemma", {}
        return self._fallback_compose(results), "fallback", {}

    def _fallback_compose(self, results: Sequence[ToolResult]) -> str:
        denied = [result for result in results if result.status == "denied"]
        if denied:
            return denied[0].payload.get(
                "reason",
                "I cannot provide protected student data for the selected persona.",
            )

        lines: list[str] = []
        for result in results:
            if result.call.name == "search_public_knowledge":
                docs = result.payload.get("documents", [])
                lines.append("I found public school guidance that matches the question:")
                for doc in docs:
                    lines.append(f"- {doc['title']}: {doc['excerpt']}")
            elif result.call.name == "get_student_snapshot":
                student = result.payload["student"]
                lines.append(
                    f"{student['name']} is in {student['grade_level']}. "
                    f"Attendance is {student['attendance_rate']}%, current focus is "
                    f"{student['current_focus']}, and the latest alert is: "
                    f"{student['latest_alert']}."
                )
            elif result.call.name == "build_study_plan":
                plan = result.payload["plan"]
                lines.append(f"Suggested support plan for {plan['student_name']}:")
                lines.extend(f"- {step}" for step in plan["steps"])
        return "\n".join(lines) if lines else "No matching evidence was found."

    def _access_decision(
        self,
        results: Sequence[ToolResult],
        evidence: Sequence[Evidence],
        question: str,
    ) -> str:
        if any(result.status == "denied" for result in results):
            return "restricted_denied"
        if any(item.access == "protected" for item in evidence):
            return "protected_allowed"
        return infer_access_intent(question)
