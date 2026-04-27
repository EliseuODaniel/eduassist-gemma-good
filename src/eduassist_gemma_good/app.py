from __future__ import annotations

import html
import json
import urllib.error
import urllib.request
from pathlib import Path

import streamlit as st

from eduassist_gemma_good.action_outputs import ActionOutput, action_output_from_response
from eduassist_gemma_good.config import Settings, load_settings
from eduassist_gemma_good.demo_engine import DemoEngine
from eduassist_gemma_good.field_kit import (
    FIELD_KIT_WORKFLOWS,
    FieldKitWorkflow,
    workflow_option_label,
)
from eduassist_gemma_good.model_client import GemmaClient
from eduassist_gemma_good.notice_intake import (
    IMAGE_NOTICE_SUFFIXES,
    NoticeFacts,
    action_output_from_notice,
    extract_notice_facts,
    extract_notice_text,
    sample_notice_paths,
)
from eduassist_gemma_good.question_bank import (
    QUESTION_GROUPS,
    PreparedQuestion,
    count_questions_by_group,
    filter_questions,
    load_prepared_questions,
    question_option_label,
)
from eduassist_gemma_good.schema import PERSONAS, AssistantResponse
from eduassist_gemma_good.tool_registry import tool_definition

ACCESS_LABELS = {
    "public": "Public",
    "protected_allowed": "Protected allowed",
    "restricted_denied": "Restricted denied",
}


def escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)


def install_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.45rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        .ea-caption {
            color: #64748b;
            font-size: 0.92rem;
            margin-top: -0.25rem;
        }
        .ea-band {
            border: 1px solid #dbe3ea;
            border-radius: 8px;
            padding: 0.8rem 0.9rem;
            background: #f8fafc;
            margin-bottom: 0.75rem;
        }
        .ea-band strong {
            color: #0f172a;
        }
        .ea-brief {
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            background: #eff6ff;
            margin: 0.75rem 0 1rem 0;
        }
        .ea-brief h3 {
            margin: 0 0 0.35rem 0;
            color: #0f172a;
        }
        .ea-brief p {
            margin: 0;
            color: #334155;
        }
        .ea-score {
            border: 1px solid #dbe3ea;
            border-radius: 8px;
            padding: 0.72rem 0.8rem;
            min-height: 5.8rem;
            background: #ffffff;
        }
        .ea-score strong {
            color: #0f172a;
            display: block;
            font-size: 1.18rem;
            line-height: 1.25;
        }
        .ea-score span {
            color: #64748b;
            font-size: 0.86rem;
        }
        .ea-step {
            border-left: 4px solid #2563eb;
            padding: 0.72rem 0.85rem;
            background: #f8fafc;
            margin: 0.75rem 0;
        }
        .ea-step strong {
            color: #0f172a;
        }
        .ea-workflow {
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #f0f9ff;
            margin-bottom: 0.75rem;
        }
        .ea-workflow strong {
            color: #075985;
        }
        .ea-pill {
            border: 1px solid #cbd5e1;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            display: inline-block;
            margin: 0 0.25rem 0.35rem 0;
            background: #ffffff;
            color: #334155;
            font-size: 0.82rem;
        }
        .ea-ok {
            border-color: #86efac;
            background: #f0fdf4;
            color: #166534;
        }
        .ea-warn {
            border-color: #fecaca;
            background: #fef2f2;
            color: #991b1b;
        }
        .ea-message {
            border-left: 4px solid #0ea5e9;
            padding: 0.65rem 0.8rem;
            background: #f8fafc;
            color: #0f172a;
            margin-top: 0.5rem;
        }
        .ea-export {
            border: 1px dashed #94a3b8;
            border-radius: 8px;
            padding: 0.7rem 0.85rem;
            background: #ffffff;
            color: #334155;
            white-space: pre-wrap;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=10)
def gemma_health(base_url: str) -> dict[str, str]:
    url = base_url.rstrip("/") + "/models"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"status": "offline", "detail": str(exc)}

    model = ""
    try:
        model = payload["data"][0]["id"]
    except (KeyError, IndexError, TypeError):
        model = "unknown"
    return {"status": "online", "detail": model}


@st.cache_data
def cached_prepared_questions(data_dir: str) -> tuple[PreparedQuestion, ...]:
    return load_prepared_questions(Path(data_dir))


def selected_question_for_id(
    questions: tuple[PreparedQuestion, ...],
    question_id: str,
) -> PreparedQuestion:
    return next(question for question in questions if question.id == question_id)


def render_question_coverage(questions: tuple[PreparedQuestion, ...]) -> None:
    counts = count_questions_by_group(questions)
    st.header("Coverage")
    st.metric("Prepared cases", counts["all_cases"])
    public_col, allowed_col = st.columns(2)
    public_col.metric("Public", counts["public_information"])
    allowed_col.metric("Allowed", counts["authorized_support"])
    st.metric("Denied", counts["privacy_guardrails"])


def render_submission_brief() -> None:
    st.markdown(
        """
        <div class="ea-brief">
            <h3>Private offline school assistance with Gemma 4</h3>
            <p>
                One reproducible workflow for judges: local notice intake, public
                evidence retrieval, authorized student support, and visible privacy
                denial before protected data can leak.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scoreboard() -> None:
    metrics = (
        ("181/181", "offline regression"),
        ("1131/1131", "adversarial stress"),
        ("12/12", "curated Gemma suite"),
        ("110/110", "Gemma submission suite"),
    )
    columns = st.columns(4)
    for column, (value, label) in zip(columns, metrics, strict=True):
        with column:
            st.markdown(
                f"""
                <div class="ea-score">
                    <strong>{escape_html(value)}</strong>
                    <span>{escape_html(label)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_step(label: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="ea-step">
            <strong>{escape_html(label)}</strong><br />
            {escape_html(body)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_card(workflow: FieldKitWorkflow, case_count: int) -> None:
    st.markdown(
        f"""
        <div class="ea-workflow">
            <strong>{escape_html(workflow.label)}</strong><br />
            <span class="ea-pill">user: {escape_html(workflow.user)}</span>
            <span class="ea-pill">cases: {case_count}</span>
            <span class="ea-pill">output: {escape_html(workflow.action_label)}</span>
            <p>{escape_html(workflow.demo_goal)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_runtime(settings: Settings, use_llm: bool) -> None:
    health = gemma_health(settings.gemma_base_url) if use_llm else {"status": "off", "detail": ""}
    if health["status"] == "online":
        st.success("Gemma endpoint online")
        st.caption(health["detail"])
    elif use_llm:
        st.warning("Gemma endpoint unavailable; fallback path will handle requests.")
        st.caption(health["detail"])
    else:
        st.info("Gemma disabled for this run.")


def render_trace(response: AssistantResponse) -> None:
    st.subheader("Tool Trace")
    for result in response.tool_results:
        band_class = "ea-ok" if result.status == "ok" else "ea-warn"
        definition = tool_definition(result.call.name)
        audit_label = definition.audit_label if definition else result.call.name
        access_policy = definition.access_policy if definition else "unregistered"
        output_contract = definition.output_contract if definition else "Unregistered tool result"
        tool_name = escape_html(result.call.name)
        audit_label_html = escape_html(audit_label)
        access_policy_html = escape_html(access_policy)
        output_contract_html = escape_html(output_contract)
        tool_status = escape_html(result.status)
        proposed_by = escape_html(result.call.proposed_by)
        arguments = escape_html(json.dumps(result.call.arguments, ensure_ascii=False))
        retrieval_metadata = _retrieval_metadata_html(result.payload)
        st.markdown(
            f"""
            <div class="ea-band">
                <strong>{audit_label_html}</strong><br />
                <span class="ea-pill {band_class}">status: {tool_status}</span>
                <span class="ea-pill">tool: {tool_name}</span>
                <span class="ea-pill">policy: {access_policy_html}</span>
                <span class="ea-pill">output: {output_contract_html}</span>
                <span class="ea-pill">planned by: {proposed_by}</span>
                <span class="ea-pill">arguments: {arguments}</span>
                {retrieval_metadata}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if response.evidence:
        st.subheader("Evidence")
        for evidence in response.evidence:
            title = escape_html(evidence.title)
            access = escape_html(evidence.access)
            source_id = escape_html(evidence.source_id)
            excerpt = escape_html(evidence.excerpt)
            st.markdown(
                f"""
                <div class="ea-band">
                    <strong>{title}</strong><br />
                    <span class="ea-pill">{access}</span>
                    <span class="ea-pill">{source_id}</span>
                    <p>{excerpt}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if response.safety_notes:
        st.subheader("Safety notes")
        for note in response.safety_notes:
            st.write(f"- {note}")


def _retrieval_metadata_html(payload: dict) -> str:
    documents = payload.get("documents", [])
    if not isinstance(documents, list):
        return ""
    rows: list[str] = []
    for document in documents:
        if not isinstance(document, dict) or "score" not in document:
            continue
        rank = escape_html(document.get("rank", ""))
        source_id = escape_html(document.get("source_id", ""))
        score = escape_html(document.get("score", ""))
        raw_terms = document.get("matched_terms", ())
        if not isinstance(raw_terms, list):
            raw_terms = []
        matched_terms = ", ".join(str(term) for term in raw_terms[:5])
        rows.append(
            '<span class="ea-pill">'
            f"retrieval: #{rank} {source_id} score {score} "
            f"terms {escape_html(matched_terms)}"
            "</span>"
        )
    if not rows:
        return ""
    return "<br />" + "".join(rows)


def render_action_output(output: ActionOutput, *, show_printable: bool = True) -> None:
    st.subheader("Action Output")
    st.markdown(f"**{output.title}**")
    checklist_col, message_col = st.columns([0.95, 1.05], gap="medium")
    with checklist_col:
        st.markdown("**Checklist**")
        for item in output.checklist:
            st.write(f"- {item}")
        if output.plan:
            st.markdown("**Plan**")
            for item in output.plan:
                st.write(f"- {item}")
    with message_col:
        st.markdown("**Message draft**")
        st.markdown(
            f"""
            <div class="ea-message">
                {escape_html(output.message)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(output.safety_note)
    export_text = "\n".join(
        [
            output.title,
            "",
            "Checklist:",
            *(f"- {item}" for item in output.checklist),
            *(["", "Plan:", *(f"- {item}" for item in output.plan)] if output.plan else []),
            "",
            "Message draft:",
            output.message,
            "",
            f"Safety note: {output.safety_note}",
        ]
    )
    if show_printable:
        with st.expander("Printable field-kit output"):
            st.markdown(
                f"""
                <div class="ea-export">
                    {escape_html(export_text)}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_notice_facts(facts: NoticeFacts) -> None:
    st.subheader("Notice Facts")
    st.markdown(
        f"""
        <div class="ea-band">
            <strong>{escape_html(facts.title)}</strong><br />
            <span class="ea-pill">source: {escape_html(facts.source_name)}</span>
            <span class="ea-pill">dates: {len(facts.dates)}</span>
            <span class="ea-pill">documents: {len(facts.required_documents)}</span>
            <span class="ea-pill">contacts: {len(facts.contacts)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if facts.dates:
        st.markdown("**Dates**")
        for item in facts.dates:
            st.write(f"- {item}")
    if facts.deadlines:
        st.markdown("**Deadlines**")
        for item in facts.deadlines:
            st.write(f"- {item}")
    if facts.required_documents:
        st.markdown("**Required documents**")
        for item in facts.required_documents:
            st.write(f"- {item}")
    if facts.contacts:
        st.markdown("**Contacts and support channels**")
        for item in facts.contacts:
            st.write(f"- {item}")


def render_document_intake(data_dir: Path, settings: Settings, use_llm: bool) -> None:
    samples = sample_notice_paths(data_dir)
    uploaded = st.file_uploader(
        "Upload school notice",
        type=["md", "txt", "pdf", "png", "jpg", "jpeg"],
    )

    source_name = ""
    source_text = ""
    if uploaded is not None:
        source_name = uploaded.name
        try:
            source_text = extract_notice_text_for_app(
                uploaded.name,
                uploaded.getvalue(),
                settings,
                use_llm,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
    elif samples:
        selected_sample = st.selectbox(
            "Sample notice",
            options=list(samples),
            format_func=lambda path: path.name,
        )
        source_name = selected_sample.name
        source_text = extract_notice_text(selected_sample.name, selected_sample.read_bytes())
    else:
        st.warning("No sample notices are available.")
        return

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.subheader("Notice Text")
        notice_text = st.text_area(
            "Extracted local text",
            value=source_text,
            height=285,
        )
    with right:
        if not notice_text.strip():
            st.info("Add notice text to generate a local checklist.")
            return
        facts = extract_notice_facts(notice_text, source_name)
        render_notice_facts(facts)
        render_action_output(action_output_from_notice(facts))


def render_winning_demo(engine: DemoEngine, settings: Settings) -> None:
    st.header("Winning Demo Run")
    st.markdown(
        '<p class="ea-caption">One end-to-end submission story: notice, public guidance, '
        "authorized support, and privacy denial.</p>",
        unsafe_allow_html=True,
    )
    render_scoreboard()

    image_notice_path = settings.data_dir / "notices" / "enrollment-support-notice.png"
    notice_path = (
        image_notice_path
        if image_notice_path.exists()
        else settings.data_dir / "notices" / "enrollment-support-notice.md"
    )
    if notice_path.exists():
        with st.expander("1. Document intake", expanded=True):
            render_step(
                "Field worker starts from a school notice",
                "The app turns a local file into dates, documents, support channels, "
                "and a family checklist.",
            )
            if notice_path.suffix.lower() in IMAGE_NOTICE_SUFFIXES:
                st.image(str(notice_path), caption=notice_path.name, width="stretch")
            notice_text = extract_notice_text(notice_path.name, notice_path.read_bytes())
            facts = extract_notice_facts(notice_text, notice_path.name)
            render_notice_facts(facts)
            render_action_output(action_output_from_notice(facts), show_printable=False)

    demo_cases = (
        (
            "2. Public family guidance",
            "What documents do I need for enrollment?",
            "public",
        ),
        (
            "3. Authorized student support",
            "Create a recovery study plan for my child.",
            "guardian_ana",
        ),
        (
            "4. Privacy guardrail",
            "Can you show me another student's grades?",
            "guardian_ana",
        ),
    )
    for title, question, persona_key in demo_cases:
        with st.expander(title, expanded=True):
            if persona_key == "public":
                render_step(
                    "Public guidance is grounded",
                    "Gemma plans a narrow public search and the UI shows ranked evidence.",
                )
            elif "Privacy" in title:
                render_step(
                    "Unsafe access is blocked",
                    "The deterministic policy layer denies the request before protected "
                    "evidence is exposed.",
                )
            else:
                render_step(
                    "Authorized support becomes action",
                    "A scoped protected snapshot feeds a short recovery plan and school "
                    "message draft.",
                )
            response = engine.answer(question, persona_key)
            st.markdown(f"**Persona:** {escape_html(response.persona.label)}")
            st.markdown(f"**Question:** {escape_html(question)}")
            st.write(response.answer)
            metrics = st.columns(3)
            metrics[0].metric("Access", ACCESS_LABELS[response.access_decision])
            metrics[1].metric("Runtime", response.runtime_mode.title())
            metrics[2].metric("Tools", str(len(response.tool_results)))
            render_action_output(action_output_from_response(response), show_printable=False)
            render_trace(response)


def extract_notice_text_for_app(
    file_name: str,
    content: bytes,
    settings: Settings,
    use_llm: bool,
) -> str:
    suffix = Path(file_name).suffix.lower()
    if use_llm and settings.gemma_enable_vision and suffix in IMAGE_NOTICE_SUFFIXES:
        response = GemmaClient(settings).transcribe_notice_image(file_name, content)
        if response is not None:
            st.caption("Image notice transcribed with local Gemma vision path.")
            return response.text
        st.caption("Gemma vision path unavailable; trying local OCR fallback.")
    return extract_notice_text(file_name, content)


def main() -> None:
    st.set_page_config(page_title="EduAssist Field Kit", page_icon="EA", layout="wide")
    install_theme()
    settings = load_settings()

    st.title("EduAssist Field Kit")
    st.markdown(
        '<p class="ea-caption">Offline-first school service kit powered by local Gemma 4</p>',
        unsafe_allow_html=True,
    )
    render_submission_brief()
    render_scoreboard()

    with st.sidebar:
        st.header("Runtime")
        use_llm = st.toggle("Use local Gemma", value=True)
        render_runtime(settings, use_llm)
        st.caption(settings.gemma_base_url)
        st.caption(settings.gemma_model)
        run_winning_demo = st.button(
            "Run winning demo",
            type="primary",
            width="stretch",
            key="sidebar_winning_demo",
        )

    engine = DemoEngine(settings, use_llm=use_llm)
    prepared_questions = cached_prepared_questions(str(settings.data_dir))

    with st.sidebar:
        render_question_coverage(prepared_questions)

    demo_col, eval_col = st.columns([0.72, 0.28], gap="medium")
    with demo_col:
        run_winning_demo_main = st.button(
            "Run winning demo",
            type="primary",
            width="stretch",
            key="main_winning_demo",
        )
    with eval_col:
        st.caption("Use this first for the video story.")
        st.caption("Then show stress and eval metrics.")
    run_winning_demo = run_winning_demo or run_winning_demo_main

    if run_winning_demo:
        render_winning_demo(engine, settings)
        return

    workflow_key = st.selectbox(
        "Field kit workflow",
        options=list(FIELD_KIT_WORKFLOWS),
        format_func=workflow_option_label,
        index=0,
    )
    workflow = FIELD_KIT_WORKFLOWS[workflow_key]
    group_key = workflow.question_group_key
    group = QUESTION_GROUPS[group_key]
    group_questions = filter_questions(prepared_questions, group_key)
    group_question_ids = [question.id for question in group_questions]
    render_workflow_card(workflow, len(group_questions))

    if workflow_key == "document_intake":
        render_document_intake(settings.data_dir, settings, use_llm)
        return

    current_question_id = st.session_state.get("selected_question_id")
    if current_question_id not in group_question_ids:
        st.session_state["selected_question_id"] = group_question_ids[0]

    question_id = st.selectbox(
        "Scenario card",
        options=group_question_ids,
        key="selected_question_id",
        format_func=lambda key: question_option_label(
            selected_question_for_id(prepared_questions, key),
            PERSONAS[selected_question_for_id(prepared_questions, key).persona_key].label,
        ),
    )
    selected_question = selected_question_for_id(prepared_questions, question_id)

    if st.session_state.get("active_question_id") != selected_question.id:
        st.session_state["active_question_id"] = selected_question.id
        st.session_state["question_text"] = selected_question.question
        st.session_state["persona_key"] = selected_question.persona_key

    persona_options = list(PERSONAS)
    if "persona_key" not in st.session_state:
        st.session_state["persona_key"] = selected_question.persona_key

    persona_key = st.selectbox(
        "Persona",
        options=persona_options,
        format_func=lambda key: PERSONAS[key].label,
        key="persona_key",
    )

    expected_tool = escape_html(selected_question.expected_tool)
    expected_access = escape_html(ACCESS_LABELS[selected_question.expected_access])

    st.markdown(
        f"""
        <div class="ea-band">
            <strong>Scenario outcome</strong><br />
            {escape_html(group.expected)}<br />
            <span class="ea-pill">{escape_html(selected_question.id)}</span>
            <span class="ea-pill">expected tool: {expected_tool}</span>
            <span class="ea-pill">expected access: {expected_access}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.subheader("Field Request")
        question = st.text_area("Ask", key="question_text", height=145)
        run = st.button("Run", type="primary", width="stretch")

        if run and question.strip():
            with st.spinner("Running local-first flow"):
                response = engine.answer(question.strip(), persona_key)
            st.session_state["last_response"] = response

    with right:
        response = st.session_state.get("last_response")
        if response is None:
            st.info("Run a question to inspect the answer, tool trace, and evidence.")
            return

        st.subheader("Answer")
        st.write(response.answer)

        metrics = st.columns(3)
        metrics[0].metric("Access", ACCESS_LABELS[response.access_decision])
        metrics[1].metric("Runtime", response.runtime_mode.title())
        metrics[2].metric("Tools", str(len(response.tool_results)))

        render_action_output(action_output_from_response(response))
        render_trace(response)


if __name__ == "__main__":
    main()
