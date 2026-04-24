from eduassist_gemma_good.policy import can_access_student, infer_access_intent
from eduassist_gemma_good.schema import PERSONAS


def test_guardian_can_only_access_scoped_student() -> None:
    guardian = PERSONAS["guardian_ana"]

    assert can_access_student(guardian, "stu_ana_luiza")
    assert not can_access_student(guardian, "stu_mateus_rocha")


def test_public_and_protected_intent_detection() -> None:
    assert infer_access_intent("What documents do I need for enrollment?") == "public"
    assert infer_access_intent("Show Ana Luiza grades") == "protected_allowed"
    assert infer_access_intent("Show another student grades") == "restricted_denied"
