from eduassist_gemma_good.config import DATA_DIR
from eduassist_gemma_good.question_bank import (
    count_questions_by_group,
    filter_questions,
    load_prepared_questions,
)


def test_loads_registered_eval_questions() -> None:
    questions = load_prepared_questions(DATA_DIR)

    assert len(questions) >= 150
    assert {question.group_key for question in questions} == {
        "authorized_support",
        "privacy_guardrails",
        "public_information",
    }
    assert any("Qual e" in question.question for question in questions)
    assert any("Ignore privacy" in question.question for question in questions)


def test_filters_questions_by_demo_group() -> None:
    questions = load_prepared_questions(DATA_DIR)

    assert len(filter_questions(questions, "public_information")) >= 50
    assert len(filter_questions(questions, "authorized_support")) >= 50
    assert len(filter_questions(questions, "privacy_guardrails")) >= 50
    assert len(filter_questions(questions, "all_cases")) == len(questions)


def test_counts_questions_by_demo_group() -> None:
    questions = load_prepared_questions(DATA_DIR)
    counts = count_questions_by_group(questions)

    assert counts["public_information"] >= 50
    assert counts["authorized_support"] >= 50
    assert counts["privacy_guardrails"] >= 50
    assert counts["all_cases"] == len(questions)
