
"""
Thin Streamlit frontend that talks to the FastAPI backend.
Run locally: streamlit run frontend/streamlit_app.py
On Streamlit Cloud set secrets:
API_URL = "https://your-api.onrender.com"
APP_API_KEY = "..."
"""

import os
import time
import requests
import streamlit as st


def _secret(name, default=""):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


API_URL = _secret("API_URL", "http://localhost:8000").rstrip("/")
HEADERS = (
    {"X-API-Key": _secret("APP_API_KEY")}
    if _secret("APP_API_KEY")
    else {}
)

st.set_page_config(
    page_title="Ethiopian AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
)

st.markdown(
    "<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;600&display=swap');"
    "html,body,[class*='css']{font-family:'Noto Sans Ethiopic',sans-serif}</style>",
    unsafe_allow_html=True,
)

st.title("🎙️ Ethiopian AI Meeting Assistant")
st.caption("Meeting video/audio → English + አማርኛ reports → chat with the meeting")


def api(method, path, **kw):
    return requests.request(
        method,
        API_URL + path,
        headers=HEADERS,
        timeout=kw.pop("timeout", 120),
        **kw,
    )


# Sidebar: backend status
with st.sidebar:
    st.header("Backend")
    try:
        response = api("GET", "/health", timeout=60)
        response.raise_for_status()
        h = response.json()

        st.success("API online")
        st.write("Gemini key:", "✅" if h["gemini_key_set"] else "❌")
        st.write("Busy:", "⏳ yes" if h["busy"] else "no")
        st.write(
            "Knowledge base:",
            "✅" if h["knowledge_base_ready"] else "○ not built",
        )
    except Exception as e:
        st.error(f"Cannot reach API at {API_URL}")
        st.caption(str(e)[:150])
        st.stop()


tab_run, tab_en, tab_am, tab_chat = st.tabs(
    [
        "🚀 Analyze",
        "🇬🇧 English Report",
        "🇪🇹 የአማርኛ ሪፖርት",
        "💬 Chat / ውይይት",
    ]
)


# Analyze: only one upload interface
with tab_run:
    mode = st.radio(
        "Input",
        ["Upload file", "YouTube / video link"],
        index=0,
        horizontal=True,
    )

    if mode == "YouTube / video link":
        st.info(
            "YouTube link processing has been temporarily deactivated "
            "due to YouTube access restrictions. Please upload your "
            "meeting audio or video file instead."
        )
    else:
        skip_visual = st.checkbox(
            "Skip slide-text (OCR) step — faster",
            value=False,
        )

        f = st.file_uploader(
            "Meeting file",
            type=["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "m4a"],
        )

        if st.button("Start analysis", type="primary"):
            if f is None:
                st.warning("Please upload a meeting file first.")
            else:
                try:
                    r = api(
                        "POST",
                        "/analyze/upload",
                        files={"file": (f.name, f.getvalue())},
                        data={"skip_visual": str(skip_visual).lower()},
                        timeout=600,
                    )

                    if not r.ok:
                        st.error(f"Could not start analysis: {r.text}")
                    else:
                        job = r.json()
                        job_id = job.get("job_id")

                        if not job_id:
                            st.error("The API response did not contain a job ID.")
                        else:
                            box = st.empty()

                            while True:
                                try:
                                    response = api(
                                        "GET",
                                        f"/jobs/{job_id}",
                                        timeout=120,
                                    )
                                    response.raise_for_status()
                                    j = response.json()
                                except requests.RequestException as e:
                                    box.error(f"Could not check progress: {e}")
                                    break

                                box.info(
                                    f"**{j['status']}** — {j['step']}"
                                )

                                if j["status"] == "done":
                                    box.success(
                                        "Finished! Open the report tabs."
                                    )
                                    break

                                if j["status"] == "failed":
                                    box.error(j.get("error", "Analysis failed."))
                                    break

                                time.sleep(8)

                except requests.RequestException as e:
                    st.error(f"Request failed: {e}")


def show_report(path):
    try:
        r = api("GET", path)

        if r.ok:
            md = r.json()["markdown"]
            st.download_button(
                "⬇️ Download (.md)",
                md,
                file_name=path.split("/")[-1] + ".md",
                key=f"download_{path.replace('/', '_')}",
            )
            st.markdown(md)
        else:
            st.info("No report yet. Run an analysis first.")

    except requests.RequestException as e:
        st.error(f"Could not load the report: {e}")


with tab_en:
    show_report("/reports/en")

with tab_am:
    show_report("/reports/amh")


with tab_chat:
    st.session_state.setdefault("msgs", [])

    top_l, top_r = st.columns([5, 1])
    top_l.caption(
        "Ask in English or Amharic. Answers come only from this meeting."
    )

    if top_r.button("🧹 Clear", use_container_width=True):
        st.session_state["msgs"] = []
        st.rerun()

    chat_box = st.container(height=520, border=True)
    q = st.chat_input("Ask a question / ጥያቄዎን ይጠይቁ...")

    def render(m):
        with st.chat_message(
            m["role"],
            avatar="🧑" if m["role"] == "user" else "🤖",
        ):
            st.markdown(m["content"])

            if m.get("sources"):
                with st.expander("📚 Sources"):
                    for i, sc in enumerate(m["sources"], 1):
                        st.caption(
                            f"{i}. {sc['source']}: {sc['text']}"
                        )

    if q:
        st.session_state["msgs"].append(
            {"role": "user", "content": q}
        )

        try:
            with st.spinner("Thinking... / እያሰብኩ ነው..."):
                r = api(
                    "POST",
                    "/chat",
                    json={"question": q},
                    timeout=180,
                )

            if r.ok:
                data = r.json()
                ans = data["answer"]
                srcs = data.get("sources", [])
            else:
                ans = f"❌ {r.text}"
                srcs = []

        except requests.RequestException as e:
            ans = f"❌ Could not connect to the API: {e}"
            srcs = []

        st.session_state["msgs"].append(
            {
                "role": "assistant",
                "content": ans,
                "sources": srcs,
            }
        )

    with chat_box:
        for m in st.session_state["msgs"]:
            render(m)
