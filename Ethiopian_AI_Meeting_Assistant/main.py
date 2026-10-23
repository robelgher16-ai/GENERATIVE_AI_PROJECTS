import sys
import os
from pathlib import Path

from core.transcriber import transcribe_audio
from core.video_processor import process_video_input
from core.summarizer import load_multimodal_inputs, generate_bilingual_reports
from rag.ingest_db import run_ingestion
from rag.chat_rag import interactive_chat

OUTPUTS_DIR = Path("outputs")

def run_full_pipeline(source: str):
    print("=" * 60, flush=True)
    print("🚀 PIPELINE STARTED: Unified Audio & Visual Analysis", flush=True)
    print("=" * 60, flush=True)
    
    source = source.strip().strip('"')
    if not source:
        print("❌ Error: No valid source input provided.")
        return

    # 1. Spoken Audio Transcription
    print("\n--- STEP 1: Running Audio Transcription ---", flush=True)
    try:
        transcribe_audio(source)
    except Exception as e:
        print(f"❌ Audio transcription failed: {e}")
        return

    # 2. Visual Frame OCR Extraction
    print("\n--- STEP 2: Running Visual Text Extraction ---", flush=True)
    try:
        process_video_input(source)
    except Exception as e:
        print(f"⚠️ Visual processing encountered an error: {e}")
        print("Continuing pipeline with available transcript data...")

    # 3. Dual-Language Reports
    print("\n--- STEP 3: Generating Bilingual Meeting Intelligence Reports ---", flush=True)
    try:
        raw_data = load_multimodal_inputs()
        english_report, amharic_report = generate_bilingual_reports(raw_data)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        
        en_path = OUTPUTS_DIR / "meeting_notes_en.md"
        en_path.write_text(english_report, encoding="utf-8")
        
        amh_path = OUTPUTS_DIR / "meeting_notes_amh.md"
        amh_path.write_text(amharic_report, encoding="utf-8")

        print(f"\n✨ English report saved to: {en_path.resolve()}", flush=True)
        print(f"✨ Amharic report saved to: {amh_path.resolve()}", flush=True)

    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return

    # 4. RAG Knowledge Base Ingestion
    print("\n--- STEP 4: Building RAG Knowledge Base ---", flush=True)
    try:
        run_ingestion()
    except Exception as e:
        print(f"❌ RAG Ingestion failed: {e}")
        return

    print("\n" + "=" * 60)
    print("🎉 Full Pipeline & RAG Ingestion Completed Successfully!")
    print("=" * 60)

    # 5. Open Interactive Bilingual Chat Session
    interactive_chat()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        source_input = " ".join(sys.argv[1:])
    else:
        source_input = input("Enter YouTube video link or local video path: ").strip()
    
    if source_input:
        run_full_pipeline(source_input)
    else:
        print("❌ No input source provided.")
