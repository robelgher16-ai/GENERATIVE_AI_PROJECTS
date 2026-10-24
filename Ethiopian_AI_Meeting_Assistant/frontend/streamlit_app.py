"""
Ethiopian AI Meeting Assistant - Streamlit frontend (talks to the FastAPI backend).
Local:   streamlit run frontend/streamlit_app.py
Cloud:   set secrets  API_URL = "https://your-api.onrender.com"   APP_API_KEY = "..."
"""
import os
import time
import requests
import streamlit as st

st.set_page_config(page_title="Ethiopian AI Meeting Assistant", page_icon="🎙️", layout="wide")


# ------------------------------------------------------------------ config
def _secret(name, default=""):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


API_URL = _secret("API_URL", "http://localhost:8000").rstrip("/")
API_KEY = _secret("APP_API_KEY")
HEADERS = {"X-API-Key": API_KEY} if API_KEY else {}

st.markdown(
    "<style>@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;600&display=swap');"
    "html,body,[class*='css']{font-family:'Noto Sans Ethiopic',sans-serif}</style>",
    unsafe_allow_html=True,
)


def api(method, path, **kw):
    return requests.request(method, API_URL + path, headers=HEADERS,
                            timeout=kw.pop("timeout", 120), **kw)


# ------------------------------------------------------------------ cached reads (fast)
# Streamlit re-runs the whole script on every click/message. Caching stops it from
# calling the server for health + both reports each time you chat.
@st.cache_data(ttl=20, show_spinner=False)
def get_health():
    r = api("GET", "/health", timeout=60)   # long timeout: sleeping Render servers need ~50s to wake
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300, show_spinner=False)
def get_report(path, _version):
    r = api("GET", path)
    return r.json()["markdown"] if r.ok else None


st.session_state.setdefault("version", 0)    # bumped when a new analysis finishes -> refreshes reports
st.session_state.setdefault("msgs", [])

# ------------------------------------------------------------------ header + sidebar
st.title("🎙️ Ethiopian AI Meeting Assistant")
st.caption("Meeting video/audio → English + አማርኛ reports → chat with the meeting")

with st.sidebar:
    st.header("Backend")
    try:
        h = get_health()
        st.success("API online")
        st.write("Gemini key:", "✅" if h["gemini_key_set"] else "❌")
        st.write("Busy:", "⏳ yes" if h["busy"] else "free")
        st.write("Knowledge base:", "✅ ready" if h["knowledge_base_ready"] else "○ not built")
        if st.button("🔄 Refresh status", use_container_width=True):
            get_health.clear()
            st.rerun()
    except Exception as e:
        st.error("Cannot reach the API.")
        st.caption(f"{API_URL}\n\n{str(e)[:150]}")
        if st.button("Try again", use_container_width=True):
            get_health.clear()
            st.rerun()
        st.stop()

tab_run, tab_en, tab_am, tab_chat = st.tabs(
    ["🚀 Analyze", "🇬🇧 English Report", "🇪🇹 የአማርኛ ሪፖርት", "💬 Chat / ውይይት"]
)


# ------------------------------------------------------------------ analyze
def run_analysis(file):
    try:
        r = api("POST", "/analyze/upload",
                files={"file": (file.name, file.getvalue())},
                data={"skip_visual": str(skip_visual).lower()}, timeout=600)
    except requests.RequestException as e:
        st.error(f"Upload failed: {e}")
        return
    if not r.ok:
        st.error(f"Could not start analysis: {r.text}")
        return
    job_id = r.json().get("job_id")
    bar = st.progress(0, text="Queued...")
    steps = {"1/4": 0.15, "2/4": 0.45, "3/4": 0.75, "4/4": 0.92}
    while True:
        try:
            j = api("GET", f"/jobs/{job_id}", timeout=60).json()
        except Exception as e:
            st.error(f"Lost connection while checking progress: {e}")
            return
        if j["status"] == "done":
            bar.progress(1.0, text="Finished ✅")
            st.session_state["version"] += 1      # refresh cached reports
            st.session_state["msgs"] = []          # new meeting -> fresh chat
            get_health.clear()
            st.success("Finished! Open the report tabs or start chatting.")
            if j.get("warning"):
                st.caption(f"ℹ️ {j['warning']}")
            return
        if j["status"] == "failed":
            st.error(j.get("error") or "Analysis failed.")
            return
        bar.progress(steps.get(j["step"][:3], 0.05), text=f"{j['status']} — {j['step']}")
        time.sleep(6)


with tab_run:
    st.subheader("Upload a meeting")
    f = st.file_uploader("Meeting audio or video file",
                         type=["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "m4a"])
    skip_visual = st.checkbox("Skip slide-text (OCR) step — faster", value=False)

    if st.button("🚀 Start analysis", type="primary", disabled=h["busy"]):
        if f is None:
            st.warning("Please upload a meeting file first.")
        else:
            run_analysis(f)
    if h["busy"]:
        st.caption("⏳ Another analysis is running. Please wait for it to finish.")

    st.divider()
    # YouTube = visible placeholder only (disabled, not the default)
    st.text_input("YouTube / video link", placeholder="Coming soon — please upload a file instead",
                  disabled=True)
    st.caption("🔒 YouTube links are turned off for now because YouTube blocks cloud servers.")


# ------------------------------------------------------------------ reports
def show_report(path, empty_msg):
    md = get_report(path, st.session_state["version"])
    if md is None:
        st.info(empty_msg)
        return
    st.download_button("⬇️ Download (.md)", md, file_name=path.split("/")[-1] + ".md",
                       key=f"dl_{path}")
    st.markdown(md)


with tab_en:
    show_report("/reports/en", "No report yet. Upload a meeting in the Analyze tab first.")
with tab_am:
    show_report("/reports/amh", "ሪፖርት የለም። መጀመሪያ በ Analyze ትር ስብሰባ ይጫኑ።")


# ------------------------------------------------------------------ chat
def body(m):
    st.markdown(m["content"])
    if m.get("sources"):
        with st.expander("📚 Sources"):
            for i, s in enumerate(m["sources"], 1):
                st.caption(f"{i}. {s['source']}: {s['text']}")


def render(m):
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
        body(m)


with tab_chat:
    left, right = st.columns([5, 1])
    left.caption("Ask in English or Amharic. Answers come only from this meeting.")
    if right.button("🧹 Clear", use_container_width=True):
        st.session_state["msgs"] = []
        st.rerun()

    chat_box = st.container(height=520, border=True)       # all messages live here (above)
    q = st.chat_input("Ask a question / ጥያቄዎን ይጠይቁ...")  # input always underneath

    with chat_box:
        if not st.session_state["msgs"] and not q:
            st.caption("👋 No messages yet. Ask something about the meeting below.")
        for m in st.session_state["msgs"]:
            render(m)
        if q:
            user_msg = {"role": "user", "content": q}
            st.session_state["msgs"].append(user_msg)
            render(user_msg)
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking... / እያሰብኩ ነው..."):
                    try:
                        r = api("POST", "/chat", json={"question": q}, timeout=180)
                        if r.ok:
                            ans, srcs = r.json()["answer"], r.json().get("sources", [])
                        else:
                            ans, srcs = f"❌ {r.json().get('detail', r.text)}", []
                    except Exception as e:
                        ans, srcs = f"❌ Could not reach the API: {e}", []
                bot = {"role": "assistant", "content": ans, "sources": srcs}
                body(bot)                      # answer fills the same bubble the spinner used
            st.session_state["msgs"].append(bot)