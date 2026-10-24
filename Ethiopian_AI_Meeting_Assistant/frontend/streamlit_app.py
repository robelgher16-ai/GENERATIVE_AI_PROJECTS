"""
Thin Streamlit frontend that talks to the FastAPI backend.
Run locally:  API_URL=http://localhost:8000 streamlit run streamlit_app.py
On Streamlit Cloud set secrets:  API_URL = "https://your-api.onrender.com"   APP_API_KEY = "..."
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
HEADERS = {"X-API-Key": _secret("APP_API_KEY")} if _secret("APP_API_KEY") else {}

st.set_page_config(page_title="Ethiopian AI Meeting Assistant", page_icon="🎙️", layout="wide")
st.markdown("<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;600&display=swap');"
            "html,body,[class*='css']{font-family:'Noto Sans Ethiopic',sans-serif}</style>", unsafe_allow_html=True)
st.title("🎙️ Ethiopian AI Meeting Assistant")
st.caption("Meeting video/audio → English + አማርኛ reports → chat with the meeting")

def api(method, path, **kw):
    return requests.request(method, API_URL + path, headers=HEADERS, timeout=kw.pop("timeout", 120), **kw)

# ---- sidebar: backend status
with st.sidebar:
    st.header("Backend")
    try:
        h = api("GET", "/health", timeout=60).json()   # long timeout: free Render servers need ~50s to wake up
        st.success("API online")
        st.write("Gemini key:", "✅" if h["gemini_key_set"] else "❌")
        st.write("Busy:", "⏳ yes" if h["busy"] else "no")
        st.write("Knowledge base:", "✅" if h["knowledge_base_ready"] else "○ not built")
    except Exception as e:
        st.error(f"Cannot reach API at {API_URL}")
        st.caption(str(e)[:150])
        st.stop()

tab_run, tab_en, tab_am, tab_chat = st.tabs(["🚀 Analyze", "🇬🇧 English Report", "🇪🇹 የአማርኛ ሪፖርት", "💬 Chat / ውይይት"])

with tab_run:
    mode = st.radio(
        "Input",
        ["Upload file", "YouTube / video link"],
        index=0,
        horizontal=True,
    )

    skip_visual = st.checkbox(
        "Skip slide-text (OCR) step — faster",
        value=False,
    )

    job = None

    if mode == "YouTube / video link":
        st.info(
            "YouTube link processing has been temporarily deactivated "
            "due to YouTube access restrictions. Please upload your "
            "meeting audio or video file instead."
        )

    else:
        f = st.file_uploader(
            "Meeting file",
            type=["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "m4a"],
        )

        if st.button("Start analysis", type="primary") and f:
            r = api(
                "POST",
                "/analyze/upload",
                files={"file": (f.name, f.getvalue())},
                data={"skip_visual": str(skip_visual).lower()},
                timeout=600,
            )
            job = r.json() if r.ok else st.error(r.text)

    if job and "job_id" in job:
        box = st.empty()

        while True:
            j = api("GET", f"/jobs/{job['job_id']}").json()
            box.info(f"**{j['status']}** — {j['step']}")

            if j["status"] == "done":
                box.success("Finished! Open the report tabs.")
                break

            if j["status"] == "failed":
                box.error(j.get("error"))
                break

            time.sleep(8)


    job = None
    if mode == "YouTube / video link":
        url = st.text_input("Link", placeholder="https://www.youtube.com/watch?v=...")
        if st.button("Start analysis", type="primary") and url:
            r = api("POST", "/analyze/url", json={"url": url, "skip_visual": skip_visual})
            job = r.json() if r.ok else st.error(r.text)
    else:
        f = st.file_uploader("Meeting file", type=["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "m4a"])
        if st.button("Start analysis", type="primary") and f:
            r = api("POST", "/analyze/upload", files={"file": (f.name, f.getvalue())},
                    data={"skip_visual": str(skip_visual).lower()}, timeout=600)
            job = r.json() if r.ok else st.error(r.text)
    if job and "job_id" in job:
        box = st.empty()
        while True:
            j = api("GET", f"/jobs/{job['job_id']}").json()
            box.info(f"**{j['status']}** — {j['step']}")
            if j["status"] == "done":
                box.success("Finished! Open the report tabs."); break
            if j["status"] == "failed":
                box.error(j.get("error")); break
            time.sleep(8)

def show_report(path):
    r = api("GET", path)
    if r.ok:
        md = r.json()["markdown"]
        st.download_button("⬇️ Download (.md)", md, file_name=path.split("/")[-1] + ".md")
        st.markdown(md)
    else:
        st.info("No report yet. Run an analysis first.")

with tab_en: show_report("/reports/en")
with tab_am: show_report("/reports/amh")

with tab_chat:
    st.session_state.setdefault("msgs", [])

    top_l, top_r = st.columns([5, 1])
    top_l.caption("Ask in English or Amharic. Answers come only from this meeting.")
    if top_r.button("🧹 Clear", use_container_width=True):
        st.session_state["msgs"] = []
        st.rerun()

    # 1) the message window is created FIRST  -> everything (old + current) appears inside it, above the input
    chat_box = st.container(height=520, border=True)

    # 2) the input box is created AFTER the window -> it is always underneath all messages
    q = st.chat_input("Ask a question / ጥያቄዎን ይጠይቁ...")

    def render(m):
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
            st.markdown(m["content"])
            if m.get("sources"):
                with st.expander("📚 Sources"):
                    for i, sc in enumerate(m["sources"], 1):
                        st.caption(f"{i}. {sc['source']}: {sc['text']}")

    with chat_box:
        for m in st.session_state["msgs"]:
            render(m)
        if q:
            user_msg = {"role": "user", "content": q}
            st.session_state["msgs"].append(user_msg)
            render(user_msg)                     # your question shows immediately, inside the window
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking... / እያሰብኩ ነው..."):
                    r = api("POST", "/chat", json={"question": q})
                    ans = r.json()["answer"] if r.ok else f"❌ {r.text}"
                    srcs = r.json()["sources"] if r.ok else []
            bot_msg = {"role": "assistant", "content": ans, "sources": srcs}
            st.session_state["msgs"].append(bot_msg)
            render(bot_msg)