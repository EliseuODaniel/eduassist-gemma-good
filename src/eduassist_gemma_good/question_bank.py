from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreparedQuestion:
    id: str
    persona_key: str
    question: str
    expected_tool: str
    expected_access: str
    group_key: str


@dataclass(frozen=True)
class QuestionGroup:
    label: str
    expected: str


QUESTION_GROUPS = {
    "public_information": QuestionGroup(
        label="Public information",
        expected="Public answers grounded in school documents",
    ),
    "authorized_support": QuestionGroup(
        label="Authorized student support",
        expected="Protected answers for scoped guardians or staff",
    ),
    "privacy_guardrails": QuestionGroup(
        label="Privacy guardrails",
        expected="Safe denials for restricted student data",
    ),
    "all_cases": QuestionGroup(
        label="All prepared questions",
        expected="Full 24-question evaluation battery",
    ),
}


def load_prepared_questions(data_dir: Path) -> tuple[PreparedQuestion, ...]:
    path = data_dir / "evals" / "gemma_good_24q.jsonl"
    questions: list[PreparedQuestion] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        questions.append(
            PreparedQuestion(
                id=raw["id"],
                persona_key=raw["persona"],
                question=raw["question"],
                expected_tool=raw["expected_tool"],
                expected_access=raw["expected_access"],
                group_key=group_for_access(raw["expected_access"]),
            )
        )
    return tuple(questions)


def group_for_access(expected_access: str) -> str:
    if expected_access == "protected_allowed":
        return "authorized_support"
    if expected_access == "restricted_denied":
        return "privacy_guardrails"
    return "public_information"


def filter_questions(
    questions: tuple[PreparedQuestion, ...],
    group_key: str,
) -> tuple[PreparedQuestion, ...]:
    if group_key == "all_cases":
        return questions
    return tuple(question for question in questions if question.group_key == group_key)


def count_questions_by_group(
    questions: tuple[PreparedQuestion, ...],
) -> dict[str, int]:
    counts = dict.fromkeys(QUESTION_GROUPS, 0)
    for question in questions:
        counts[question.group_key] += 1
        counts["all_cases"] += 1
    return counts


def question_option_label(question: PreparedQuestion, persona_label: str) -> str:
    return f"{persona_label} | {question.question}"
