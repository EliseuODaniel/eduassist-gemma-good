from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo_engine import DemoEngine

ROOT = Path(__file__).resolve().parents[2]
EVAL_SET = ROOT / "data" / "demo" / "evals" / "gemma_good_24q.jsonl"
ARTIFACTS = ROOT / "artifacts"


def load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def run_eval(*, use_llm: bool = False, path: Path = EVAL_SET) -> dict:
    engine = DemoEngine(use_llm=use_llm)
    cases = load_cases(path)
    rows = []
    passed = 0
    for case in cases:
        response = engine.answer(case["question"], case["persona"])
        tools = [result.call.name for result in response.tool_results]
        statuses = [result.status for result in response.tool_results]
        ok = True
        expected_tool = case.get("expected_tool")
        expected_access = case.get("expected_access")
        if expected_tool and expected_tool not in tools:
            ok = False
        if expected_access and response.access_decision != expected_access:
            ok = False
        if case.get("expected_denial") and "denied" not in statuses:
            ok = False
        passed += int(ok)
        rows.append(
            {
                "id": case["id"],
                "ok": ok,
                "persona": case["persona"],
                "question": case["question"],
                "expected_tool": expected_tool,
                "tools": tools,
                "expected_access": expected_access,
                "access": response.access_decision,
                "runtime": response.runtime_mode,
                "answer_chars": len(response.answer),
            }
        )
    return {
        "use_llm": use_llm,
        "total": len(cases),
        "passed": passed,
        "pass_rate": round(passed / len(cases), 3) if cases else 0,
        "rows": rows,
    }


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
        "",
        "| id | ok | expected tool | access | runtime |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['id']} | {row['ok']} | {row['expected_tool']} | "
            f"{row['access']} | {row['runtime']} |"
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
    args = parser.parse_args()

    report = run_eval(use_llm=args.use_llm, path=args.dataset)
    write_report(report)
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
