# Evaluation Plan

The demo keeps the original 24-question seed regression set in
`data/demo/evals/gemma_good_24q.jsonl` and expands it through versioned
templates in `src/eduassist_gemma_good/eval_cases.py`.

The Streamlit app exposes the expanded question battery as prepared demo
questions, grouped by public information, authorized support, and privacy
guardrail scenarios. The scenario is selected first, then the prepared question
loads its registered persona and expected outcome.

The evaluation checks:

- whether the expected tool is used;
- whether public, protected, and restricted requests receive the expected access
  decision;
- whether denial cases produce a denied tool result;
- whether denial cases expose no protected evidence;
- whether structured action outputs include the expected checklist/message/plan
  terms;
- whether local document intake extracts expected notice facts while ignoring
  prompt-injection text in generated family actions;
- whether the runtime used Gemma, local document processing, or deterministic
  fallback;
- latency p50, p95, and max for the run.

Run:

```bash
make eval
```

Run with Gemma enabled:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm
```

Run a representative Gemma subset:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm \
  --case-id public_enrollment_01 \
  --case-id protected_guardian_02 \
  --case-id denied_guardian_01
```

Run the broader curated Gemma representative suite:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm \
  --representative-gemma-suite
```

Run the adversarial stress battery:

```bash
uv run python -m eduassist_gemma_good.stress_eval
```

Run a stratified stress sample with local Gemma:

```bash
uv run python -m eduassist_gemma_good.stress_eval --use-llm --limit 45
```

Run the balanced 110-case submission proof suite with local Gemma:

```bash
uv run python -m eduassist_gemma_good.stress_eval --use-llm \
  --submission-gemma-suite
```

## Latest Local Result

On April 27, 2026, the expanded offline and stress suites passed locally:

- Runtime: Gemma 4 E4B served by llama.cpp through an OpenAI-compatible endpoint.
- Model artifact: `ggml-org/gemma-4-E4B-it-GGUF` /
  `gemma-4-E4B-it-Q4_K_M.gguf`.
- Hardware used: NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB VRAM.
- GPU validation: llama.cpp reported `offloaded 43/43 layers to GPU`, with
  `CUDA0` model, KV, and compute buffers. A live `nvidia-smi` sample during
  generation showed 86-92% GPU utilization and about 4.6 GB VRAM in use.
- Result: 181/181 cases passed, pass rate 1.0.
- Coverage: 60 public-information cases, 55 authorized-support cases, 54
  privacy-guardrail cases, and 12 document-intake cases.
- Denial safety: 54/54 restricted-data denials passed with zero protected
  evidence leaks.
- Structured checks: checklist/message/plan assertions are enforced for question
  responses, and notice intake checks expected facts plus prompt-injection
  exclusion from family-facing actions.
- Curated Gemma representative suite: 12/12 passed with local Gemma through
  `--representative-gemma-suite`, covering 4 public-information cases, 5
  authorized-support cases, 3 privacy-guardrail cases, and Portuguese prompts.
- Local Gemma denial safety in that suite: 3/3 restricted-data denials passed
  with zero protected-evidence leaks.
- Stress battery: 1131/1131 passed in deterministic mode after privacy preflight
  hardening. The first stress run found 275 failures, concentrated in generic
  protected public requests, bulk/cross-student requests, and direct tool
  injection attempts; those are now covered by deterministic preflight.
- Balanced local Gemma submission proof: 110/110 passed through
  `--submission-gemma-suite`, with 10/10 cases in each of 11 stress categories.
  High-confidence routing keeps deterministic privacy/protected-data paths out
  of the local model hot path while still using Gemma to rewrite public,
  non-sensitive answers from validated drafts.
- Local Gemma submission proof latency p50/p95/max:
  0.01 / 0.51 / 8328.24 ms.

This is not a benchmark of raw model intelligence. It is a product regression
suite that tests the core promises of the submission:

- public questions are answered from public school documents;
- authorized guardians and teachers can access only scoped synthetic records;
- unauthorized protected questions are denied;
- the app remains inspectable through tool traces and evidence panels.
