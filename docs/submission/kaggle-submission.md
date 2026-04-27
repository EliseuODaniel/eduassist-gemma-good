# Kaggle Submission Package

## Project Title

EduAssist Field Kit: Private, Offline School Assistance with Gemma 4

## One-line Summary

EduAssist Field Kit uses Gemma 4 running locally to help families and school
staff turn school notices, public questions, and scoped student-support requests
into safe next actions while deterministic tools enforce student-data scope,
evidence grounding, and auditable denials.

## Impact Area

Future of Education and Digital Equity.

## Public Links

- Code repository: https://github.com/EliseuODaniel/eduassist-gemma-good
- Demo video: to be added after recording
- Live demo: optional; local Gemma demo instructions are in the README
- Evidence pack: `docs/submission/evidence/sample-outputs.md`
- Media gallery guide: `docs/submission/media-gallery.md`

## Writeup

Schools need to answer everyday questions from families, guardians, and staff:
What documents are required for enrollment? When are recovery exams? How is my
child doing, and what should we do next? These questions become harder in
low-connectivity communities and in privacy-sensitive environments, where sending
student records to a remote chatbot is often inappropriate.

EduAssist Field Kit is a working proof-of-concept for a local-first school
assistant. It runs Gemma 4 E4B locally through llama.cpp and exposes a Streamlit
interface for four common workflows: document intake, public school information,
authorized guardian or teacher support, and safe denial of restricted student
data.

Gemma 4 is central to the application. It is used first as a tool planner: given
the user's question, selected persona, authorized synthetic student ids, and
available tool schemas, Gemma proposes a compact JSON tool call. The Python
application then validates the tool name, arguments, and persona scope before
execution. Gemma is used again as a grounded composer: it receives only validated
tool results and produces the final answer from evidence. The model never gets
direct database access.

The Gemma integration follows the official documentation more closely than a
plain chat wrapper. Planner prompts use a Gemma-oriented function-calling
contract, the parser accepts `parameters`, one-call JSON, multi-call JSON, direct
JSON arrays, legacy `arguments`, and native `<|tool_call>` markers, and the
composer returns structured JSON for the answer, checklist, recovery plan,
school message draft, and safety note. Image notice uploads can also attempt a
local Gemma vision transcription path before falling back to local OCR/text
extraction. The repo includes a visual PNG school notice for a reproducible
image-intake demo. For explicit recovery-plan requests, the executor
deterministically adds `build_study_plan` when Gemma has already selected an
authorized student snapshot but omitted the follow-up call, preserving a
reliable product workflow without expanding model privileges.

The app intentionally uses a lightweight custom planner-executor-composer loop
instead of LangGraph or a specialist supervisor. That keeps the hackathon demo
local, auditable, and easy to explain: Gemma plans and writes, while Python owns
tool validation, access policy, and execution. Public retrieval is also local:
weighted lexical search with bilingual query expansion returns ranked evidence
plus `score` and `matched_terms`, while protected student data remains a scoped
deterministic lookup rather than a retriever.

The deterministic tool layer includes public document search, protected
synthetic student snapshots, study-plan generation, and explicit denial results.
This design makes the answer inspectable: the UI shows runtime mode, access
decision, tool trace, arguments, status, and evidence. A judge can see not only
the answer, but why the app was allowed to answer.

The demo data is synthetic by design. It includes public school documents,
protected student snapshots, and an expanded 181-case regression set that covers
public information, authorized protected support, restricted denials, document
intake, Portuguese prompts, and malicious notice text. The Streamlit app uses
the question subset as a prepared scenario picker, so the demo can be replayed
consistently. Local validation on April 27, 2026 passed 181/181 offline cases,
including 54/54 restricted-data denials with zero protected-evidence leaks. GPU
validation on an NVIDIA GeForce RTX 4070 Laptop GPU confirmed llama.cpp
offloaded 43/43 layers to CUDA, with generation-time GPU utilization observed at
86-92%. The curated 12-case `--representative-gemma-suite` also passed 12/12
with local Gemma, including 3/3 restricted-data denials and zero protected
evidence leaks.

After an adversarial 1131-case stress battery exposed weaknesses in generic
protected requests, class-wide private exports, direct tool-injection phrasing,
public policy-boundary questions, private administrative data requests, and
mixed named-person prompts, the app added deterministic preflight before Gemma
planning. The current stress
result is 1131/1131 in deterministic mode, and the balanced 110-case local Gemma
submission proof suite passed 110/110 with no failure clusters.

The main technical challenge was balancing model usefulness with privacy. A plain
chatbot could easily over-answer or invent access. EduAssist Field Kit instead
gives Gemma a narrow planning role and keeps authorization in deterministic
Python code. If a guardian asks for another student's grades, the app returns a
denial tool result and never exposes that restricted record to the composer.

This is not a finished production identity platform. It is a focused hackathon
prototype showing a deployable pattern: local open-model reasoning plus small,
auditable tools. For schools with limited connectivity or strict privacy needs,
that pattern can provide AI help without making protected data an invisible
cloud dependency.

## Demo Checklist

- Start the local model with `make llm-up`.
- Start the app with `make app`.
- Show the sidebar: Gemma endpoint online, model id, prepared-case coverage.
- Click `Run winning demo` and show the scorecards.
- Show the document intake workflow with `enrollment-support-notice.png` or
  `enrollment-support-notice.md`.
- Run the public enrollment question.
- Run the authorized recovery-plan question.
- Run the privacy denial question.
- Show `make eval`, `--submission-gemma-suite`, the generated evaluation
  artifacts, or the evidence pack.

## Final Pre-submission Checklist

- Repository is public.
- README includes setup, Gemma usage, evaluation, and safety posture.
- Demo script is ready for a 3-4 minute video.
- Technical writeup is present in `docs/submission/technical-writeup.md`.
- Evaluation plan is present in `docs/submission/evaluation-plan.md`.
- Implementation status is present in `docs/submission/implementation-status.md`.
- Evidence pack is present in `docs/submission/evidence/sample-outputs.md`.
- Media guide and SVG assets are present in `docs/submission/media-gallery.md`
  and `docs/submission/assets/`.
- Demo video URL is added after recording.
- Kaggle submission form is filled with this package.
