# Field Kit Sample Outputs

These examples show the product contract judges should look for in the UI. The
default optimized runtime uses Gemma only to rewrite public, non-sensitive
answers from validated drafts; protected support, denials, public-policy
boundaries, document intake, and action-output structure remain deterministic.

## 1. Document Intake

Source files:

- `data/demo/notices/enrollment-support-notice.md`
- `data/demo/notices/enrollment-support-notice.png`

The PNG notice is a visual sample for the video flow and carries embedded demo
OCR text so image intake is reproducible without a cloud OCR service.

Extracted facts:

- Title: `Enrollment Support Notice`
- Dates: `January 20, 2026`, `February 2, 2026`
- Deadline: `The deadline to submit enrollment documents is February 2, 2026.`
- Required documents:
  - `Birth certificate or student ID.`
  - `Guardian photo ID.`
  - `Proof of address.`
  - `Vaccination card.`
- Contact/support channel:
  - `The school office can scan documents for families who cannot upload files online.`

Action output:

- Confirm the deadline: `The deadline to submit enrollment documents is February 2, 2026.`
- Collect required document: `Birth certificate or student ID.`
- Use the listed school contact: `The school office can scan documents for families who cannot upload files online.`
- Ask the school office for in-person support if internet access fails.

Message draft:

```text
Hello, I need help with 'Enrollment Support Notice'. Can the school confirm the required steps before January 20, 2026?
```

Safety note:

```text
Generated locally from the uploaded or selected school notice.
```

## 2. Public Gemma Rewrite

Persona: `Public visitor`

Question:

```text
What documents do I need for enrollment?
```

Tool trace:

- Tool: `search_public_knowledge`
- Access policy: `public`
- Runtime: `gemma` when the public rewriter returns in time; otherwise the safe
  deterministic draft is used.
- Top retrieval result: `enrollment`
- Retrieval score: `15.37`
- Matched terms: `document`, `enrollment`, `reenrollment`

Representative answer:

```text
For enrollment, families generally need a student identification document, a guardian identification document, proof of residence issued within the last 90 days, a previous school transcript if transferring, a signed digital services consent form, and a health and emergency contact form.
```

Action output:

- Use public school documents for this guidance.
- Review the public guidance returned by the school knowledge base.
- Collect any documents, dates, or office hours mentioned in the answer.
- Use in-person support if the family cannot complete the step online.
- Keep source reference: `Enrollment And Reenrollment`.

Message draft:

```text
Hello, I need help confirming the next step for this school procedure: What documents do I need for enrollment?
```

Safety note:

```text
This output uses public school documents only.
```

## 3. Authorized Student Support

Persona: `Marina Costa, guardian of Ana Luiza`

Question:

```text
Create a recovery study plan for my child.
```

Tool trace:

- `get_student_snapshot`: allowed for `stu_ana_luiza`
- `build_study_plan`: allowed for `stu_ana_luiza`
- Access decision: `protected_allowed`
- Runtime: deterministic controlled composition.

Recovery plan:

- Review linear equations and missing algebra homework with a teacher-provided example.
- Complete one 20 minute practice block on two weekdays.
- Send one question to the school support channel before Friday.
- Ask the teacher to confirm whether the missing activity was recovered.

Message draft:

```text
Hello, this is Marina Costa, guardian of Ana Luiza. I would like to coordinate a recovery plan for Ana Luiza Costa. First proposed step: Review linear equations and missing algebra homework with a teacher-provided example.
```

Safety note:

```text
Generated from scoped synthetic protected evidence.
```

## 4. Privacy Guardrail

Persona: `Marina Costa, guardian of Ana Luiza`

Question:

```text
Can you show me another student's grades?
```

Tool trace:

- Tool: `deny_request`
- Status: `denied`
- Access decision: `restricted_denied`
- Protected evidence exposed: `0`
- Runtime: deterministic controlled denial.

Action output:

- Do not reveal protected student details.
- Ask the requester to use the correct authorized account or school channel.
- Keep the denial reason visible in the audit trace.

Message draft:

```text
Hello, I cannot process this request from the selected access scope. Please contact the school office through an authorized channel.
```

Safety note:

```text
The request asks for protected data outside the selected persona scope.
```

## Current Evaluation Snapshot

- Offline regression: `181/181`
- Public information: `60/60`
- Authorized support: `55/55`
- Privacy guardrails: `54/54`
- Document intake: `12/12`
- Restricted-data denial pass rate: `54/54`
- Denial leak failures: `0`
- Curated Gemma representative suite: `12/12`
- Local Gemma denial safety in curated suite: `3/3`, zero protected-evidence
  leaks
- Stress battery: `1131/1131` deterministic, `110/110` balanced local Gemma
  submission proof
- Local Gemma submission latency p50/p95/max: `0.01 / 0.51 / 8328.24 ms`
