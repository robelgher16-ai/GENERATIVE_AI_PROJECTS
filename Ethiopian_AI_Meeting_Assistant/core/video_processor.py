import os
import sys
import re
from pathlib import Path

import cv2
import yt_dlp
import pytesseract
from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "downloads"
OUTPUT_DIR = PROJECT_DIR / "outputs"
VISUAL_OUTPUT = OUTPUT_DIR / "visual.txt"

TESSERACT_EXE = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
DENO_EXE = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Microsoft"
    / "WinGet"
    / "Packages"
    / "DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "deno.exe"
)

FRAME_INTERVAL_SECONDS = 15
MIN_TEXT_LENGTH = 3

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OCR_AVAILABLE = False

def initialize_ocr():
    global OCR_AVAILABLE
    if TESSERACT_EXE.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)
        OCR_AVAILABLE = True
        print(f"✅ OCR Ready.", flush=True)

def download_youtube_video(url: str) -> str:
    print(f"\n📥 Downloading video: {url}", flush=True)
    js_runtimes = {"deno": {"path": str(DENO_EXE)}} if DENO_EXE.is_file() else {}
    
    # Robust options using standard client player strategies (no cookie locking issues)
    options = {
        "format": "bv*+ba/b",
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "js_runtimes": js_runtimes,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        filename = downloader.prepare_filename(info)
        base, _ = os.path.splitext(filename)
        mp4_file = Path(base + ".mp4")
        if mp4_file.is_file():
            print(f"✅ Download complete: {mp4_file.resolve()}", flush=True)
            return str(mp4_file.resolve())
            
    raise FileNotFoundError("Download failed.")

def extract_frames_and_text(video_path: str, output_path: str = str(VISUAL_OUTPUT)) -> str:
    video_file = Path(video_path).expanduser().resolve()
    print(f"\n⚡ Fast processing visual text for: {video_file.name}", flush=True)

    cap = cv2.VideoCapture(str(video_file))
    if not cap.isOpened():
        raise RuntimeError("Could not open video file.")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0 or frame_count <= 0:
            fps = 30
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 300)

        duration = frame_count / fps
        
        timestamps = []
        sec = 0.0
        while sec < duration:
            timestamps.append(sec)
            sec += FRAME_INTERVAL_SECONDS

        print(f"⚡ Total sample points: {len(timestamps)}", flush=True)

        results = []
        seen_text = set()

        for index, timestamp in enumerate(timestamps, start=1):
            frame_number = min(int(timestamp * fps), frame_count - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            success, frame = cap.read()

            if not success or frame is None:
                continue

            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                text = pytesseract.image_to_string(Image.fromarray(gray), lang="eng", config="--oem 1 --psm 6")
                
                cleaned = " ".join(text.split())
                if len(cleaned) >= MIN_TEXT_LENGTH and cleaned.lower() not in seen_text:
                    seen_text.add(cleaned.lower())
                    mins, secs = int(timestamp // 60), int(timestamp % 60)
                    results.append(f"[{mins:02d}:{secs:02d}] {cleaned}")
                    print(f"[{index}/{len(timestamps)}] Captured text at [{mins:02d}:{secs:02d}]", flush=True)
            except Exception:
                continue

        output_file = Path(output_path)
        content = "\n\n".join(results) if results else "[No significant text detected]"
        output_file.write_text(content, encoding="utf-8")
        print(f"\n✅ Visual transcript saved to: {output_file.resolve()}", flush=True)
        return str(output_file.resolve())
    finally:
        cap.release()

def process_video_input(source: str) -> str:
    source = source.strip().strip('"')
    video_path = download_youtube_video(source) if source.startswith(("http://", "https://")) else source
    return extract_frames_and_text(video_path)

if __name__ == "__main__":
    initialize_ocr()
    source_input = sys.argv[1] if len(sys.argv) > 1 else input("Enter YouTube URL or local path: ").strip()
    if source_input:
        process_video_input(source_input)
