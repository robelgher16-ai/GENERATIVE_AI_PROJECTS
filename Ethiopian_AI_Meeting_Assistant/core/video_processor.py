
import os
import sys
import shutil
from pathlib import Path

import cv2
import yt_dlp
import pytesseract
from PIL import Image


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "downloads"
OUTPUT_DIR = PROJECT_DIR / "outputs"
VISUAL_OUTPUT = OUTPUT_DIR / "visual.txt"

if os.environ.get("TESSERACT_CMD"):
    TESSERACT_EXE = Path(os.environ["TESSERACT_CMD"])
elif os.name == "nt":
    TESSERACT_EXE = Path(
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
else:
    TESSERACT_EXE = Path("/usr/bin/tesseract")

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


# ============================================================
# 2. INITIALIZE OCR
# ============================================================

def initialize_ocr():
    global OCR_AVAILABLE

    if TESSERACT_EXE.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_EXE)
        OCR_AVAILABLE = True
        print("✅ Tesseract OCR ready.", flush=True)
    elif shutil.which("tesseract"):
        pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")
        OCR_AVAILABLE = True
        print("✅ Tesseract OCR ready.", flush=True)
    else:
        OCR_AVAILABLE = False
        print(
            "⚠️ Tesseract not found. Check your system packages.",
            flush=True,
        )


# ============================================================
# 3. DOWNLOAD YOUTUBE VIDEO
# ============================================================

def download_youtube_video(url: str) -> str:
    print(f"\n📥 Downloading video: {url}", flush=True)

    js_runtimes = (
        {"deno": {"path": str(DENO_EXE)}}
        if DENO_EXE.is_file()
        else {}
    )

    options = {
        "format": "best[ext=mp4]/best",
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "retries": 3,
        "extractor_retries": 3,
        "fragment_retries": 3,
        "force_ipv4": True,
        "js_runtimes": js_runtimes,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=True)
            filename = Path(downloader.prepare_filename(info))

        # The actual downloaded extension may vary by format.
        if filename.is_file():
            video_file = filename
        else:
            candidates = [
                DOWNLOAD_DIR / f"{info['id']}.mp4",
                DOWNLOAD_DIR / f"{info['id']}.mkv",
                DOWNLOAD_DIR / f"{info['id']}.webm",
            ]
            video_file = next(
                (candidate for candidate in candidates if candidate.is_file()),
                None,
            )

        if video_file is None:
            raise FileNotFoundError(
                "yt-dlp finished but the downloaded video file was not found."
            )

        print(f"✅ Download complete: {video_file.resolve()}", flush=True)
        return str(video_file.resolve())

    except Exception as exc:
        raise RuntimeError(
            "YouTube video download failed. Check the yt-dlp logs; "
            "YouTube may restrict downloads from the cloud server. "
            f"Details: {exc}"
        ) from exc


# ============================================================
# 4. EXTRACT FRAMES AND TEXT
# ============================================================

def extract_frames_and_text(
    video_path: str,
    output_path: str = str(VISUAL_OUTPUT),
) -> str:
    if not OCR_AVAILABLE:
        initialize_ocr()

    if not OCR_AVAILABLE:
        raise RuntimeError(
            "Tesseract OCR is unavailable. Install Tesseract and its "
            "English language data."
        )

    video_file = Path(video_path).expanduser().resolve()

    if not video_file.is_file():
        raise FileNotFoundError(f"Video file not found: {video_file}")

    print(
        f"\n⚡ Processing visual text from: {video_file.name}",
        flush=True,
    )

    cap = cv2.VideoCapture(str(video_file))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_file}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0 or frame_count <= 0:
            raise RuntimeError(
                "Could not determine video duration or frame rate."
            )

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
            frame_number = min(
                int(timestamp * fps),
                frame_count - 1,
            )

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            success, frame = cap.read()

            if not success or frame is None:
                continue

            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.threshold(
                    gray,
                    0,
                    255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU,
                )[1]

                text = pytesseract.image_to_string(
                    Image.fromarray(gray),
                    lang="eng",
                    config="--oem 1 --psm 6",
                )

                cleaned = " ".join(text.split())

                if (
                    len(cleaned) >= MIN_TEXT_LENGTH
                    and cleaned.lower() not in seen_text
                ):
                    seen_text.add(cleaned.lower())

                    mins = int(timestamp // 60)
                    secs = int(timestamp % 60)

                    results.append(
                        f"[{mins:02d}:{secs:02d}] {cleaned}"
                    )

                    print(
                        f"[{index}/{len(timestamps)}] "
                        f"Captured text at [{mins:02d}:{secs:02d}]",
                        flush=True,
                    )

            except Exception as exc:
                print(f"⚠️ OCR error on frame {index}: {exc}", flush=True)

        output_file = Path(output_path).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        content = (
            "\n\n".join(results)
            if results
            else "[No significant text detected]"
        )

        output_file.write_text(content, encoding="utf-8")

        print(
            f"\n✅ Visual transcript saved to: {output_file}",
            flush=True,
        )

        return str(output_file)

    finally:
        cap.release()


# ============================================================
# 5. PROCESS VIDEO INPUT
# ============================================================

def process_video_input(source: str) -> str:
    source = source.strip().strip('"')

    if not source:
        raise ValueError("Please provide a YouTube URL or local video path.")

    if source.startswith(("http://", "https://")):
        video_path = download_youtube_video(source)
    else:
        video_path = source

    return extract_frames_and_text(video_path)


# ============================================================
# 6. RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    initialize_ocr()

    source_input = (
        sys.argv[1]
        if len(sys.argv) > 1
        else input("Enter YouTube URL or local path: ").strip()
    )

    if source_input:
        try:
            result = process_video_input(source_input)
            print(f"✅ Processing complete: {result}", flush=True)
        except Exception as exc:
            print(f"❌ Processing failed: {exc}", flush=True)
            raise SystemExit(1)
