from __future__ import annotations

import html
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

import streamlit as st

from eduassist_gemma_good.config import Settings, load_settings
from eduassist_gemma_good.demo_engine import DemoEngine
from eduassist_gemma_good.schema import PERSONAS, AssistantResponse


@dataclass(frozen=True)
class DemoScenario:
    label: str
    persona_key: str
    question: str
    expected: str


DEMO_SCENARIOS = {
    "public_enrollment": DemoScenario(
        label="Public enrollment question",
        persona_key="public",
        question="What documents do I need for enrollment?",
        expected="Public answer grounded in school documents",
    ),
    "guardian_plan": DemoScenario(
        label="Authorized recovery plan",
        persona_key="guardian_ana",
        question="Create a recovery study plan for my child.",
        expected="Protected support answer for Ana Luiza only",
    ),
    "safe_denial": DemoScenario(
        label="Restricted data denial",
        persona_key="guardian_ana",
        question="Can you show me another student's grades?",
        expected="Safe denial without exposing protected records",
    ),
    "manual": DemoScenario(
        label="Manual question",
        persona_key="guardian_ana",
        question="How is Ana Luiza doing in math and attendance?",
        expected="Custom exploration with the selected persona",
    ),
}


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
            padding-top: 2rem;
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
        tool_name = escape_html(result.call.name)
        tool_status = escape_html(result.status)
        proposed_by = escape_html(result.call.proposed_by)
        arguments = escape_html(json.dumps(result.call.arguments, ensure_ascii=False))
        st.markdown(
            f"""
            <div class="ea-band">
                <strong>{tool_name}</strong><br />
                <span class="ea-pill {band_class}">status: {tool_status}</span>
                <span class="ea-pill">planned by: {proposed_by}</span>
                <span class="ea-pill">arguments: {arguments}</span>
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


def main() -> None:
    st.set_page_config(page_title="EduAssist Local", page_icon="EA", layout="wide")
    install_theme()
    settings = load_settings()

    st.title("EduAssist Local")
    st.markdown(
        '<p class="ea-caption">Gemma 4 local-first school assistance demo</p>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Runtime")
        use_llm = st.toggle("Use local Gemma", value=True)
        render_runtime(settings, use_llm)
        st.caption(settings.gemma_base_url)
        st.caption(settings.gemma_model)

    engine = DemoEngine(settings, use_llm=use_llm)

    scenario_key = st.selectbox(
        "Demo scenario",
        options=list(DEMO_SCENARIOS),
        format_func=lambda key: DEMO_SCENARIOS[key].label,
        index=0,
    )
    scenario = DEMO_SCENARIOS[scenario_key]

    persona_key = st.selectbox(
        "Persona",
        options=list(PERSONAS),
        format_func=lambda key: PERSONAS[key].label,
        index=list(PERSONAS).index(scenario.persona_key),
    )

    st.markdown(
        f"""
        <div class="ea-band">
            <strong>Expected outcome</strong><br />
            {escape_html(scenario.expected)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.subheader("Question")
        question = st.text_area("Ask", value=scenario.question, height=145)
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

        render_trace(response)


if __name__ == "__main__":
    main()
