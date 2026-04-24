from __future__ import annotations

import json

import streamlit as st

from eduassist_gemma_good.config import load_settings
from eduassist_gemma_good.demo_engine import DemoEngine
from eduassist_gemma_good.schema import PERSONAS, AssistantResponse

SAMPLE_QUESTIONS = [
    "When is the recovery exam week?",
    "What documents do I need for enrollment?",
    "How is Ana Luiza doing in math and attendance?",
    "Create a recovery study plan for my child.",
    "Can you show me another student's grades?",
]


def render_trace(response: AssistantResponse) -> None:
    st.subheader("Trace")
    rows = []
    for result in response.tool_results:
        rows.append(
            {
                "tool": result.call.name,
                "status": result.status,
                "proposed_by": result.call.proposed_by,
                "arguments": json.dumps(result.call.arguments, ensure_ascii=False),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if response.evidence:
        st.subheader("Evidence")
        for evidence in response.evidence:
            st.markdown(f"**{evidence.title}**  \n`{evidence.access}` | `{evidence.source_id}`")
            st.write(evidence.excerpt)

    if response.safety_notes:
        st.subheader("Safety notes")
        for note in response.safety_notes:
            st.write(f"- {note}")


def main() -> None:
    st.set_page_config(page_title="EduAssist Local", page_icon="EA", layout="wide")
    settings = load_settings()

    st.title("EduAssist Local")
    st.caption("Gemma 4 local-first school assistance demo")

    with st.sidebar:
        st.header("Runtime")
        persona_key = st.selectbox(
            "Persona",
            options=list(PERSONAS),
            format_func=lambda key: PERSONAS[key].label,
            index=1,
        )
        use_llm = st.toggle("Use local Gemma", value=True)
        st.text_input("Gemma endpoint", value=settings.gemma_base_url, disabled=True)
        st.text_input("Gemma model", value=settings.gemma_model, disabled=True)

    engine = DemoEngine(settings, use_llm=use_llm)

    left, right = st.columns([1.2, 0.8], gap="large")

    with left:
        st.subheader("Question")
        selected = st.radio(
            "Samples",
            SAMPLE_QUESTIONS,
            horizontal=False,
            label_visibility="collapsed",
        )
        question = st.text_area("Ask", value=selected, height=130)
        run = st.button("Run", type="primary", use_container_width=True)

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
        metrics[0].metric("Access", response.access_decision)
        metrics[1].metric("Runtime", response.runtime_mode)
        metrics[2].metric("Tools", str(len(response.tool_results)))

        render_trace(response)


if __name__ == "__main__":
    main()
