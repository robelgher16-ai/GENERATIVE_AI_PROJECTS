
import os
import sys
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Resolve project paths independently of the current working directory.
PROJECT_ROOT = Path(__file__).resolve().parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

os.chdir(PROJECT_ROOT)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env locally if python-dotenv is installed.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# Configure Tesseract for both local Windows and Render/Linux environments.
# On Render, install tesseract-ocr in the Docker image.
try:
    import pytesseract

    tesseract_env = os.environ.get("TESSERACT_CMD")
    tesseract_path = tesseract_env or shutil.which("tesseract")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
except ImportError:
    pytesseract = None

from core.transcriber import transcribe_audio
from core.video_processor import process_video_input, initialize_ocr
from core.summarizer import load_multimodal_inputs, generate_bilingual_reports
from rag.ingest_db import run_ingestion
from rag.chat_rag import answer_question, knowledge_base_ready

app = FastAPI(
    title="Ethiopian AI Meeting Assistant API",
    description=(
        "API for audio transcription, video OCR, bilingual meeting reports, "
        "knowledge-base ingestion, and meeting Q&A in English and Amharic."
    ),
    version="1.0.0",
)

# For production, set FRONTEND_ORIGIN to your deployed Streamlit URL.
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origin.split(",") if origin.strip()],
    allow_credentials=False if frontend_origin == "*" else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SourceRequest(BaseModel):
    source: str = Field(..., min_length=1, description="A public URL or a file path available to the API server")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about processed meeting records")
    k: int = Field(default=6, ge=1, le=20)


def _safe_upload_name(filename: Optional[str]) -> str:
    """Keep only the basename to prevent path traversal from uploaded filenames."""
    name = Path(filename or "upload.bin").name
    return name.replace("/", "_").replace("\\", "_")


def _save_upload(upload: UploadFile) -> Path:
    name = _safe_upload_name(upload.filename)
    destination = DOWNLOADS_DIR / name
    # Avoid overwriting a previous upload with the same name.
    if destination.exists():
        destination = DOWNLOADS_DIR / f"{destination.stem}_{os.getpid()}{destination.suffix}"
    with destination.open("wb") as output:
        shutil.copyfileobj(upload.file, output)
    return destination


@app.on_event("startup")
def startup_checks():
    """Initialize OCR when possible; don't prevent API startup if OCR is unavailable."""
    try:
        initialize_ocr()
    except Exception as exc:
        print(f"OCR initialization warning: {exc}", flush=True)


@app.get("/")
def root():
    return {
        "message": "Ethiopian AI Meeting Assistant API is running.",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "Ethiopian AI Meeting Assistant",
        "gemini_api_key_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "knowledge_base_ready": knowledge_base_ready(),
        "tesseract_available": bool(shutil.which("tesseract") or os.environ.get("TESSERACT_CMD")),
    }


@app.post("/transcribe")
def transcribe(request: SourceRequest):
    """Transcribe a URL or a file path that exists on the API server."""
    try:
        result_path = transcribe_audio(request.source.strip())
        transcript_path = Path(result_path)
        transcript_text = (
            transcript_path.read_text(encoding="utf-8")
            if transcript_path.exists()
            else None
        )
        return {
            "status": "success",
            "transcript_path": str(transcript_path),
            "transcript": transcript_text,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc


@app.post("/transcribe-upload")
def transcribe_upload(file: UploadFile = File(...)):
    """Upload an audio file and transcribe it."""
    saved_path = None
    try:
        saved_path = _save_upload(file)
        result_path = transcribe_audio(str(saved_path))
        transcript_path = Path(result_path)
        transcript_text = (
            transcript_path.read_text(encoding="utf-8")
            if transcript_path.exists()
            else None
        )
        return {
            "status": "success",
            "uploaded_file": saved_path.name,
            "transcript_path": str(transcript_path),
            "transcript": transcript_text,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Uploaded-audio transcription failed: {exc}") from exc
    finally:
        file.file.close()


@app.post("/process-video")
def process_video(request: SourceRequest):
    """Download/process a public video URL or process a server-local video path."""
    try:
        output_path = process_video_input(request.source.strip())
        output_file = Path(output_path)
        text = output_file.read_text(encoding="utf-8") if output_file.exists() else None
        return {
            "status": "success",
            "visual_text_path": str(output_file),
            "visual_text": text,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video processing failed: {exc}") from exc


@app.post("/process-video-upload")
def process_video_upload(file: UploadFile = File(...)):
    """Upload a video file and extract on-screen text with OCR."""
    try:
        saved_path = _save_upload(file)
        output_path = process_video_input(str(saved_path))
        output_file = Path(output_path)
        text = output_file.read_text(encoding="utf-8") if output_file.exists() else None
        return {
            "status": "success",
            "uploaded_file": saved_path.name,
            "visual_text_path": str(output_file),
            "visual_text": text,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Uploaded-video processing failed: {exc}") from exc
    finally:
        file.file.close()


@app.post("/generate-reports")
def generate_reports():
    """Generate English and Amharic reports from the current transcript/visual files."""
    try:
        meeting_data = load_multimodal_inputs()
        if not meeting_data.strip():
            raise HTTPException(
                status_code=400,
                detail="No meeting transcript or visual text found. Process audio or video first.",
            )

        english_report, amharic_report = generate_bilingual_reports(meeting_data)
        return {
            "status": "success",
            "english_report": english_report,
            "amharic_report": amharic_report,
            "english_report_path": str(OUTPUTS_DIR / "meeting_notes_en.md"),
            "amharic_report_path": str(OUTPUTS_DIR / "meeting_notes_amh.md"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}") from exc


@app.post("/ingest")
def ingest():
    """Build/rebuild the ChromaDB knowledge base from generated meeting reports."""
    try:
        result = run_ingestion()
        return {
            "status": "success",
            "message": "Knowledge-base ingestion finished.",
            "result": str(result) if result is not None else None,
            "knowledge_base_ready": knowledge_base_ready(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge-base ingestion failed: {exc}") from exc


@app.post("/chat")
def chat(request: ChatRequest):
    """Answer a question using the indexed meeting records."""
    try:
        answer, docs = answer_question(
            request.question.strip(),
            k=request.k,
            return_sources=True,
        )
        sources = [
            {
                "source": doc.metadata.get("source", "meeting record"),
                "language": doc.metadata.get("language"),
                "content": doc.page_content,
            }
            for doc in docs
        ]
        return {
            "status": "success",
            "question": request.question,
            "answer": answer,
            "sources": sources,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chat request failed: {exc}") from exc
