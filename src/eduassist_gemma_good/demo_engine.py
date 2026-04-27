from __future__ import annotations

import re
from collections.abc import Sequence

from .config import Settings, load_settings
from .data_store import DemoDataStore
from .model_client import (
    GemmaClient,
    calls_from_model_text,
    composition_prompt,
    parse_composition_json,
    parse_json_object,
    parse_json_string_field,
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
CAPITALIZED_NAME_RE = re.compile(
    r"\b[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ]+(?:\s+[A-ZÀ-ÖØ-Þ][A-Za-zÀ-ÖØ-öø-ÿ]+)+\b"
)
NAME_LEADING_STOPWORDS = {
    "build",
    "call",
    "compare",
    "create",
    "give",
    "list",
    "mostre",
    "plan",
    "qual",
    "recovery",
    "reveal",
    "show",
    "sou",
    "study",
    "tell",
    "use",
    "what",
}
RESTRICTED_ADMIN_PRIVATE_TERMS = (
    "employee file",
    "folha de pagamento",
    "medical records",
    "payroll",
    "principal staff file",
    "salary",
    "salario",
    "staff file",
    "staff salary",
)
PUBLIC_POLICY_QUESTION_PHRASES = (
    "are grades public",
    "authenticated access",
    "can public",
    "can teachers export",
    "can visitors",
    "public information",
    "public visitors",
    "podem exportar",
    "requires authenticated",
    "requires guardian access",
    "student records protected",
    "what is the policy",
    "what policy",
    "which student information",
    "allowed to see",
    "podem ver",
    "politica para",
    "politica de",
    "visitantes publicos",
)


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
        if preflight_denial is not None:
            calls = (preflight_denial,)
            planning_mode = "fallback"
            safety_notes = ("Deterministic privacy preflight denied the request.",)
        elif self._looks_like_public_policy_question(normalize_text(question)):
            calls = (ToolCall("search_public_knowledge", {"query": question}),)
            planning_mode = "fallback"
            safety_notes = ("Deterministic public-policy preflight routed to public documents.",)
        else:
            calls, planning_mode, safety_notes = self._plan(
                question,
                persona,
                detected_student_id,
            )
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
        if self._looks_like_public_policy_question(normalized):
            return (ToolCall("search_public_knowledge", {"query": question}),)
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
        if self._looks_like_restricted_admin_private_request(normalized) and not (
            self._looks_like_public_policy_question(normalized)
        ):
            return ToolCall(
                "deny_request",
                {
                    "reason": (
                        "The request asks for private administrative data outside "
                        "the public school information scope."
                    )
                },
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
            and not self._looks_like_public_policy_question(normalized)
        ):
            return ToolCall(
                "deny_request",
                {"reason": "The selected persona is not authorized for the requested student."},
            )
        if (
            self._looks_like_protected_request(normalized, normalized_tokens)
            and self._mentions_unrecognized_named_person(question, persona, detected_student_ids)
            and not self._looks_like_public_policy_question(normalized)
        ):
            return ToolCall(
                "deny_request",
                {
                    "reason": (
                        "The request appears to ask for a named person's protected "
                        "record outside the selected persona scope."
                    )
                },
            )
        if any(term in normalized for term in BULK_OR_CROSS_STUDENT_TERMS) and not (
            self._looks_like_public_policy_question(normalized)
        ):
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
            and not self._looks_like_public_policy_question(normalized)
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

    def _looks_like_public_policy_question(self, normalized: str) -> bool:
        return any(phrase in normalized for phrase in PUBLIC_POLICY_QUESTION_PHRASES)

    def _looks_like_restricted_admin_private_request(self, normalized: str) -> bool:
        return any(term in normalized for term in RESTRICTED_ADMIN_PRIVATE_TERMS)

    def _mentions_unrecognized_named_person(
        self,
        question: str,
        persona: Persona,
        detected_student_ids: tuple[str, ...],
    ) -> bool:
        allowed_entities: list[set[str]] = []
        for student_id in tuple(dict.fromkeys((*persona.student_ids, *detected_student_ids))):
            student = self.data_store.get_student(student_id)
            allowed_entities.append(tokens(student["name"]))
            allowed_entities.append(tokens(student["guardian"]))

        for candidate in CAPITALIZED_NAME_RE.findall(question):
            candidate_tokens = tokens(candidate)
            candidate_tokens -= NAME_LEADING_STOPWORDS
            if not candidate_tokens:
                continue
            if any(candidate_tokens <= allowed for allowed in allowed_entities):
                continue
            return True
        return False

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
                max_tokens=700,
                temperature=0.2,
            )
            if response is not None:
                parsed = parse_json_object(response.text)
                if self.settings.gemma_enable_structured_composer and parsed:
                    structured = parse_composition_json(parsed)
                    if structured is not None:
                        answer, structured_output = structured
                        return answer, "gemma", structured_output
                answer = parse_json_string_field(response.text, "answer")
                if answer is not None:
                    return answer, "gemma", {}
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
        if results and all(result.call.name == "search_public_knowledge" for result in results):
            return "public"
        return infer_access_intent(question)
