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
EduAssist Local is a Gemma 4 Good project for schools that need useful AI
support without sending every private student question to a cloud model. Gemma 4
runs locally, while narrow deterministic tools keep data access auditable.
```

## Scene 2: Public school information, 0:35-1:20

Demo scenario: Public information.
Prepared question: Public visitor | What documents do I need for enrollment?

Question:

```text
What documents do I need for enrollment?
```

Show:

- answer from public evidence;
- `search_public_knowledge` trace;
- public access decision.

Narration:

```text
For public procedures, Gemma plans a public document search and then writes a
plain-language answer from retrieved evidence. The UI shows the tool trace and
source, so this is not a black-box chatbot response.
```

## Scene 3: Authorized guardian support, 1:20-2:20

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
student record. Gemma can request the study-plan tool, but Python validates the
persona, arguments, and access before any protected data reaches the composer.
```

## Scene 4: Safe denial, 2:20-3:10

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

## Closing, 3:10-3:40

Emphasize the product thesis:

EduAssist Local uses Gemma 4 for local reasoning and language, while deterministic
tools keep school data scoped, auditable, and useful in low-connectivity
environments.

Final line:

```text
The result is a local-first education assistant: practical for families, useful
for schools, and designed around privacy, digital equity, and transparent AI.
```
