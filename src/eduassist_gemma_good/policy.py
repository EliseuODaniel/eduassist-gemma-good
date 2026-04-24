from __future__ import annotations

from .schema import AccessDecision, Persona
from .text_utils import normalize_text

PROTECTED_TERMS = {
    "grade",
    "grades",
    "attendance",
    "absence",
    "absences",
    "behavior",
    "risk",
    "student",
    "boletim",
    "nota",
    "notas",
    "faltas",
    "frequencia",
    "aluno",
    "aluna",
}

RESTRICTED_TERMS = {
    "another student",
    "other student",
    "colega",
    "outro aluno",
    "outra aluna",
    "payroll",
    "salary",
    "staff file",
    "medical record",
    "prontuario",
}


def infer_access_intent(question: str) -> AccessDecision:
    normalized = normalize_text(question)
    if any(term in normalized for term in RESTRICTED_TERMS):
        return "restricted_denied"
    if any(term in normalized.split() for term in PROTECTED_TERMS):
        return "protected_allowed"
    return "public"


def can_access_student(persona: Persona, student_id: str) -> bool:
    return student_id in persona.student_ids


def explain_denial(persona: Persona, student_id: str | None) -> str:
    subject = "that student" if student_id else "protected student data"
    return (
        f"{persona.label} is not authorized to access {subject}. "
        "The assistant can still answer public school policy questions."
    )
