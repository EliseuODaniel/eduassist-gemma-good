from eduassist_gemma_good.stress_eval import (
    generate_stress_cases,
    run_stress_eval,
    submission_gemma_cases,
)


def test_stress_generator_covers_major_risk_categories() -> None:
    cases = generate_stress_cases()
    categories = {case["category"] for case in cases}

    assert len(cases) >= 700
    assert {
        "public_information",
        "authorized_snapshot",
        "authorized_plan",
        "denial_public_named",
        "denial_public_generic_protected",
        "denial_guardian_other_student",
        "denial_bulk_or_cross_student",
        "denial_tool_injection",
        "document_intake",
    } <= categories


def test_stress_eval_runs_stratified_subset() -> None:
    report = run_stress_eval(use_llm=False, limit=45)

    assert report["total"] == 45
    assert set(report["latency_ms"]) == {"max", "p50", "p95"}
    assert "by_category" in report


def test_submission_gemma_suite_is_balanced_90_case_set() -> None:
    cases = submission_gemma_cases()
    counts = {}
    for case in cases:
        counts[case["category"]] = counts.get(case["category"], 0) + 1

    assert len(cases) == 90
    assert set(counts.values()) == {10}

    report = run_stress_eval(use_llm=False, submission_gemma_suite=True)

    assert report["suite"] == "submission_gemma_90"
    assert report["total"] == 90
    assert report["passed"] == 90
