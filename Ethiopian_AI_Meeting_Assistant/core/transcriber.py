import os
import sys
from pathlib import Path
from faster_whisper import WhisperModel
import yt_dlp

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = PROJECT_DIR / "downloads"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TRANSCRIPT_OUTPUT = OUTPUT_DIR / "transcript.txt"

DENO_EXE = (
    Path(os.environ.get("LOCALAPPDATA", ""))
    / "Microsoft"
    / "WinGet"
    / "Packages"
    / "DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "deno.exe"
)

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_audio_from_youtube(url: str) -> str:
    print(f"📥 Downloading audio from YouTube...", flush=True)
    js_runtimes = {"deno": {"path": str(DENO_EXE)}} if DENO_EXE.is_file() else {}
    
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "js_runtimes": js_runtimes,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(url, download=True)
        video_id = info.get("id")
        audio_path = DOWNLOAD_DIR / f"{video_id}.mp3"
        if audio_path.is_file():
            print(f"✅ Audio downloaded: {audio_path.resolve()}", flush=True)
            return str(audio_path.resolve())

    raise FileNotFoundError("Could not download audio file.")

def transcribe_audio(source: str, output_path: str = str(TRANSCRIPT_OUTPUT)) -> str:
    source = source.strip().strip('"')
    if source.startswith(("http://", "https://")):
        audio_file = download_audio_from_youtube(source)
    else:
        audio_file = source

    audio_path = Path(audio_file)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"🎙️ Loading Whisper model (base)...", flush=True)
    model = WhisperModel("base", device="cpu", compute_type="int8")

    print(f"📝 Transcribing audio stream...", flush=True)
    segments, info = model.transcribe(str(audio_path), beam_size=5)

    results = []
    for segment in segments:
        mins, secs = int(segment.start // 60), int(segment.start % 60)
        line = f"[{mins:02d}:{secs:02d}] {segment.text.strip()}"
        results.append(line)
        print(line, flush=True)

    output_file = Path(output_path)
    if not output_file.is_absolute():
        output_file = PROJECT_DIR / output_file
    output_file.parent.mkdir(parents=True, exist_ok=True)

    content = "\n".join(results)
    output_file.write_text(content, encoding="utf-8")
    print(f"\n✅ Transcript saved to: {output_file.resolve()}", flush=True)
    return str(output_file.resolve())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        transcribe_audio(sys.argv[1])