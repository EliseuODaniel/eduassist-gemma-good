# Demo Script

Target video length: 3 to 4 minutes.

## Scene 1: Local-first setup, 0:00-0:35

Show the repository and run:

```bash
make llm-up
make app
```

Mention that Gemma 4 E4B is served locally through llama.cpp and the app talks
to it through an OpenAI-compatible endpoint.

In the sidebar, show that the Gemma endpoint is online. The app should display
the local model id returned by `/v1/models`.

Narration:

```text
EduAssist Field Kit is a Gemma 4 Good project for schools that need useful AI
support without sending every private student question to a cloud model. Gemma 4
runs locally to improve public guidance, while narrow deterministic tools keep
protected data access auditable.
```

## Scene 2: Document intake, 0:35-1:15

Demo scenario: Document intake.
Sample notice: `enrollment-support-notice.png`.

Show:

- visual notice intake without cloud OCR;
- local notice text extraction;
- important dates/documents/support channels;
- family checklist and school message draft.

Narration:

```text
The Field Kit starts from the kind of artifact families actually bring to school:
a notice, PDF, or photo. The sample image is local and reproducible, and the
workflow turns confusing instructions into dates, documents, and next actions.
```

## Scene 3: Public school information, 1:15-1:55

Demo scenario: Public information.
Prepared question: Public visitor | What documents do I need for enrollment?

Question:

```text
What documents do I need for enrollment?
```

Show:

- Gemma-rewritten answer from a validated public draft;
- `search_public_knowledge` trace;
- public access decision.

Narration:

```text
For public procedures, deterministic retrieval builds a safe draft from school
documents, and Gemma rewrites only that non-sensitive public guidance. The UI
shows the tool trace and source, including retrieval rank, score, and matched
terms, so this is not a black-box chatbot response.
```

## Scene 4: Authorized guardian support, 1:55-2:45

Demo scenario: Authorized student support.
Prepared question: Marina Costa, guardian of Ana Luiza | Create a recovery
study plan for my child.

Question:

```text
Create a recovery study plan for my child.
```

Show:

- protected access allowed;
- student snapshot and study plan tools;
- evidence panel with synthetic protected source;
- final grounded answer.

Narration:

```text
For a scoped guardian, the policy layer allows only that guardian's synthetic
student record. The protected answer is controlled by deterministic tools, so
Gemma never becomes the privacy boundary.
```

## Scene 5: Safe denial, 2:45-3:30

Demo scenario: Privacy guardrails.
Prepared question: Marina Costa, guardian of Ana Luiza | Can you show me another
student's grades?

Question:

```text
Can you show me another student's grades?
```

Show:

- `deny_request` tool;
- restricted denial;
- no protected record leaked.

Narration:

```text
When the same guardian asks for another student's grades, the app denies the
request through an explicit tool result. Gemma never receives the restricted
record, and the evidence panel stays empty.
```

## Closing, 3:30-3:55

Show the scorecards or terminal results:

```bash
make eval
uv run python -m eduassist_gemma_good.stress_eval --use-llm --submission-gemma-suite
```

Emphasize the product thesis:

EduAssist Field Kit uses Gemma 4 for local public-language improvement, while
deterministic tools keep school data scoped, auditable, and useful in
low-connectivity environments.

Final line:

```text
The result is a local-first education assistant: practical for families, useful
for schools, and designed around privacy, digital equity, and transparent AI.
```
