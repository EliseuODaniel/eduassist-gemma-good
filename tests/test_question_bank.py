from eduassist_gemma_good.config import DATA_DIR
from eduassist_gemma_good.question_bank import (
    count_questions_by_group,
    filter_questions,
    load_prepared_questions,
)


def test_loads_registered_eval_questions() -> None:
    questions = load_prepared_questions(DATA_DIR)

    assert len(questions) == 24
    assert {question.group_key for question in questions} == {
        "authorized_support",
        "privacy_guardrails",
        "public_information",
    }


def test_filters_questions_by_demo_group() -> None:
    questions = load_prepared_questions(DATA_DIR)

    assert len(filter_questions(questions, "public_information")) == 12
    assert len(filter_questions(questions, "authorized_support")) == 7
    assert len(filter_questions(questions, "privacy_guardrails")) == 5
    assert len(filter_questions(questions, "all_cases")) == 24


def test_counts_questions_by_demo_group() -> None:
    questions = load_prepared_questions(DATA_DIR)

    assert count_questions_by_group(questions) == {
        "public_information": 12,
        "authorized_support": 7,
        "privacy_guardrails": 5,
        "all_cases": 24,
    }
