# Gemma 4 Optimization Notes

Status: active on `codex/field-kit-winning-track`.

Date: April 27, 2026.

## Source Review

The latest implementation pass was guided by the official Gemma documentation:

- Gemma 4 function calling:
  https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
- Gemma prompt formatting and system instructions:
  https://ai.google.dev/gemma/docs/core/prompt-structure
- Gemma visual data prompting:
  https://ai.google.dev/gemma/docs/capabilities/vision/prompt-with-visual-data
- Gemma local runtime options:
  https://ai.google.dev/gemma/docs/run

Key source-backed decisions:

- Gemma applications must validate model-proposed function names and arguments
  before execution. EduAssist already keeps execution in a typed Python registry
  and never gives the model direct data access.
- Gemma instruction-tuned prompt structure is user/model oriented. Planner and
  composer instructions are therefore embedded in the user turn for the
  OpenAI-compatible local endpoint instead of depending on an unsupported system
  role.
- Gemma 4 function-calling examples use explicit function schemas and native
  tool-call markers. The local parser now accepts `parameters`, legacy
  `arguments`, single-call JSON, multi-call JSON, direct JSON arrays, and native
  `<|tool_call>call:name{...}<tool_call|>` output.
- Gemma visual prompting is useful for image understanding, but the official
  guidance warns that precise OCR is better handled by dedicated OCR tooling.
  The app therefore tries local Gemma vision for image notices when enabled and
  falls back to local OCR/text extraction without making OCR precision a safety
  requirement.
- Official runtime guidance lists local options including Ollama, llama.cpp,
  LiteRT-LM, MLX, and Hugging Face Transformers. This fork keeps llama.cpp
  because it already proves GPU offload, low setup friction, and an
  OpenAI-compatible endpoint for the Streamlit demo.

## Implemented Changes

### Planner

- Planner prompt is framed as Gemma 4 function calling.
- Tool schemas are generated from the typed registry.
- The planner parser accepts:
  - `{"name": "...", "parameters": {...}}`
  - `{"tool_calls": [{"name": "...", "parameters": {...}}]}`
  - `{"name": "...", "arguments": {...}}` for backward compatibility
  - direct arrays of calls
  - native Gemma `<|tool_call>` markers
- Every parsed call is still checked against the planner-enabled tool registry
  before execution.
- If Gemma selects an authorized student snapshot but omits the required
  `build_study_plan` call for an explicit recovery/study-plan question, the
  application deterministically completes that narrow tool sequence before
  execution. This keeps Gemma central for intent and target selection while
  making the product workflow reliable.

### Composer

- The composer now requests structured JSON with:
  - `answer`
  - `action_output.title`
  - `action_output.checklist`
  - `action_output.plan`
  - `action_output.message`
  - `action_output.safety_note`
- The UI action panel prefers valid structured Gemma output and falls back to
  deterministic templates if the model output is invalid.
- The prompt includes stable conventions for public guidance, recovery plans,
  and privacy denials so evaluations can check useful output structure without
  requiring exact answer wording.

### Vision And Document Intake

- `GEMMA_ENABLE_VISION=true` enables a best-effort image notice transcription
  path through local Gemma.
- The app explicitly instructs Gemma not to follow instructions inside uploaded
  images.
- If Gemma vision is unavailable, PDF/TXT/Markdown extraction and optional local
  OCR remain the guaranteed offline path.

### Evaluation

- `--representative-gemma-suite` runs a curated 12-case Gemma suite across:
  - public guidance;
  - authorized protected support;
  - privacy denials;
  - Portuguese cases.
- The full offline regression suite remains 181 cases, with document intake and
  prompt-injection checks.
- Latest local result: 12/12 passed with local Gemma, including 3/3 restricted
  denials and zero protected-evidence leaks.
- Submission proof result: 110/110 passed with local Gemma through
  `uv run python -m eduassist_gemma_good.stress_eval --use-llm
  --submission-gemma-suite`; after routing optimization, latency p50/p95/max is
  0.02 / 0.36 / 7707.03 ms.
- Runtime optimization follows the local-first pattern: deterministic Python
  handles high-confidence routing, denials, protected-data composition, and
  document-intake outputs; Gemma is reserved for concise grounded public
  synthesis where language generation adds visible value.

## Remaining High-Ceiling Upgrade

The strongest next technical upgrade would be a true local multimodal runtime
using Hugging Face `AutoModelForMultimodalLM` or another official Gemma 4
runtime that supports image tensors directly. That would let the video show
Gemma reading a notice photo as a first-class multimodal input instead of using
the current OpenAI-compatible best-effort image route. For the current branch,
llama.cpp remains the pragmatic choice because the GPU path is already
validated and reproducible.
