# Evaluation Plan

The demo includes a small 24-question regression set in
`data/demo/evals/gemma_good_24q.jsonl`.

The Streamlit app exposes this same set as prepared demo questions, grouped by
public information, authorized support, and privacy guardrail scenarios. The
scenario is selected first, then the prepared question loads its registered
persona and expected outcome.

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

## Latest Local Result

On April 24, 2026, the suite passed with the local Gemma runtime enabled:

- Runtime: Gemma 4 E4B served by llama.cpp through an OpenAI-compatible endpoint.
- Model artifact: `ggml-org/gemma-4-E4B-it-GGUF` /
  `gemma-4-E4B-it-Q4_K_M.gguf`.
- Hardware used: NVIDIA GeForce RTX 4070 Laptop GPU with 8 GB VRAM.
- GPU validation: llama.cpp reported `offloaded 43/43 layers to GPU`, with
  `CUDA0` model, KV, and compute buffers. A live `nvidia-smi` sample during
  generation showed 86-92% GPU utilization and about 4.6 GB VRAM in use.
- Result: 24/24 cases passed, pass rate 1.0.
- Coverage: public document search, authorized protected snapshots, study-plan
  tool calls, and restricted-data denials all used Gemma-planned tool traces.
- Final pre-submission rerun: `uv run python -m
  eduassist_gemma_good.eval_runner --use-llm` returned `24/24`, pass rate
  `1.0`, with every row reporting runtime `gemma`.

This is not a benchmark of raw model intelligence. It is a product regression
suite that tests the core promises of the submission:

- public questions are answered from public school documents;
- authorized guardians and teachers can access only scoped synthetic records;
- unauthorized protected questions are denied;
- the app remains inspectable through tool traces and evidence panels.
