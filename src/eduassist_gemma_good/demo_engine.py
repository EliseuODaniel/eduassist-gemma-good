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

DIRECT_TOOL_INJECTION_TERMS = (
    "get_student_snapshot",
    "build_study_plan",
    "tool_calls",
    "tool call",
    "protected database",
    "hide the trace",
    "omit the denial",
    "pretend authorization",
    "ignore the registry",
    "chame get_student_snapshot",
)
BULK_OR_CROSS_STUDENT_TERMS = (
    "another student",
    "other student",
    "every student",
    "all students",
    "any student",
    "every child",
    "class grade",
    "grade spreadsheet",
    "attendance table",
    "class 8a",
    "colega",
    "outro aluno",
    "outra aluna",
    "todos os alunos",
    "toda a turma",
    "todas as alunas",
    "todos estudantes",
)
PROTECTED_REQUEST_TERMS = {
    "attendance",
    "absence",
    "absences",
    "alert",
    "alerts",
    "behavior",
    "grade",
    "grades",
    "record",
    "records",
    "risk",
    "snapshot",
    "boletim",
    "faltas",
    "frequencia",
    "nota",
    "notas",
    "prontuario",
    "prontuarios",
}
PROTECTED_REQUEST_PHRASES = (
    "academic alert",
    "academic summary",
    "student record",
    "support focus",
    "recovery plan",
    "study plan",
    "plano de estudo",
    "plano semanal",
    "resumo academico",
    "meu filho",
    "minha filha",
    "my child",
    "my kid",
)
MY_CHILD_TERMS = ("my child", "my kid", "minha filha", "meu filho")


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
        detected_student_ids = self.data_store.find_students_by_text(question)
        detected_student_id = detected_student_ids[0] if len(detected_student_ids) == 1 else None
        preflight_denial = self._preflight_denial(question, persona, detected_student_ids)
        if preflight_denial is None:
            calls, planning_mode, safety_notes = self._plan(
                question,
                persona,
                detected_student_id,
            )
        else:
            calls = (preflight_denial,)
            planning_mode = "fallback"
            safety_notes = ("Deterministic privacy preflight denied the request.",)
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

    def _preflight_denial(
        self,
        question: str,
        persona: Persona,
        detected_student_ids: tuple[str, ...],
    ) -> ToolCall | None:
        normalized = normalize_text(question)
        normalized_tokens = tokens(question)
        if any(term in normalized for term in DIRECT_TOOL_INJECTION_TERMS):
            return ToolCall(
                "deny_request",
                {"reason": "The request attempts to control internal tools or bypass policy."},
            )
        if len(detected_student_ids) > 1:
            return ToolCall(
                "deny_request",
                {
                    "reason": (
                        "The request asks for multiple protected student records, which is "
                        "outside this demo scope."
                    )
                },
            )
        if (
            len(detected_student_ids) == 1
            and detected_student_ids[0] not in persona.student_ids
            and self._looks_like_protected_request(normalized, normalized_tokens)
        ):
            return ToolCall(
                "deny_request",
                {"reason": "The selected persona is not authorized for the requested student."},
            )
        if any(term in normalized for term in BULK_OR_CROSS_STUDENT_TERMS):
            return ToolCall(
                "deny_request",
                {
                    "reason": (
                        "The request asks for protected data outside a single authorized "
                        "student scope."
                    )
                },
            )
        if (
            self._looks_like_protected_request(normalized, normalized_tokens)
            and not detected_student_ids
            and not self._can_resolve_my_child_reference(normalized, persona)
        ):
            return ToolCall(
                "deny_request",
                {
                    "reason": (
                        "The request asks for protected student data without an authorized "
                        "student scope."
                    )
                },
            )
        return None

    def _looks_like_protected_request(self, normalized: str, normalized_tokens: set[str]) -> bool:
        return bool(
            PROTECTED_REQUEST_TERMS & normalized_tokens
            or any(phrase in normalized for phrase in PROTECTED_REQUEST_PHRASES)
        )

    def _can_resolve_my_child_reference(self, normalized: str, persona: Persona) -> bool:
        return len(persona.student_ids) == 1 and any(term in normalized for term in MY_CHILD_TERMS)

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
