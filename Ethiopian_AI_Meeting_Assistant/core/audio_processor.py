
import os
import shutil
import subprocess
from pathlib import Path

import yt_dlp


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "downloads"
OUTPUT_DIR = PROJECT_DIR / "outputs"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. CHECK FFMPEG
# ============================================================

def get_ffmpeg_path() -> str:
    """Return the FFmpeg executable path or raise a clear error."""
    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg was not found. Install FFmpeg and ensure it is "
            "available on PATH. On Streamlit Cloud, add ffmpeg "
            "to packages.txt."
        )

    return ffmpeg_path


# ============================================================
# 3. DOWNLOAD YOUTUBE AUDIO
# ============================================================

def download_youtube_audio(url: str) -> str:
    """Download YouTube audio and return the resulting WAV path."""
    get_ffmpeg_path()

    print("📥 Downloading audio from YouTube...", flush=True)

    output_template = str(DOWNLOAD_DIR / "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "retries": 3,
        "extractor_retries": 3,
        "fragment_retries": 3,
        "force_ipv4": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"],
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as downloader:
            info = downloader.extract_info(url, download=True)
            prepared_path = Path(downloader.prepare_filename(info))
            wav_path = prepared_path.with_suffix(".wav")

        if not wav_path.is_file():
            raise FileNotFoundError(
                f"Expected WAV file was not created: {wav_path}"
            )

        print(f"✅ Audio downloaded: {wav_path}", flush=True)
        return str(wav_path.resolve())

    except Exception as exc:
        raise RuntimeError(
            "YouTube audio download failed. YouTube may be blocking "
            "the cloud server or yt-dlp may need an update. "
            f"Details: {exc}"
        ) from exc


# ============================================================
# 4. CONVERT LOCAL AUDIO OR VIDEO TO WAV
# ============================================================

def convert_to_wav(input_path: str) -> str:
    """Convert a local media file to 16 kHz, mono, PCM WAV."""
    ffmpeg = get_ffmpeg_path()
    source_path = Path(input_path).expanduser().resolve()

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Input audio/video file does not exist: {source_path}"
        )

    output_path = source_path.with_name(
        f"{source_path.stem}_converted.wav"
    )

    command = [
        ffmpeg,
        "-y",
        "-i", str(source_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if result.returncode != 0 or not output_path.is_file():
        raise RuntimeError(
            "FFmpeg failed to convert the input file: "
            f"{result.stderr[-2000:]}"
        )

    print(f"✅ Converted audio: {output_path}", flush=True)
    return str(output_path.resolve())


# ============================================================
# 5. SPLIT AUDIO INTO CHUNKS
# ============================================================

def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list[str]:
    """Split a WAV file into sequential chunks using FFmpeg."""
    ffmpeg = get_ffmpeg_path()
    source_path = Path(wav_path).expanduser().resolve()

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Audio file does not exist: {source_path}"
        )

    if chunk_minutes < 1:
        raise ValueError("chunk_minutes must be at least 1.")

    # Read duration using FFmpeg's companion tool, ffprobe.
    ffprobe = shutil.which("ffprobe")

    if not ffprobe:
        raise RuntimeError(
            "ffprobe was not found. Install FFmpeg with ffprobe available."
        )

    probe_command = [
        ffprobe,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(source_path),
    ]

    probe = subprocess.run(
        probe_command,
        capture_output=True,
        text=True,
        check=False,
    )

    if probe.returncode != 0:
        raise RuntimeError(
            f"Could not read audio duration: {probe.stderr[-1000:]}"
        )

    try:
        duration_seconds = float(probe.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("Invalid audio duration returned by ffprobe.") from exc

    if duration_seconds <= 0:
        raise RuntimeError("The audio file has no usable duration.")

    chunk_seconds = chunk_minutes * 60
    chunks = []
    start = 0.0
    index = 0

    while start < duration_seconds:
        chunk_path = source_path.with_name(
            f"{source_path.stem}_chunk_{index}.wav"
        )

        command = [
            ffmpeg,
            "-y",
            "-ss", str(start),
            "-i", str(source_path),
            "-t", str(chunk_seconds),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(chunk_path),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if result.returncode != 0 or not chunk_path.is_file():
            raise RuntimeError(
                f"Failed to create audio chunk {index}: "
                f"{result.stderr[-1500:]}"
            )

        chunks.append(str(chunk_path.resolve()))
        print(f"🎧 Created chunk {index + 1}: {chunk_path.name}", flush=True)

        start += chunk_seconds
        index += 1

    print(f"✅ Audio ready — {len(chunks)} chunk(s) created.", flush=True)
    return chunks


# ============================================================
# 6. PROCESS INPUT
# ============================================================

def process_input(source: str) -> list[str]:
    """Download or convert media, then split the resulting WAV."""
    source = source.strip().strip('"')

    if not source:
        raise ValueError("Please provide a YouTube URL or local file path.")

    if source.startswith(("http://", "https://")):
        print("Detected YouTube URL.", flush=True)
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local audio/video file.", flush=True)
        wav_path = convert_to_wav(source)

    print("✂️ Chunking audio...", flush=True)
    return chunk_audio(wav_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python core/audio_processor.py "
            "<YouTube URL or local media path>"
        )
        raise SystemExit(1)

    try:
        audio_chunks = process_input(sys.argv[1])
        print("\nGenerated chunks:")
        for chunk in audio_chunks:
            print(chunk)
    except Exception as exc:
        print(f"❌ Audio processing failed: {exc}", flush=True)
        raise SystemExit(1)
