# Evaluation Plan

The demo includes a small 24-question regression set in
`data/demo/evals/gemma_good_24q.jsonl`.

The evaluation checks:

- whether the expected tool is used;
- whether public, protected, and restricted requests receive the expected access
  decision;
- whether denial cases produce a denied tool result;
- whether the runtime used Gemma or deterministic fallback.

Run:

```bash
make eval
```

Run with Gemma enabled:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm
```

This is not a benchmark of raw model intelligence. It is a product regression
suite that tests the core promises of the submission:

- public questions are answered from public school documents;
- authorized guardians and teachers can access only scoped synthetic records;
- unauthorized protected questions are denied;
- the app remains inspectable through tool traces and evidence panels.
