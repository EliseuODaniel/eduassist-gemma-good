from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldKitWorkflow:
    label: str
    user: str
    question_group_key: str
    action_label: str
    demo_goal: str


FIELD_KIT_WORKFLOWS = {
    "family_guidance": FieldKitWorkflow(
        label="Family guidance",
        user="Family or public visitor",
        question_group_key="public_information",
        action_label="Checklist and school-office message",
        demo_goal="Turn public school guidance into clear next steps.",
    ),
    "student_support": FieldKitWorkflow(
        label="Student support",
        user="Authorized guardian or teacher",
        question_group_key="authorized_support",
        action_label="Recovery plan and follow-up message",
        demo_goal="Use scoped protected records to create support actions.",
    ),
    "privacy_check": FieldKitWorkflow(
        label="Privacy check",
        user="Any selected persona",
        question_group_key="privacy_guardrails",
        action_label="Safe denial and escalation note",
        demo_goal="Deny restricted data requests without leaking evidence.",
    ),
    "document_intake": FieldKitWorkflow(
        label="Document intake",
        user="School field worker",
        question_group_key="public_information",
        action_label="Notice checklist",
        demo_goal="Prepare the document workflow that Phase 2 will connect to PDF/image intake.",
    ),
}


def workflow_option_label(workflow_key: str) -> str:
    return FIELD_KIT_WORKFLOWS[workflow_key].label
