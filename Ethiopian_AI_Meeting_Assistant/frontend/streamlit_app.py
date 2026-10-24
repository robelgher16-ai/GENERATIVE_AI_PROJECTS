
"""
Ethiopian AI Meeting Assistant — Streamlit Frontend

Local:
    streamlit run frontend/streamlit_app.py

Streamlit Cloud secrets:
    API_URL = "https://ethiopian-ai-meeting-assistant-api.onrender.com"
    APP_API_KEY = "your_app_api_key"
"""

import os
import time

import requests
import streamlit as st


# --------------------------------------------------
# Configuration
# --------------------------------------------------

def _secret(name, default=""):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


API_URL = _secret(
    "API_URL",
    "http://localhost:8000",
).rstrip("/")

APP_API_KEY = _secret("APP_API_KEY")

HEADERS = (
    {"X-API-Key": APP_API_KEY}
    if APP_API_KEY
    else {}
)

st.set_page_config(
    page_title="Ethiopian AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
)

st.markdown(
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;600&display=swap');"
    "html,body,[class*='css']{font-family:'Noto Sans Ethiopic',sans-serif}"
    "</style>",
    unsafe_allow_html=True,
)

st.title("🎙️ Ethiopian AI Meeting Assistant")
st.caption(
    "Meeting audio/video → English + አማርኛ reports → chat with the meeting"
)


# --------------------------------------------------
# Backend request helper
# --------------------------------------------------

def api(method, path, **kwargs):
    timeout = kwargs.pop("timeout", 120)

    return requests.request(
        method,
        f"{API_URL}{path}",
        headers=HEADERS,
        timeout=timeout,
        **kwargs,
    )


# --------------------------------------------------
# Sidebar: backend status
# --------------------------------------------------

with st.sidebar:
    st.header("Backend")

    try:
        response = api("GET", "/health", timeout=60)
        response.raise_for_status()
        health = response.json()

        st.success("API online")

        st.write(
            "Gemini key:",
            "✅" if health.get("gemini_key_set") else "❌",
        )

        st.write(
            "Busy:",
            "⏳ yes" if health.get("busy") else "no",
        )

        st.write(
            "Knowledge base:",
            "✅" if health.get("knowledge_base_ready") else "○ not built",
        )

    except Exception as exc:
        st.error(f"Cannot reach API at {API_URL}")
        st.caption(str(exc)[:200])
        st.stop()


# --------------------------------------------------
# Main tabs
# --------------------------------------------------

tab_run, tab_en, tab_am, tab_chat = st.tabs(
    [
        "🚀 Analyze",
        "🇬🇧 English Report",
        "🇪🇹 የአማርኛ ሪፖርት",
        "💬 Chat / ውይይት",
    ]
)


# --------------------------------------------------
# Analyze: upload file only
# YouTube link processing is intentionally disabled.
# --------------------------------------------------

with tab_run:
    mode = st.radio(
        "Input",
        ["Upload file", "YouTube / video link"],
        index=0,
        horizontal=True,
        key="input_mode",
    )

    if mode == "YouTube / video link":
        st.info(
            "YouTube link processing is temporarily disabled due to "
            "YouTube access restrictions. Please upload your meeting "
            "audio or video file instead."
        )

    else:
        skip_visual = st.checkbox(
            "Skip slide-text (OCR) step — faster",
            value=False,
            key="skip_visual_ocr",
        )

        uploaded_file = st.file_uploader(
            "Meeting file",
            type=[
                "mp4",
                "mov",
                "mkv",
                "avi",
                "webm",
                "mp3",
                "wav",
                "m4a",
            ],
            key="meeting_file_uploader",
        )

        if st.button("Start analysis", type="primary", key="start_upload_analysis"):
            if uploaded_file is None:
                st.warning("Please upload a meeting audio or video file first.")

            else:
                try:
                    with st.spinner("Submitting your file..."):
                        response = api(
                            "POST",
                            "/analyze/upload",
                            files={
                                "file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                )
                            },
                            data={
                                "skip_visual": str(skip_visual).lower()
                            },
                            timeout=600,
                        )

                    if not response.ok:
                        st.error(
                            f"Could not start analysis "
                            f"({response.status_code}): {response.text[:1000]}"
                        )

                    else:
                        job = response.json()
                        job_id = job.get("job_id")

                        if not job_id:
                            st.error(
                                "The API response did not contain a job ID."
                            )

                        else:
                            status_box = st.empty()

                            while True:
                                try:
                                    job_response = api(
                                        "GET",
                                        f"/jobs/{job_id}",
                                        timeout=120,
                                    )
                                    job_response.raise_for_status()
                                    job_status = job_response.json()

                                except requests.RequestException as exc:
                                    status_box.error(
                                        f"Could not check analysis progress: {exc}"
                                    )
                                    break

                                status = job_status.get("status", "unknown")
                                step = job_status.get("step", "Processing")

                                status_box.info(
                                    f"**{status}** — {step}"
                                )

                                if status == "done":
                                    status_box.success(
                                        "Analysis finished! Open the English "
                                        "Report and Amharic Report tabs."
                                    )
                                    break

                                if status == "failed":
                                    status_box.error(
                                        job_status.get(
                                            "error",
                                            "Analysis failed. Please check the backend logs.",
                                        )
                                    )
                                    break

                                time.sleep(8)

                except requests.RequestException as exc:
                    st.error(f"Request failed: {exc}")


# --------------------------------------------------
# Report display
# --------------------------------------------------

def show_report(path):
    try:
        response = api("GET", path, timeout=120)

        if response.ok:
            report_data = response.json()
            markdown_report = report_data.get("markdown", "")

            if not markdown_report:
                st.info("The report is empty.")
                return

            st.download_button(
                "⬇️ Download (.md)",
                data=markdown_report,
                file_name=f"{path.split('/')[-1]}.md",
                mime="text/markdown",
                key=f"download_{path.replace('/', '_')}",
            )

            st.markdown(markdown_report)

        else:
            st.info(
                "No report available yet. Run an analysis first."
            )

    except requests.RequestException as exc:
        st.error(f"Could not load the report: {exc}")


with tab_en:
    show_report("/reports/en")

with tab_am:
    show_report("/reports/amh")


# --------------------------------------------------
# Chat in English or Amharic
# --------------------------------------------------

with tab_chat:
    if "msgs" not in st.session_state:
        st.session_state["msgs"] = []

    left_column, right_column = st.columns([5, 1])

    left_column.caption(
        "Ask in English or Amharic. Answers come from the meeting."
    )

    if right_column.button(
        "🧹 Clear",
        use_container_width=True,
        key="clear_chat",
    ):
        st.session_state["msgs"] = []
        st.rerun()

    # Display messages in a scrollable window.
    chat_box = st.container(height=520, border=True)

    # Keep the chat input below the message window.
    question = st.chat_input(
        "Ask a question / ጥያቄዎን ይጠይቁ...",
        key="meeting_chat_input",
    )

    def render_message(message):
        with st.chat_message(
            message["role"],
            avatar="🧑" if message["role"] == "user" else "🤖",
        ):
            st.markdown(message["content"])

            sources = message.get("sources", [])

            if sources:
                with st.expander("📚 Sources"):
                    for index, source in enumerate(sources, 1):
                        st.caption(
                            f"{index}. {source.get('source', 'Source')}: "
                            f"{source.get('text', '')}"
                        )

    if question:
        st.session_state["msgs"].append(
            {
                "role": "user",
                "content": question,
            }
        )

        try:
            with st.spinner("Thinking... / እያሰብኩ ነው..."):
                response = api(
                    "POST",
                    "/chat",
                    json={"question": question},
                    timeout=180,
                )

            if response.ok:
                answer_data = response.json()

                answer = answer_data.get(
                    "answer",
                    "The API did not return an answer.",
                )
                sources = answer_data.get("sources", [])

            else:
                answer = (
                    f"❌ Chat request failed "
                    f"({response.status_code}): {response.text[:1000]}"
                )
                sources = []

        except requests.RequestException as exc:
            answer = f"❌ Could not connect to the API: {exc}"
            sources = []

        st.session_state["msgs"].append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
            }
        )

    with chat_box:
        for message in st.session_state["msgs"]:
            render_message(message)
