# Submission Media Gallery

Use these versioned assets in the Kaggle media gallery and video planning.

## Cover

- File: `docs/submission/assets/eduassist-local-cover.svg`
- Purpose: repository cover and first Kaggle media card.
- Message: local Gemma, auditable policy tools, synthetic data, 181-case eval.

## Architecture

- File: `docs/submission/assets/field-kit-architecture.svg`
- Purpose: show why the project is not a generic chatbot.
- Message: Gemma plans and composes; Python validates policy and executes
  narrow tools; retrieval and protected data remain local and auditable.

## Demo Storyboard

- File: `docs/submission/assets/field-kit-storyboard.svg`
- Purpose: guide a 3-4 minute demo video.
- Message: one coherent field-worker story: notice intake, public guidance,
  authorized support, privacy denial, evaluation evidence.

## Evidence Pack

- File: `docs/submission/evidence/sample-outputs.md`
- Purpose: copy/paste source for the Kaggle writeup and narration.
- Message: concrete outputs for document intake, public guidance, protected
  recovery plan, and privacy denial.

## Image Notice

- File: `data/demo/notices/enrollment-support-notice.png`
- Purpose: show a visible school notice in the document-intake workflow.
- Message: image intake is local-first; Gemma vision can transcribe when
  available, and the sample carries embedded OCR text for reproducible demos.

## Recommended Video Order

1. Show local Gemma endpoint online.
2. Click `Run winning demo` for the end-to-end story in one screen.
3. Run document intake on `enrollment-support-notice.png`.
4. Run public enrollment guidance and point at retrieval score/matched terms.
5. Run guardian recovery plan and point at protected evidence scope.
6. Run cross-student privacy request and point at empty protected evidence.
7. Show `make eval`, the 90-case Gemma submission suite command, or
   `docs/submission/evidence/sample-outputs.md`.
