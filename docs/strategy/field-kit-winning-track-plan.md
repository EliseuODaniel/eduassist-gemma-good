# EduAssist Field Kit Winning Track Plan

Status: Phase 5 repository-side submission polish in progress.

Branch: `codex/field-kit-winning-track`.

## Decision

Keep the current fork as the canonical competition repository and build the
ambitious version on a new branch. Do not start a new repository yet.

Rationale:

- `main` already proves the local Gemma runtime, GPU setup, tool trace,
  persona-scoped access, evaluation, and submission package.
- A new branch lets us make large UX and architecture changes without risking
  the stable MVP.
- A new repository would slow us down with duplicated setup, history, and public
  documentation work.
- If the branch becomes a substantially different product, we can later rename
  or split it. That decision should happen after the winning-track prototype is
  demonstrably stronger than the current MVP.

## External Validation

The current public signal supports this direction:

- The hackathon is product-oriented: submissions are expected to demonstrate a
  working prototype, public code, technical writeup, demo/video assets, and a
  clear real-world use case.
- Strong submissions should solve one specific workflow for one clear user, not
  present a generic chatbot.
- Gemma 4's official positioning emphasizes local/edge deployment, multimodal
  input, native function calling, structured JSON output, long context, and
  multilingual capability.
- The strongest competitive angle for this repo is therefore not "school
  chatbot"; it is an offline, privacy-preserving school service field kit that
  uses Gemma 4's local and agentic strengths where cloud systems are weakest.

Primary references:

- Kaggle challenge page: https://www.kaggle.com/competitions/gemma-4-good-hackathon
- Google Gemma 4 launch: https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Gemma model card: https://ai.google.dev/gemma/docs/model_card
- Gemma function calling: https://ai.google.dev/gemma/docs/capabilities/function-calling
- LiteRT-LM repository: https://github.com/google-ai-edge/LiteRT-LM

Secondary validation:

- Public coverage of the hackathon consistently describes required artifacts as
  a working demo/prototype, public repository, technical writeup, and video.
- Public hackathon guidance emphasizes impact, storytelling, technical
  execution, and concrete workflows over overbuilt model science.

## Product Reframe

Rename the ambitious branch concept from **EduAssist Local** to:

**EduAssist Field Kit**

One-line pitch:

> EduAssist Field Kit helps low-connectivity schools turn documents, family
> questions, and student-support records into safe next actions using local
> Gemma 4 reasoning, multimodal intake, and deterministic access tools.

Primary user:

- A school secretary, teacher, or community school worker supporting families
  with limited internet, bureaucratic documents, and privacy-sensitive student
  questions.

Primary family benefit:

- Families receive plain-language answers, document checklists, recovery plans,
  and messages to send to school without exposing protected records to an
  external cloud chatbot.

Competition tracks:

- Future of Education.
- Digital Equity.
- Safety & Trust as the technical differentiator.

## Winning Demo Shape

The video should show one coherent story:

1. A family brings a photo or PDF of a school notice.
2. The app extracts deadlines, required documents, and next actions.
3. A guardian asks for help with the child's recovery plan.
4. Gemma plans tool calls; deterministic policy validates access.
5. The app generates a printable action plan and a message to the school.
6. The same user asks for another student's private data.
7. The app denies the request and shows that no protected evidence was exposed.
8. The presenter shows local Gemma, GPU/local runtime, and evaluation metrics.

The judge should understand the payoff in under 30 seconds:

> "This turns confusing school paperwork into private, actionable help, even
> where internet access is unreliable."

## Required Product Changes

### 1. Move from Chat Demo to Guided Workflow

Current state: question/answer app.

Target state: guided field-kit workflow with four modes:

- `Document Intake`: upload image/PDF/text notice and extract facts.
- `Family Guidance`: answer public/procedural questions from school documents.
- `Student Support`: authorized protected support and recovery planning.
- `Privacy Check`: visibly deny restricted requests.

### 2. Add Multimodal/Document Intake

Minimum viable path:

- PDF text extraction for official notices and forms.
- Image upload with OCR fallback.
- If Gemma 4 multimodal serving is available locally, route image understanding
  through Gemma.
- If local multimodal serving is not stable in llama.cpp, use OCR/text extraction
  first and clearly state that Gemma reasons over extracted local content.

Winning path:

- Demonstrate at least one image/PDF notice transformed into:
  - important dates;
  - required documents;
  - who should act;
  - checklist;
  - family-facing explanation.

### 3. Make Outputs Actionable

Add structured outputs:

- printable checklist;
- recovery plan;
- school message draft;
- escalation/safety note;
- "what to do today" summary.

This matters because a judge can see utility immediately.

### 4. Implement Native Tool Registry

Refactor tool planning into a typed registry:

- tool name;
- input schema;
- output schema;
- access policy;
- examples;
- audit label.

Tools to support:

- `extract_notice_facts`
- `search_public_school_docs`
- `get_student_snapshot`
- `build_recovery_plan`
- `draft_school_message`
- `generate_family_checklist`
- `deny_request`

The registry should be the single source for:

- Gemma function/tool schema prompts;
- execution validation;
- UI trace labels;
- evaluation expectations.

### 5. Improve Runtime Architecture

Pragmatic architecture for the branch:

```text
Streamlit or React UI
    -> FastAPI/domain service boundary
    -> Gemma planner/composer client
    -> typed tool registry
    -> access policy engine
    -> public/protected synthetic data stores
    -> evaluation runner
```

Recommendation:

- Keep Streamlit only for the first implementation sprint if speed matters.
- Introduce a service layer now so the UI can later move to React without
  rewriting policy, tools, and evaluation.
- Move product logic out of Streamlit before adding multimodal workflows.

### 6. Expand Evaluation

Current set: 181 cases from the original 24-case seed plus generated Field Kit
templates.

Winning target:

- 150+ synthetic cases.
- Portuguese and English.
- public notice/document questions;
- authorized guardian questions;
- teacher support questions;
- cross-student privacy attacks;
- prompt-injection attempts inside uploaded notices;
- low-connectivity/offline fallback checks;
- output structure checks for checklist/message/plan.

Metrics:

- expected tool hit rate;
- access decision accuracy;
- denial leak rate;
- structured output validity;
- evidence citation presence;
- runtime mode;
- latency p50/p95 for local Gemma.

Pass bar before submission:

- 95%+ overall pass rate.
- 100% pass on restricted-data denial cases.
- zero protected-evidence leaks in denied cases.

### 7. Add Product Evidence

Versioned artifacts:

- sample uploaded notice;
- sample output checklist;
- sample protected recovery plan;
- eval report;
- architecture diagram;
- 3-4 minute video script;
- cover image/media gallery assets.

## What Not To Do

- Do not expand into a broad "AI school platform."
- Do not rebuild the original `eduassist-platform` inside the hackathon repo.
- Do not make Gemma a generic chatbot behind a nicer UI.
- Do not rely on cloud-only services for the core demo.
- Do not add real student data.
- Do not add model-to-database access.

## Implementation Phases

### Phase 1: Product Skeleton

Goal: keep current behavior but reshape the app around Field Kit workflows.

Implementation status: complete on this branch.

Tasks:

- Rename visible product concept to EduAssist Field Kit on the branch. Done.
- Add workflow mode selector. Done.
- Move current question bank into scenario cards. Done.
- Add "action output" panel for checklist/plan/message. Done.
- Keep all current tests passing. Done.

Exit criteria:

- Current 24 eval cases still pass.
- Demo still runs with local Gemma.
- UI tells a clearer story.

### Phase 2: Document Intake

Goal: support uploaded notices/forms as first-class inputs.

Implementation status: minimum viable local intake complete.

Tasks:

- Add sample school notice files. Done.
- Implement local PDF text extraction. Done.
- Implement image OCR fallback if available locally. Done as an optional local
  path; PDF/TXT/MD remain the guaranteed demo path.
- Add `extract_notice_facts` and `generate_family_checklist`. Done as local
  notice fact extraction plus `Notice checklist output`.
- Add eval cases for notice extraction.

Exit criteria:

- A sample notice produces a structured checklist. Done.
- No cloud dependency is required for the demo path. Done.

### Phase 3: Tool Registry and Policy Refactor

Goal: make the agent architecture more serious and auditable.

Implementation status: complete on this branch for the active runtime tools.
The notice/document tools are registered as planned contracts and remain
disabled for Gemma planning until the workflow is promoted into the agent
executor.

Tasks:

- Create typed tool registry. Done.
- Generate planner schemas from registry. Done.
- Validate all tool calls through the registry. Done.
- Keep access policy deterministic. Done.
- Render tool descriptions and policy decisions in the UI trace. Done.

Exit criteria:

- All tools have typed input/output contracts. Done.
- All tool calls are auditable from one registry. Done.

### Phase 4: Evaluation Upgrade

Goal: prove reliability beyond the demo path.

Implementation status: complete on this branch for the offline regression path.
The runner also supports representative Gemma subsets through repeated
`--case-id` arguments and a curated 12-case `--representative-gemma-suite`.

Tasks:

- Expand eval set to 150+ cases. Done.
- Add malicious document/prompt-injection cases. Done.
- Add Portuguese cases. Done.
- Add structured output assertions. Done.
- Add latency/runtime summary. Done.

Exit criteria:

- 95%+ overall pass. Done: 181/181 offline.
- 100% denial pass. Done: 54/54 with zero denial leak failures.
- Gemma runtime shown on representative evals. Done: 12/12 curated Gemma
  representative suite passed with local Gemma.

### Phase 5: Submission Polish

Goal: make the branch submission-ready.

Implementation status: in progress. The architecture/retrieval decision is now
documented, and public retrieval has been upgraded with local weighted lexical
ranking plus bilingual query expansion. Gemma 4 prompt, tool-call, structured
output, and vision optimization decisions are documented in
`docs/strategy/gemma-4-optimization.md`. Versioned evidence, architecture media,
storyboard assets, and a curated 12-case Gemma representative suite have been
added. The 12-case suite now passes 12/12 with local Gemma; the remaining major
item is recording the external demo video.

Tasks:

- Finalize README for Field Kit. Done.
- Add screenshots/GIF or updated SVG media. Done with SVG cover,
  architecture, and storyboard assets.
- Update Kaggle writeup with metrics. Done.
- Record 3-4 minute video. Pending outside repository.
- Optional: publish fallback demo if low-friction.

Exit criteria:

- Public repo tells the story without private context. Done.
- Video shows end-to-end value in one coherent user journey. Ready to record
  from the storyboard; final video still pending.

## Recommendation

Start implementation on this branch, not a new repository.

The first implementation step should be Phase 1: refactor the app into Field Kit
workflow modes while preserving the current Gemma runtime and 24-case eval. That
gives us a safer base for multimodal/document intake in Phase 2.
