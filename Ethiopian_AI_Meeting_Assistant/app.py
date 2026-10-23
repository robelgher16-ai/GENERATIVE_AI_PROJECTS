import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import gc
import io
import os
import re
import sys
import time
import contextlib
from pathlib import Path

# Always work from the project root so all modules share the same outputs/ folder
PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import streamlit as st

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
CHROMA_DIR = OUTPUTS_DIR / "chroma_db"
EN_FILE = OUTPUTS_DIR / "meeting_notes_en.md"
AMH_FILE = OUTPUTS_DIR / "meeting_notes_amh.md"
TRANSCRIPT_FILE = OUTPUTS_DIR / "transcript.txt"
VISUAL_FILE = OUTPUTS_DIR / "visual.txt"

st.set_page_config(
    page_title="Ethiopian AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Results stay hidden on open/refresh until a run is started
if "results_visible" not in st.session_state:
    st.session_state["results_visible"] = False

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stChatMessage {
    font-family: 'Inter', 'Noto Sans Ethiopic', 'Nyala', sans-serif;
}
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1250px; }

.hero {
    padding: 1.6rem 1.8rem;
    border-radius: 18px;
    background: linear-gradient(120deg, #0f766e 0%, #1d4ed8 55%, #7c3aed 100%);
    color: #fff;
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px rgba(29, 78, 216, 0.25);
}
.hero h1 { margin: 0; font-size: 2rem; font-weight: 800; color: #fff; }
.hero p  { margin: .35rem 0 0 0; opacity: .92; font-size: 1.02rem; }
.hero .pill {
    display: inline-block; margin: .7rem .4rem 0 0; padding: .2rem .75rem;
    border-radius: 999px; background: rgba(255,255,255,.18); font-size: .82rem;
}

.card {
    padding: 1rem 1.2rem; border-radius: 14px;
    border: 1px solid rgba(128,128,128,.25);
    background: rgba(128,128,128,.06);
}
.status-row { display:flex; justify-content:space-between; padding:.28rem 0; font-size:.93rem; }
.ok  { color:#16a34a; font-weight:600; }
.bad { color:#9ca3af; font-weight:600; }

.report-box {
    padding: 1.2rem 1.6rem; border-radius: 14px;
    border: 1px solid rgba(128,128,128,.25);
    background: rgba(128,128,128,.04);
}
.amharic { font-family: 'Noto Sans Ethiopic', 'Nyala', sans-serif; line-height: 1.9; }

div.stButton > button, div.stDownloadButton > button {
    border-radius: 10px; font-weight: 600;
}
[data-testid="stMetric"] {
    background: rgba(128,128,128,.07); border: 1px solid rgba(128,128,128,.2);
    padding: .7rem 1rem; border-radius: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def file_ready(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size > 0


def kb_ready() -> bool:
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if file_ready(path) else ""


def api_key_ready() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


class LiveLog(io.StringIO):
    """Captures print() output from the pipeline modules and shows it live."""

    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self._last = 0.0

    def write(self, s):
        result = super().write(s)
        now = time.time()
        if "\n" in s or now - self._last > 0.4:
            self._last = now
            tail = "\n".join(self.getvalue().splitlines()[-60:])
            self.placeholder.code(tail or " ", language=None)
        return result

    def flush(self):
        pass


def release_vector_store():
    """Frees any open database connection so ingestion can delete and rebuild it (needed on Windows).
    The chat itself no longer keeps a cached database: chat_rag opens it fresh for every question."""
    st.cache_resource.clear()
    try:
        from rag.ingest_db import _release_chroma_handles
        _release_chroma_handles()
    except Exception:
        pass
    gc.collect()


# ----------------------------------------------------------------------------
# Pipeline steps (each one only calls your existing functions)
# ----------------------------------------------------------------------------
def step_transcribe(source):
    from core.transcriber import transcribe_audio
    transcribe_audio(source)


def step_visual(source):
    from core.video_processor import process_video_input
    process_video_input(source)


def step_reports():
    from core.summarizer import load_multimodal_inputs, generate_bilingual_reports
    raw_data = load_multimodal_inputs()
    english_report, amharic_report = generate_bilingual_reports(raw_data)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    EN_FILE.write_text(english_report, encoding="utf-8")
    AMH_FILE.write_text(amharic_report, encoding="utf-8")


def step_ingest():
    release_vector_store()
    from rag.ingest_db import run_ingestion
    run_ingestion()


def run_steps(title: str, steps: list) -> bool:
    """steps = [(label, function, is_fatal), ...]. Shows progress and a live log."""
    status = st.status(title, expanded=True)
    log_box = st.expander("📜 Live log (updates while running)", expanded=True).empty()
    log = LiveLog(log_box)
    success = True

    for label, fn, fatal in steps:
        with status:
            st.write(f"⏳ **{label}**")
        t0 = time.time()
        try:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                fn()
            with status:
                st.write(f"✅ {label}: done ({time.time() - t0:.0f}s)")
        except Exception as e:
            if fatal:
                with status:
                    st.error(f"{label} failed: {e}")
                    st.info(
                        "If this was a 503 'high demand' error, it is temporary on Google's side. "
                        "Wait a few minutes and click **Regenerate reports** in the sidebar. "
                        "The earlier steps will not be repeated."
                    )
                status.update(label=f"❌ {title}: failed", state="error", expanded=True)
                success = False
                break
            with status:
                st.warning(f"{label} had a problem: {e}. Continuing with available data.")

    if success:
        status.update(label=f"✅ {title}: completed", state="complete", expanded=False)
        st.toast("Finished successfully!", icon="🎉")
    return success


def clear_old_outputs():
    for f in (TRANSCRIPT_FILE, VISUAL_FILE, EN_FILE, AMH_FILE):
        try:
            if f.exists():
                f.unlink()
        except Exception:
            pass


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎙️ Meeting Assistant")
    st.caption("Audio + visual analysis → bilingual reports → chat")

    st.markdown("### 📊 Status")
    shown = st.session_state["results_visible"]
    rows = [
        ("Gemini API key", api_key_ready()),
        ("Audio transcript", shown and file_ready(TRANSCRIPT_FILE)),
        ("Visual text", shown and file_ready(VISUAL_FILE)),
        ("English report", shown and file_ready(EN_FILE)),
        ("Amharic report", shown and file_ready(AMH_FILE)),
        ("Knowledge base", shown and kb_ready()),
    ]
    html = '<div class="card">'
    for name, ok in rows:
        mark = '<span class="ok">● Ready</span>' if ok else '<span class="bad">○ Missing</span>'
        html += f'<div class="status-row"><span>{name}</span>{mark}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    if not api_key_ready():
        st.error("GEMINI_API_KEY not found. Add it to your .env file and restart the app.")

    st.markdown("### ⚙️ Options")
    clear_old = st.checkbox(
        "Clear previous results before a new run",
        value=True,
        help="Prevents old transcripts or reports from mixing with the new meeting.",
    )

    st.markdown("### ⚡ Quick actions")
    st.caption("Use these to continue without redoing earlier steps.")
    quick_reports = st.button(
        "📝 Regenerate reports",
        use_container_width=True,
        disabled=not (file_ready(TRANSCRIPT_FILE) or file_ready(VISUAL_FILE)) or not api_key_ready(),
    )
    quick_ingest = st.button(
        "🧠 Rebuild knowledge base",
        use_container_width=True,
        disabled=not (file_ready(EN_FILE) or file_ready(AMH_FILE)),
    )

# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
  <h1>🎙️ Ethiopian AI Meeting Assistant</h1>
  <p>Turn any meeting video into clear English and Amharic reports, then ask questions about it.</p>
  <span class="pill">🎧 Audio transcription</span>
  <span class="pill">👁️ Slide text extraction</span>
  <span class="pill">🇬🇧 English report</span>
  <span class="pill">🇪🇹 አማርኛ report</span>
  <span class="pill">💬 Bilingual chat</span>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Input card
# ----------------------------------------------------------------------------
st.markdown("### Choose your meeting")
mode = st.radio(
    "Input type",
    ["🔗 YouTube link", "📁 Upload a file", "📂 Local file path"],
    horizontal=True,
    label_visibility="collapsed",
)

source_value = ""
uploaded = None

if mode == "🔗 YouTube link":
    source_value = st.text_input("YouTube link", placeholder="https://www.youtube.com/watch?v=...").strip()
elif mode == "📁 Upload a file":
    uploaded = st.file_uploader(
        "Upload a meeting video or audio file",
        type=["mp4", "mov", "mkv", "avi", "webm", "mp3", "wav", "m4a"],
        help="Large files: start the app with `streamlit run app.py --server.maxUploadSize 2000`",
    )
else:
    source_value = st.text_input("Full path to a local video", placeholder=r"C:\Videos\meeting.mp4").strip().strip('"')

start = st.button(
    "🚀 Start full analysis",
    type="primary",
    use_container_width=True,
    disabled=not api_key_ready(),
)
st.caption("⚠️ While the analysis is running, don't click anything or refresh the page, or the run will restart.")

# ----------------------------------------------------------------------------
# Run actions
# ----------------------------------------------------------------------------
if start:
    source = source_value
    problem = None

    if mode == "📁 Upload a file":
        if uploaded is None:
            problem = "Please upload a file first."
        else:
            DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
            saved = DOWNLOADS_DIR / Path(uploaded.name).name
            saved.write_bytes(uploaded.getbuffer())
            source = str(saved)
    elif not source:
        problem = "Please enter a link or path first."
    elif mode == "📂 Local file path" and not Path(source).exists():
        problem = f"File not found: {source}"

    if problem:
        st.warning(problem)
    else:
        if clear_old:
            clear_old_outputs()
        st.session_state["messages"] = []
        run_steps(
            "Full pipeline",
            [
                ("Step 1: Audio transcription", lambda: step_transcribe(source), True),
                ("Step 2: Visual text extraction", lambda: step_visual(source), False),
                ("Step 3: Bilingual reports", step_reports, True),
                ("Step 4: Knowledge base", step_ingest, True),
            ],
        )
        st.session_state["results_visible"] = True

if quick_reports:
    run_steps("Regenerate reports", [("Bilingual reports", step_reports, True), ("Knowledge base", step_ingest, True)])
    st.session_state["results_visible"] = True

if quick_ingest:
    run_steps("Rebuild knowledge base", [("Knowledge base", step_ingest, True)])
    st.session_state["results_visible"] = True

# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
st.markdown("### Results")

visible = st.session_state["results_visible"]

transcript_text = read_text(TRANSCRIPT_FILE) if visible else ""
visual_text = read_text(VISUAL_FILE) if visible else ""

tab_en, tab_amh, tab_chat, tab_raw = st.tabs(
    ["🇬🇧 English Report", "🇪🇹 የአማርኛ ሪፖርት", "💬 Chat with the meeting", "🗂️ Raw data"]
)

# ---- English report
with tab_en:
    en_text = read_text(EN_FILE) if visible else ""
    if en_text:
        st.download_button(
            "⬇️ Download English report (.md)",
            en_text,
            file_name="meeting_notes_en.md",
            mime="text/markdown",
            key="dl_en_md",
        )
        st.markdown('<div class="report-box">', unsafe_allow_html=True)
        st.markdown(en_text)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No English report yet. Start the analysis above.")

# ---- Amharic report
with tab_amh:
    amh_text = read_text(AMH_FILE) if visible else ""
    if amh_text:
        st.download_button(
            "⬇️ ሪፖርቱን አውርድ (.md)",
            amh_text,
            file_name="meeting_notes_amh.md",
            mime="text/markdown",
            key="dl_amh_md",
        )
        st.markdown('<div class="report-box amharic">', unsafe_allow_html=True)
        st.markdown(amh_text)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No Amharic report yet. Start the analysis above.")

# ---- Chat
with tab_chat:
    if not (visible and kb_ready()):
        st.info("The knowledge base is not built yet. Run the analysis or use **Rebuild knowledge base** in the sidebar.")
    else:
        if "messages" not in st.session_state:
            st.session_state["messages"] = []

        top_l, top_r = st.columns([4, 1])
        with top_l:
            st.caption("Ask in English or Amharic. Answers come only from this meeting's records.")
        with top_r:
            if st.button("🧹 Clear chat", use_container_width=True):
                st.session_state["messages"] = []
                st.rerun()

        s1, s2, s3 = st.columns(3)
        suggestion = None
        if s1.button("📋 Summarize the meeting", use_container_width=True):
            suggestion = "Give me a short summary of the meeting."
        if s2.button("✅ What are the action items?", use_container_width=True):
            suggestion = "What are the action items and who owns them?"
        if s3.button("🎯 ዋና ዋና ውሳኔዎች ምንድን ናቸው?", use_container_width=True):
            suggestion = "በስብሰባው ላይ ዋና ዋና ውሳኔዎች ምንድን ናቸው?"

        # Scrollable chat window: messages stack downward, input sits under it.
        chat_box = st.container(height=520, border=True)

        with chat_box:
            for msg in st.session_state["messages"]:
                with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
                    st.markdown(msg["content"])
                    if msg.get("sources"):
                        with st.expander("📚 Sources used"):
                            for i, src in enumerate(msg["sources"], start=1):
                                st.markdown(f"**Source {i}: {src['source']}**")
                                st.caption(src["text"])

        question = st.chat_input("Ask a question / ጥያቄዎን ይጠይቁ...") or suggestion

        if question:
            st.session_state["messages"].append({"role": "user", "content": question})
            with chat_box:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(question)

                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Searching the meeting records and writing an answer..."):
                        sources = []
                        try:
                            from rag.chat_rag import answer_question

                            # Opens the database fresh for every question, so it always works
                            # (also right after 'Rebuild knowledge base')
                            answer, docs = answer_question(question, return_sources=True)
                            sources = [
                                {
                                    "source": d.metadata.get("source", "meeting record"),
                                    "text": d.page_content[:400],
                                }
                                for d in docs
                            ]
                        except Exception as e:
                            answer, sources = f"❌ Chat error: {e}", []

                    st.markdown(answer)
                    if sources:
                        with st.expander("📚 Sources used"):
                            for i, src in enumerate(sources, start=1):
                                st.markdown(f"**Source {i}: {src['source']}**")
                                st.caption(src["text"])

            st.session_state["messages"].append({"role": "assistant", "content": answer, "sources": sources})

# ---- Raw data
with tab_raw:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🎧 Audio transcript")
        if transcript_text:
            st.text_area("transcript", transcript_text, height=420, label_visibility="collapsed")
        else:
            st.info("No transcript yet.")
    with c2:
        st.markdown("#### 👁️ Visual / slide text")
        if visual_text:
            st.text_area("visual", visual_text, height=420, label_visibility="collapsed")
        else:
            st.info("No visual text yet.")

st.markdown("---")
st.caption("✨ Ethiopian AI Meeting Assistant · Powered by Gemini, ChromaDB and FastEmbed")