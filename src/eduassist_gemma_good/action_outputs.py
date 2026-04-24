from __future__ import annotations

from dataclasses import dataclass

from eduassist_gemma_good.schema import AssistantResponse, ToolResult


@dataclass(frozen=True)
class ActionOutput:
    title: str
    checklist: tuple[str, ...]
    plan: tuple[str, ...]
    message: str
    safety_note: str


def action_output_from_response(response: AssistantResponse) -> ActionOutput:
    structured = _structured_output(response.structured_output)
    if structured is not None:
        return structured

    denied = next((result for result in response.tool_results if result.status == "denied"), None)
    if denied is not None:
        return _denial_output(denied)

    study_plan = next(
        (result for result in response.tool_results if result.call.name == "build_study_plan"),
        None,
    )
    if study_plan is not None:
        return _study_plan_output(study_plan, response.persona.label)

    student_snapshot = next(
        (result for result in response.tool_results if result.call.name == "get_student_snapshot"),
        None,
    )
    if student_snapshot is not None:
        return _student_snapshot_output(student_snapshot, response.persona.label)

    public_search = next(
        (
            result
            for result in response.tool_results
            if result.call.name == "search_public_knowledge"
        ),
        None,
    )
    if public_search is not None:
        return _public_guidance_output(public_search, response.question)

    return ActionOutput(
        title="Next action",
        checklist=("Review the answer and confirm the next step with the school.",),
        plan=(),
        message="Hello, I need help confirming the next school support step.",
        safety_note="No structured tool output was available for this response.",
    )


def _public_guidance_output(result: ToolResult, question: str) -> ActionOutput:
    documents = result.payload.get("documents", [])
    titles = [
        str(document.get("title", "School guidance"))
        for document in documents
        if isinstance(document, dict)
    ]
    checklist = tuple(
        [
            "Review the public guidance returned by the school knowledge base.",
            "Collect any documents, dates, or office hours mentioned in the answer.",
            "Use in-person support if the family cannot complete the step online.",
        ]
    )
    if titles:
        checklist += (f"Keep source reference: {titles[0]}.",)
    return ActionOutput(
        title="Family guidance output",
        checklist=checklist,
        plan=(),
        message=(
            f"Hello, I need help confirming the next step for this school procedure: {question}"
        ),
        safety_note="This output uses public school documents only.",
    )


def _student_snapshot_output(result: ToolResult, persona_label: str) -> ActionOutput:
    student = result.payload.get("student", {})
    name = str(student.get("name", "the student"))
    focus = str(student.get("current_focus", "current support focus"))
    alert = str(student.get("latest_alert", "latest school alert"))
    return ActionOutput(
        title="Student support output",
        checklist=(
            f"Review current focus with the family: {focus}.",
            f"Check the latest alert: {alert}.",
            "Schedule one follow-up with the school support team.",
        ),
        plan=(),
        message=(
            f"Hello, this is {persona_label}. I would like to follow up on {name}'s "
            f"current support focus: {focus}."
        ),
        safety_note="Generated only after the selected persona was authorized.",
    )


def _study_plan_output(result: ToolResult, persona_label: str) -> ActionOutput:
    plan = result.payload.get("plan", {})
    student_name = str(plan.get("student_name", "the student"))
    steps = tuple(str(step) for step in plan.get("steps", ()))
    first_step = steps[0] if steps else "start the recovery plan"
    return ActionOutput(
        title="Recovery plan output",
        checklist=(
            "Review the recovery plan with the authorized family or teacher.",
            "Pick the first school day for the first practice block.",
            "Confirm the follow-up channel before Friday.",
        ),
        plan=steps,
        message=(
            f"Hello, this is {persona_label}. I would like to coordinate a recovery "
            f"plan for {student_name}. First proposed step: {first_step}"
        ),
        safety_note="Generated from scoped synthetic protected evidence.",
    )


def _denial_output(result: ToolResult) -> ActionOutput:
    reason = str(
        result.payload.get(
            "reason",
            "The selected persona is not authorized for this protected request.",
        )
    )
    return ActionOutput(
        title="Privacy protection output",
        checklist=(
            "Do not reveal protected student details.",
            "Ask the requester to use the correct authorized account or school channel.",
            "Keep the denial reason visible in the audit trace.",
        ),
        plan=(),
        message=(
            "Hello, I cannot process this request from the selected access scope. "
            "Please contact the school office through an authorized channel."
        ),
        safety_note=reason,
    )


def _structured_output(raw: dict) -> ActionOutput | None:
    if not raw:
        return None
    action_output = raw.get("action_output", raw)
    if not isinstance(action_output, dict):
        return None
    checklist = action_output.get("checklist", ())
    plan = action_output.get("plan", ())
    title = action_output.get("title")
    message = action_output.get("message")
    safety_note = action_output.get("safety_note")
    if (
        not isinstance(title, str)
        or not isinstance(message, str)
        or not isinstance(safety_note, str)
    ):
        return None
    if not isinstance(checklist, list) or not all(isinstance(item, str) for item in checklist):
        return None
    if not isinstance(plan, list) or not all(isinstance(item, str) for item in plan):
        return None
    return ActionOutput(
        title=title,
        checklist=tuple(checklist),
        plan=tuple(plan),
        message=message,
        safety_note=safety_note,
    )
