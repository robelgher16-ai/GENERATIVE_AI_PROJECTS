"""
Ethiopian AI Meeting Assistant - Streamlit frontend (talks to the FastAPI backend).
Local:   streamlit run frontend/streamlit_app.py
Cloud:   secrets  API_URL = "https://your-api.onrender.com"   APP_API_KEY = "..."
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
    "html,body,[class*='css']{font-family:'Noto Sans Ethiopic',sans-serif}"
    ".block-container{padding-top:2.2rem}"
    "div[data-testid='stVerticalBlock']{gap:0.6rem}"
    "</style>",
    unsafe_allow_html=True,
)


def err_text(r):
    """Readable error from ANY response (JSON or not)."""
    try:
        return str(r.json().get("detail", r.text))[:300]
    except Exception:
        return f"HTTP {r.status_code} — {(r.text or 'empty response')[:200]}"


def api(method, path, **kw):
    return requests.request(method, API_URL + path, headers=HEADERS,
                            timeout=kw.pop("timeout", 120), **kw)


# ------------------------------------------------------------------ cached reads
@st.cache_data(ttl=15, show_spinner=False)
def get_health():
    r = api("GET", "/health", timeout=60)   # long timeout: a sleeping Render server needs ~50s to wake
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=300, show_spinner=False)
def get_report(path, version):              # NOTE: no leading underscore, so a new `version` refreshes the cache
    r = api("GET", path)
    if not r.ok:
        raise LookupError("no report")      # errors are never cached, so "no report yet" is re-checked next time
    return r.json()["markdown"]


st.session_state.setdefault("version", 0)
st.session_state.setdefault("msgs", [])
st.session_state.setdefault("up_n", 0)
st.session_state.setdefault("running", False)
st.session_state.setdefault("need_file", False)

# ------------------------------------------------------------------ sidebar = navigation
def go(feature):
    st.session_state["page"] = feature      # opens that feature page (and highlights it in the sidebar)


def refresh_all():
    """Start fresh for a NEW upload: clear chat, finished-state, timings and the uploaded file, go to Analysis."""
    st.session_state["msgs"] = []
    st.session_state["done_sig"] = None
    st.session_state["timings"] = None
    st.session_state["running"] = False
    st.session_state["need_file"] = False
    st.session_state["up_n"] += 1           # new uploader key -> the old file disappears
    st.session_state["version"] += 1        # reports are re-read from the server
    st.session_state["page"] = None         # back to the Analysis page
    get_health.clear()


FEATURES = ["🇬🇧 English Report", "🇪🇹 የአማርኛ ሪፖርት", "💬 Chat / ውይይት"]


with st.sidebar:
    st.markdown("### 🎙️ Ethiopian AI Meeting Assistant")
    st.markdown("**Features**")
    page = st.radio("Features", FEATURES, index=None, key="page", label_visibility="collapsed")
    st.button("🔄 Refresh / አድስ", key="side_refresh", on_click=refresh_all, use_container_width=True)

try:
    h = get_health()
except Exception:
    h = None

if h is None:
    st.title("🎙️ Ethiopian AI Meeting Assistant")
    st.error("The backend API is not answering, so nothing can work yet.")
    st.markdown(
        "- On Render the free/low plan **sleeps** — wait ~1 minute and press **Refresh status**.\n"
        "- Check the `API_URL` secret is exactly your Render address (no trailing path).\n"
        "- Open `<API_URL>/health` in a browser. If it fails there, the problem is the Render service "
        "(see its **Logs** tab: crashed or out of memory)."
    )
    st.caption(f"API address in use: {API_URL}")
    if st.button("🔄 Try again"):
        get_health.clear()
        st.rerun()
    st.stop()


# ------------------------------------------------------------------ job progress
def watch_job(job_id, sig=None):
    """Live progress of a job - works for a job you just started or one already running on the server."""
    bar = st.progress(0.03, text="Queued...")
    steps = {"1/4": 0.15, "2/4": 0.45, "3/4": 0.75, "4/4": 0.92}
    t0 = time.time()
    while True:
        try:
            j = api("GET", f"/jobs/{job_id}", timeout=60).json()
        except Exception as e:
            st.error(f"Lost connection while checking progress: {e}")
            return
        mins, secs = divmod(int(time.time() - t0), 60)
        if j["status"] == "done":
            bar.progress(1.0, text=f"Finished ✅ ({mins}m {secs}s)")
            st.session_state["version"] += 1
            st.session_state["msgs"] = []
            st.session_state["done_sig"] = sig
            st.session_state["timings"] = j.get("timings", {})
            get_health.clear()
            st.success("Finished! Open the reports from the menu on the left, or start chatting.")
            if j.get("warning"):
                st.caption(f"ℹ️ {j['warning']}")
            return
        if j["status"] == "failed":
            get_health.clear()
            st.error(f"Analysis failed: {j.get('error') or 'unknown error'}")
            return
        bar.progress(steps.get(j["step"][:3], 0.05), text=f"{j['step']} — {mins}m {secs:02d}s elapsed")
        time.sleep(3)


def run_analysis(file, skip_visual):
    try:
        r = api("POST", "/analyze/upload", files={"file": (file.name, file.getvalue())},
                data={"skip_visual": str(skip_visual).lower()}, timeout=600)
    except requests.RequestException as e:
        st.error(f"Upload failed: {e}")
        return
    if r.status_code == 409:
        get_health.clear()
        return
    if not r.ok:
        st.error(f"Could not start analysis — {err_text(r)}")
        return
    watch_job(r.json()["job_id"], (file.name, file.size))


# ------------------------------------------------------------------ pages
def start_clicked():
    """Runs the moment the button is pressed (before the page redraws)."""
    f = st.session_state.get(f"uploader_{st.session_state['up_n']}")
    if f is None:
        st.session_state["need_file"] = True        # nothing uploaded -> ask the user to upload
    else:
        st.session_state["need_file"] = False
        st.session_state["running"] = True          # pressed (disabled) until the result is ready


def page_analyze():
    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)   # ~2 cm space before the upload title
    st.markdown("##### Upload a meeting")
    f = st.file_uploader("Meeting audio or video file", key=f"uploader_{st.session_state['up_n']}",
                         type=["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "m4a"])
    skip_visual = st.checkbox("Skip slide-text (OCR) step — much faster", value=False)

    running = st.session_state["running"]
    already_done = f is not None and st.session_state.get("done_sig") == (f.name, f.size)

    # Red + clickable when nothing is uploaded (clicking asks for a file) and after upload.
    # Pressed (disabled) while the analysis runs, and for a file that is already analysed.
    btn_slot = st.empty()
    btn_slot.button("🚀 Start analysis", key="start_btn", type="primary",
                    disabled=running or already_done or bool(h.get("active_job")),
                    on_click=start_clicked)

    if st.session_state["need_file"]:
        st.session_state["need_file"] = False
        st.warning("Please upload a meeting file first (wait until the upload shows a green tick).")

    if running and f is not None:
        try:
            st.toast(f"Uploading {f.name} ({f.size/1_048_576:.1f} MB)...")
            run_analysis(f, skip_visual)
        finally:
            st.session_state["running"] = False
        done_now = st.session_state.get("done_sig") == (f.name, f.size)
        btn_slot.button("🚀 Start analysis", key="start_btn_after", type="primary",
                        disabled=done_now, on_click=start_clicked)   # free again if it failed
        already_done = done_now
    elif running:
        st.session_state["running"] = False

    if already_done:
        st.caption("✅ This file is already analysed. Upload a different file to start again.")

    if h.get("active_job") and not running:
        if st.button("👀 Watch running analysis"):
            watch_job(h["active_job"])

    t = st.session_state.get("timings")
    if t:
        with st.expander("⏱️ Where the time went (per step)"):
            for k, v in t.items():
                st.write(f"**{k}**: {v:.0f}s")

    st.divider()
    st.text_input("YouTube / video link (not active)", placeholder="Coming soon — please upload a file instead", disabled=True)
    st.caption("🔒 This box is switched off on purpose (YouTube blocks cloud servers). It does not affect file upload.")


def page_report(title, path, empty_msg):
    st.subheader(title)
    try:
        md = get_report(path, st.session_state["version"])
    except Exception:
        st.info(empty_msg)
        return
    st.download_button("⬇️ Download (.md)", md, file_name=path.split("/")[-1] + ".md", key=f"dl_{path}")
    st.markdown(md)


def body(m):
    st.markdown(m["content"])
    if m.get("sources"):
        with st.expander("📚 Sources"):
            for i, s in enumerate(m["sources"], 1):
                st.caption(f"{i}. {s['source']}: {s['text']}")


def render(m):
    with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🤖"):
        body(m)


def page_chat():
    st.subheader("💬 Chat / ውይይት")
    left, right = st.columns([5, 1])
    left.caption("Ask in English or Amharic. Answers come only from this meeting.")
    if right.button("🧹 Clear", use_container_width=True):
        st.session_state["msgs"] = []
        st.rerun()

    chat_box = st.container(height=420, border=True)        # all messages (old + current) live here
    q = st.chat_input("Ask a question / ጥያቄዎን ይጠይቁ...")   # input is always underneath

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
                        try:
                            data = r.json() if r.ok else None
                        except ValueError:
                            data = None
                        if data and "answer" in data:
                            ans, srcs = data["answer"], data.get("sources", [])
                        else:
                            ans, srcs = (f"❌ The server answered with an error — {err_text(r)}\n\n"
                                         "If the server restarted, upload the meeting again (Render's disk is temporary)."), []
                    except requests.RequestException as e:
                        ans, srcs = f"❌ Could not reach the API (network/timeout): {e}", []
                bot = {"role": "assistant", "content": ans, "sources": srcs}
                body(bot)
            st.session_state["msgs"].append(bot)


# ------------------------------------------------------------------ fixed header (never moves)
st.title("🎙️ Ethiopian AI Meeting Assistant")
st.caption("Upload a meeting → English + አማርኛ reports → chat with it")

NAV = [("🚀 Analysis", None, "nav_home"),
       ("🇪🇹 የአማርኛ ሪፖርት", FEATURES[1], "nav_am"),
       ("🇬🇧 English Report", FEATURES[0], "nav_en"),
       ("💬 Chat / ውይይት", FEATURES[2], "nav_chat")]
for col, (label, target, key) in zip(st.columns(len(NAV), gap="small"), NAV):
    col.button(label, key=key, on_click=go, args=(target,), use_container_width=True,
               type="primary" if page == target else "secondary")

# only the selected page runs -> faster than tabs (tabs run ALL pages on every click)
if page is None:
    page_analyze()
elif page == FEATURES[0]:
    page_report("🇬🇧 English Report", "/reports/en", "No report yet. Open 🚀 Analysis and upload a meeting first.")
elif page == FEATURES[1]:
    page_report("🇪🇹 የአማርኛ ሪፖርት", "/reports/amh", "ሪፖርት የለም። መጀመሪያ በ 🚀 Analysis ስብሰባ ይጫኑ።")
else:
    page_chat()