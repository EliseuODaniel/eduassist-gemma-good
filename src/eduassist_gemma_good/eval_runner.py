from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from .action_outputs import action_output_from_response
from .demo_engine import DemoEngine
from .eval_cases import load_eval_cases
from .notice_intake import action_output_from_notice, extract_notice_facts

ROOT = Path(__file__).resolve().parents[2]
EVAL_SET = ROOT / "data" / "demo" / "evals" / "gemma_good_24q.jsonl"
ARTIFACTS = ROOT / "artifacts"


def load_cases(path: Path) -> list[dict]:
    return load_eval_cases(path)


def run_eval(
    *,
    use_llm: bool = False,
    path: Path = EVAL_SET,
    case_ids: tuple[str, ...] = (),
) -> dict:
    engine = DemoEngine(use_llm=use_llm)
    cases = load_cases(path)
    if case_ids:
        allowed_ids = set(case_ids)
        cases = [case for case in cases if case["id"] in allowed_ids]
    rows = []
    passed = 0
    denial_total = 0
    denial_passed = 0
    denial_leak_failures = 0
    for case in cases:
        started = time.perf_counter()
        row = (
            _run_notice_case(case)
            if case.get("kind") == "notice"
            else _run_question_case(engine, case)
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        row["latency_ms"] = latency_ms
        ok = bool(row["ok"])
        passed += int(ok)
        if case.get("expected_denial"):
            denial_total += 1
            denial_passed += int(ok)
            denial_leak_failures += int(not row.get("leak_ok", True))
        rows.append(row)
    latencies = [row["latency_ms"] for row in rows]
    return {
        "use_llm": use_llm,
        "total": len(cases),
        "passed": passed,
        "pass_rate": round(passed / len(cases), 3) if cases else 0,
        "by_category": _category_summary(rows),
        "denial_total": denial_total,
        "denial_passed": denial_passed,
        "denial_pass_rate": round(denial_passed / denial_total, 3) if denial_total else 0,
        "denial_leak_failures": denial_leak_failures,
        "latency_ms": _latency_summary(latencies),
        "rows": rows,
    }


def _run_question_case(engine: DemoEngine, case: dict) -> dict:
    response = engine.answer(case["question"], case["persona"])
    output = action_output_from_response(response)
    tools = [result.call.name for result in response.tool_results]
    statuses = [result.status for result in response.tool_results]
    expected_tool = case.get("expected_tool")
    expected_access = case.get("expected_access")
    tool_ok = not expected_tool or expected_tool in tools
    access_ok = not expected_access or response.access_decision == expected_access
    denial_ok = not case.get("expected_denial") or "denied" in statuses
    leak_ok = not case.get("expected_denial") or not response.evidence
    structured_ok = _contains_terms(
        _action_output_text(output),
        case.get("expected_output_terms", ()),
    )
    ok = tool_ok and access_ok and denial_ok and leak_ok and structured_ok
    return {
        "id": case["id"],
        "kind": "question",
        "ok": ok,
        "category": case.get("category", expected_access),
        "persona": case["persona"],
        "question": case["question"],
        "expected_tool": expected_tool,
        "tools": tools,
        "tool_ok": tool_ok,
        "expected_access": expected_access,
        "access": response.access_decision,
        "access_ok": access_ok,
        "denial_ok": denial_ok,
        "leak_ok": leak_ok,
        "structured_ok": structured_ok,
        "runtime": response.runtime_mode,
        "answer_chars": len(response.answer),
    }


def _run_notice_case(case: dict) -> dict:
    facts = extract_notice_facts(case["notice_text"], case["source_name"])
    output = action_output_from_notice(facts)
    tools = ["extract_notice_facts", "generate_family_checklist"]
    expected_tool = case.get("expected_tool")
    tool_ok = not expected_tool or expected_tool in tools
    expected_access = case.get("expected_access", "public")
    facts_text = " ".join(
        [
            facts.title,
            *facts.dates,
            *facts.deadlines,
            *facts.required_documents,
            *facts.contacts,
            *facts.actions,
        ]
    )
    output_text = _action_output_text(output)
    structured_ok = _contains_terms(facts_text + " " + output_text, case.get("expected_terms", ()))
    injection_ok = _excludes_terms(output_text, case.get("forbidden_terms", ()))
    ok = tool_ok and structured_ok and injection_ok
    return {
        "id": case["id"],
        "kind": "notice",
        "ok": ok,
        "category": case.get("category", "document_intake"),
        "persona": "local_document",
        "question": case["source_name"],
        "expected_tool": expected_tool,
        "tools": tools,
        "tool_ok": tool_ok,
        "expected_access": expected_access,
        "access": "public",
        "access_ok": True,
        "denial_ok": True,
        "leak_ok": injection_ok,
        "structured_ok": structured_ok,
        "runtime": "local",
        "answer_chars": len(output_text),
    }


def _action_output_text(output) -> str:
    return " ".join(
        [output.title, *output.checklist, *output.plan, output.message, output.safety_note]
    )


def _contains_terms(text: str, terms) -> bool:
    normalized = text.lower()
    return all(str(term).lower() in normalized for term in terms)


def _excludes_terms(text: str, terms) -> bool:
    normalized = text.lower()
    return not any(str(term).lower() in normalized for term in terms)


def _category_summary(rows: list[dict]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for row in rows:
        category = str(row.get("category", "unknown"))
        bucket = summary.setdefault(category, {"total": 0, "passed": 0, "pass_rate": 0})
        bucket["total"] += 1
        bucket["passed"] += int(bool(row["ok"]))
    for bucket in summary.values():
        total = int(bucket["total"])
        bucket["pass_rate"] = round(int(bucket["passed"]) / total, 3) if total else 0
    return summary


def _latency_summary(latencies: list[float]) -> dict[str, float]:
    if not latencies:
        return {"p50": 0, "p95": 0, "max": 0}
    ordered = sorted(latencies)
    return {
        "p50": round(statistics.median(ordered), 2),
        "p95": round(_percentile(ordered, 0.95), 2),
        "max": round(max(ordered), 2),
    }


def _percentile(ordered: list[float], percentile: float) -> float:
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * percentile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def write_report(report: dict) -> None:
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / "eval_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# EduAssist Local Evaluation Report",
        "",
        f"- LLM enabled: `{report['use_llm']}`",
        f"- Passed: `{report['passed']}/{report['total']}`",
        f"- Pass rate: `{report['pass_rate']}`",
        f"- Denial pass rate: `{report['denial_pass_rate']}`",
        f"- Denial leak failures: `{report['denial_leak_failures']}`",
        f"- Latency p50/p95/max ms: "
        f"`{report['latency_ms']['p50']}` / "
        f"`{report['latency_ms']['p95']}` / "
        f"`{report['latency_ms']['max']}`",
        "",
        "## Category Summary",
        "",
        "| category | passed | total | pass rate |",
        "| --- | --- | --- | --- |",
    ]
    for category, bucket in report["by_category"].items():
        lines.append(
            f"| {category} | {bucket['passed']} | {bucket['total']} | {bucket['pass_rate']} |"
        )
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| id | ok | kind | expected tool | access | runtime | latency ms |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["rows"]:
        lines.append(
            f"| {row['id']} | {row['ok']} | {row['kind']} | {row['expected_tool']} | "
            f"{row['access']} | {row['runtime']} | {row['latency_ms']} |"
        )
    (ARTIFACTS / "eval_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Call the configured Gemma endpoint.",
    )
    parser.add_argument("--dataset", type=Path, default=EVAL_SET)
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Run only a specific case id. Can be passed more than once.",
    )
    args = parser.parse_args()

    report = run_eval(use_llm=args.use_llm, path=args.dataset, case_ids=tuple(args.case_id))
    write_report(report)
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
