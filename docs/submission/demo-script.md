# Demo Script

Target video length: 3 to 4 minutes.

## Scene 1: Local-first setup

Show the repository and run:

```bash
make llm-up
make app
```

Mention that Gemma 4 E4B is served locally through llama.cpp and the app talks
to it through an OpenAI-compatible endpoint.

In the sidebar, show that the Gemma endpoint is online. The app should display
the local model id returned by `/v1/models`.

## Scene 2: Public school information

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

## Scene 3: Authorized guardian support

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

## Scene 4: Safe denial

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

## Closing

Emphasize the product thesis:

EduAssist Local uses Gemma 4 for local reasoning and language, while deterministic
tools keep school data scoped, auditable, and useful in low-connectivity
environments.
