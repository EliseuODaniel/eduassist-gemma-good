from eduassist_gemma_good.field_kit import FIELD_KIT_WORKFLOWS
from eduassist_gemma_good.question_bank import QUESTION_GROUPS


def test_field_kit_workflows_have_backed_question_groups() -> None:
    assert set(FIELD_KIT_WORKFLOWS) == {
        "document_intake",
        "family_guidance",
        "privacy_check",
        "student_support",
    }

    for workflow in FIELD_KIT_WORKFLOWS.values():
        assert workflow.question_group_key in QUESTION_GROUPS
        assert workflow.action_label
        assert workflow.demo_goal
