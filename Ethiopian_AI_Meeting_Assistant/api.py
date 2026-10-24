"""
FastAPI backend for the Ethiopian AI Meeting Assistant.
Run locally:  uvicorn api:app --reload --port 8000
Docs (auto):  http://localhost:8000/docs
"""
import os
import sys
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
EN_FILE = OUTPUTS_DIR / "meeting_notes_en.md"
AMH_FILE = OUTPUTS_DIR / "meeting_notes_amh.md"
TRANSCRIPT_FILE = OUTPUTS_DIR / "transcript.txt"
VISUAL_FILE = OUTPUTS_DIR / "visual.txt"
CHROMA_DIR = OUTPUTS_DIR / "chroma_db"
for d in (OUTPUTS_DIR, DOWNLOADS_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Ethiopian AI Meeting Assistant API",
    description="Transcribe a meeting, generate English + Amharic reports, and chat with it (RAG).",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- security
def check_api_key(x_api_key: Optional[str] = Header(default=None)):
    """If APP_API_KEY is set on the server, every protected call must send it
    in the 'X-API-Key' header. If it is not set, the API is open (fine for local tests)."""
    required = os.environ.get("APP_API_KEY")
    if required and x_api_key != required:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


# ---------------------------------------------------------------- job state
# The pipeline works on ONE meeting at a time (it shares the outputs/ folder),
# so we keep a single lock and a small in-memory job table.
JOBS: dict = {}
PIPELINE_LOCK = threading.Lock()


def _set(job_id: str, **kw):
    JOBS[job_id].update(kw, updated_at=time.time())


def _run_pipeline(job_id: str, source: str, skip_visual: bool):
    if not PIPELINE_LOCK.acquire(blocking=False):
        _set(job_id, status="failed", error="Another analysis is already running. Try again later.")
        return
    try:
        for f in (TRANSCRIPT_FILE, VISUAL_FILE, EN_FILE, AMH_FILE):
            f.unlink(missing_ok=True)

        _set(job_id, status="running", step="1/4 Audio transcription")
        from core.transcriber import transcribe_audio
        transcribe_audio(source)

        if not skip_visual:
            _set(job_id, step="2/4 Visual text extraction")
            try:
                from core.video_processor import process_video_input
                process_video_input(source)
            except Exception as e:  # visual step is optional (same as app.py)
                _set(job_id, warning=f"Visual step skipped: {e}")

        _set(job_id, step="3/4 Bilingual reports")
        from core.summarizer import load_multimodal_inputs, generate_bilingual_reports
        en, amh = generate_bilingual_reports(load_multimodal_inputs())
        EN_FILE.write_text(en, encoding="utf-8")
        AMH_FILE.write_text(amh, encoding="utf-8")

        _set(job_id, step="4/4 Knowledge base")
        from rag.ingest_db import run_ingestion
        run_ingestion()

        _set(job_id, status="done", step="finished")
    except Exception as e:
        _set(job_id, status="failed", error=str(e)[:500])
    finally:
        PIPELINE_LOCK.release()


def _new_job() -> str:
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"job_id": job_id, "status": "queued", "step": "waiting",
                    "error": None, "warning": None,
                    "created_at": time.time(), "updated_at": time.time()}
    return job_id


# ---------------------------------------------------------------- schemas
class AnalyzeURL(BaseModel):
    url: str
    skip_visual: bool = False


class ChatRequest(BaseModel):
    question: str
    k: int = 6


# ---------------------------------------------------------------- endpoints
@app.get("/", tags=["system"])
def root():
    return {"name": app.title, "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "gemini_key_set": bool(os.environ.get("GEMINI_API_KEY")),
        "api_key_protection": bool(os.environ.get("APP_API_KEY")),
        "busy": PIPELINE_LOCK.locked(),
        "knowledge_base_ready": CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()),
    }


@app.post("/analyze/url", tags=["pipeline"], dependencies=[Depends(check_api_key)])
def analyze_url(body: AnalyzeURL, background: BackgroundTasks):
    """Start a full analysis from a YouTube / video URL. Returns a job_id to poll."""
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "url must start with http:// or https://")
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(500, "GEMINI_API_KEY is not set on the server.")
    if PIPELINE_LOCK.locked():
        raise HTTPException(409, "Another analysis is already running.")
    job_id = _new_job()
    background.add_task(_run_pipeline, job_id, body.url, body.skip_visual)
    return {"job_id": job_id, "status": "queued"}


@app.post("/analyze/upload", tags=["pipeline"], dependencies=[Depends(check_api_key)])
def analyze_upload(background: BackgroundTasks,
                   file: UploadFile = File(...),
                   skip_visual: bool = Form(False)):
    """Start a full analysis from an uploaded audio/video file."""
    allowed = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".mp3", ".wav", ".m4a"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(allowed)}")
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(500, "GEMINI_API_KEY is not set on the server.")
    if PIPELINE_LOCK.locked():
        raise HTTPException(409, "Another analysis is already running.")
    saved = DOWNLOADS_DIR / Path(file.filename).name
    with open(saved, "wb") as out:
        shutil.copyfileobj(file.file, out)
    # audio-only files have no slides -> skip visual step automatically
    audio_only = ext in {".mp3", ".wav", ".m4a"}
    job_id = _new_job()
    background.add_task(_run_pipeline, job_id, str(saved), skip_visual or audio_only)
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}", tags=["pipeline"], dependencies=[Depends(check_api_key)])
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown job_id (the server may have restarted).")
    return job


def _read(path: Path, what: str) -> str:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        raise HTTPException(404, f"{what} not available yet. Run /analyze first.")
    return path.read_text(encoding="utf-8")


@app.get("/reports/en", tags=["results"], dependencies=[Depends(check_api_key)])
def report_en():
    return {"language": "en", "markdown": _read(EN_FILE, "English report")}


@app.get("/reports/amh", tags=["results"], dependencies=[Depends(check_api_key)])
def report_amh():
    return {"language": "am", "markdown": _read(AMH_FILE, "Amharic report")}


@app.get("/transcript", tags=["results"], dependencies=[Depends(check_api_key)])
def transcript():
    return {"transcript": _read(TRANSCRIPT_FILE, "Transcript"),
            "visual_text": VISUAL_FILE.read_text(encoding="utf-8") if VISUAL_FILE.exists() else ""}


@app.post("/chat", tags=["chat"], dependencies=[Depends(check_api_key)])
def chat(body: ChatRequest):
    """Ask a question (English or Amharic) about the analysed meeting."""
    if not body.question.strip():
        raise HTTPException(400, "question is empty")
    from rag.chat_rag import answer_question
    answer, docs = answer_question(body.question, k=body.k, return_sources=True)
    sources = [{"source": d.metadata.get("source", "meeting record"),
                "text": d.page_content[:400]} for d in docs]
    return {"question": body.question, "answer": answer, "sources": sources}


@app.post("/knowledge-base/rebuild", tags=["pipeline"], dependencies=[Depends(check_api_key)])
def rebuild_kb():
    """Re-index the existing reports without redoing transcription."""
    if PIPELINE_LOCK.locked():
        raise HTTPException(409, "Another analysis is running.")
    from rag.ingest_db import run_ingestion
    try:
        run_ingestion()
    except Exception as e:
        raise HTTPException(500, str(e)[:300])
    return {"status": "rebuilt"}