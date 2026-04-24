# EduAssist Field Kit for Gemma 4 Good

EduAssist Field Kit is a Gemma 4 Good hackathon fork of the EduAssist school
service platform. It demonstrates a local-first assistant for schools and
families in low-connectivity contexts, using Gemma 4 as the central reasoning
and response engine while deterministic tools enforce access control and
evidence grounding.

This repository is intentionally smaller than the source EduAssist platform. It
contains only synthetic data, a demo app, a local Gemma 4 runtime recipe, and the
submission writeup assets needed for a public hackathon repo.

![EduAssist Field Kit submission cover](docs/submission/assets/eduassist-local-cover.svg)

## Why this project

Schools often need to answer operational and student-support questions without
depending on a cloud LLM for every private interaction. EduAssist Field Kit shows a
privacy-preserving flow:

1. A family member or school staff user asks a question.
2. Gemma 4 proposes a narrow tool plan.
3. The application validates the requested tool call and access scope.
4. Deterministic tools retrieve public policy documents or synthetic protected
   student snapshots.
5. Gemma 4 writes the final answer using only validated evidence.
6. The UI exposes the tool trace, evidence, and access decision for auditability.

The result is not a generic chatbot. It is a local, auditable school assistance
workflow aimed at Digital Equity and Future of Education.

## Gemma 4 usage

The demo is built around Gemma 4 E4B running locally through llama.cpp with an
OpenAI-compatible HTTP API. The app uses Gemma in two places:

- tool planning: pick from a small, validated set of school-assistance tools;
- grounded composition: generate the final answer from retrieved evidence and
  policy decisions.

The orchestration is a lightweight custom planner-executor-composer loop rather
than LangGraph or a specialist supervisor. That keeps the public hackathon fork
easy to run locally and makes each tool, policy decision, and retrieved evidence
item visible in the UI trace. Public retrieval is local weighted lexical search
with bilingual query expansion and auditable `rank`, `score`, and
`matched_terms` metadata.

The Field Kit branch also adapts the prompts and parsers to Gemma's documented
function-calling behavior. Planner output may use `parameters`, legacy
`arguments`, one-call JSON, multi-call JSON, direct JSON arrays, or native
Gemma `<|tool_call>` markers. The composer requests structured JSON for
answer/checklist/plan/message/safety-note output, and image notice uploads can
try a local Gemma vision transcription path before falling back to local
OCR/text extraction.

If the local model is unavailable, the app falls back to a deterministic planner
and composer so judges can still inspect the product flow. The intended
submission demo should run with the local Gemma service enabled.

Official references used for this design:

- Kaggle challenge: https://www.kaggle.com/competitions/gemma-4-good-hackathon
- Gemma 4 launch: https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Gemma model card: https://ai.google.dev/gemma/docs/model_card
- Gemma 4 function calling guide:
  https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
- Gemma prompt formatting:
  https://ai.google.dev/gemma/docs/core/prompt-structure
- Gemma visual data prompting:
  https://ai.google.dev/gemma/docs/capabilities/vision/prompt-with-visual-data

## Quick start

Install Python dependencies with uv:

```bash
uv sync --dev
```

Start the demo app without a model, using the deterministic fallback:

```bash
uv run streamlit run src/eduassist_gemma_good/app.py
```

Start the local Gemma 4 E4B service:

```bash
cp .env.example .env
make llm-up
```

The first run builds the CUDA-enabled llama.cpp image and downloads
`gemma-4-E4B-it-Q4_K_M.gguf` from `ggml-org/gemma-4-E4B-it-GGUF`, so it can take
several minutes. Later runs reuse the Docker image and Hugging Face cache.

Then run the app with Gemma enabled:

```bash
make app
```

Open http://localhost:8501.

On the `codex/field-kit-winning-track` branch, the app is reframed as
EduAssist Field Kit. It includes `Field kit workflow` and `Scenario card`
selectors populated from the same expanded question battery used by
`make eval`. The `Document intake` workflow can read local TXT, Markdown, or PDF
school notices, extract dates/documents/support channels, and produce a family
checklist plus school message draft without a cloud dependency. Image OCR is
wired as an optional local path when OCR tooling is installed.

## Evaluation

Run the fast offline evaluation:

```bash
make eval
```

Run the same evaluation with local Gemma calls:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm
```

Reports are written to `artifacts/eval_report.json` and
`artifacts/eval_report.md`.

Run a small representative Gemma smoke without spending time on the full suite:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm \
  --case-id public_enrollment_01 \
  --case-id protected_guardian_02 \
  --case-id denied_guardian_01
```

Run the larger curated Gemma representative suite:

```bash
uv run python -m eduassist_gemma_good.eval_runner --use-llm \
  --representative-gemma-suite
```

Current local validation:

- Gemma runtime: `ggml-org/gemma-4-E4B-it-GGUF`, file
  `gemma-4-E4B-it-Q4_K_M.gguf`;
- hardware smoke: NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB VRAM;
- CUDA offload confirmed by llama.cpp logs: `offloaded 43/43 layers to GPU`;
- generation-time GPU utilization observed at 86-92% with about 4.6 GB VRAM in
  use;
- expanded offline evaluation: 181/181 passed, pass rate 1.0, with 54/54
  restricted-data denials and zero denial leak failures.
- curated Gemma representative suite: 12/12 passed with local Gemma across
  public information, authorized support, privacy guardrails, and Portuguese
  cases; denial safety remained 3/3 with zero protected-evidence leaks.

## Repository map

- `src/eduassist_gemma_good/` - demo app and local-first assistant engine.
- `data/demo/public/` - synthetic public school documents.
- `data/demo/protected/` - synthetic protected student snapshots.
- `data/demo/evals/` - seed evaluation cases; generated templates expand the
  Field Kit regression battery.
- `data/demo/notices/` - sample school notices for the Field Kit document intake.
- `infra/compose/` - local Gemma 4 E4B service and optional demo-web service.
- `docs/submission/` - hackathon writeup, demo script, evaluation plan, and
  implementation status.
- `docs/strategy/orchestration-and-retrieval.md` - architecture decision for the
  custom orchestration loop and local retrieval path.
- `docs/strategy/gemma-4-optimization.md` - official-doc-backed Gemma prompt,
  tool-call, structured-output, and vision optimization notes.
- `docs/submission/evidence/sample-outputs.md` - concrete sample outputs for
  the demo story.
- `docs/submission/media-gallery.md` - versioned SVG assets and video order for
  the Kaggle media gallery.
- `docs/submission/kaggle-submission.md` - title, summary, writeup, links, and
  final checklist for the Kaggle form.

## Safety posture

- No real student data is stored here.
- Model calls never access a database directly.
- Tools are explicit, narrow, and validated before execution.
- Protected answers are denied unless the selected persona has scope.
- The final answer is instructed to use only retrieved evidence.
