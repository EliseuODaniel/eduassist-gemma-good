from eduassist_gemma_good.stress_eval import generate_stress_cases, run_stress_eval


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
