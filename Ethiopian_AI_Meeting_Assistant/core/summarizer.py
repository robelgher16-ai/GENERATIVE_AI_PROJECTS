import os
import random
import time
import traceback
from pathlib import Path
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Model chain
# ---------------------------------------------------------------------------
# Stable models first. "gemini-3.8-flash" was returning 503 (high demand), so it
# is no longer first. Override without editing code, e.g. in your .env file:
#   GEMINI_MODELS=gemini-2.5-flash,gemini-3.5-flash
DEFAULT_MODELS = [
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
]

OUTPUTS_DIR = Path("outputs")

# Retry behaviour
PER_MODEL_TRIES = 2        # tries per model before moving to the next one
MAX_ROUNDS = 3             # how many times to sweep the whole chain
ROUND_PAUSE = 12           # seconds to wait between sweeps (multiplied by round number)
REQUEST_TIMEOUT_MS = 180_000  # 3 minutes max per request, so a call can never hang forever

_AVAILABLE_MODELS = None   # cache of model names your API key can actually use
_EXTRAS_ANNOUNCED = False


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY environment variable is not set. Please set your API key.")
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )


def _get_available_models(client):
    """Returns the set of model names available to this API key (or None if it can't be checked)."""
    global _AVAILABLE_MODELS
    if _AVAILABLE_MODELS is not None:
        return _AVAILABLE_MODELS
    try:
        names = set()
        for m in client.models.list():
            names.add(m.name.replace("models/", ""))
        _AVAILABLE_MODELS = names
        return names
    except Exception as e:
        print(f"   ⚠️ Could not list available models ({e}). Will try each model directly.", flush=True)
        return None


def _build_model_chain(client):
    """Preferred models first, then any other text 'flash' models your key can use.
    Built on every call (cheap) so changes to GEMINI_MODELS take effect without restarting."""
    global _EXTRAS_ANNOUNCED

    env_models = os.environ.get("GEMINI_MODELS", "")
    base = [m.strip() for m in env_models.split(",") if m.strip()] or list(DEFAULT_MODELS)
    chain = list(base)
    available = _get_available_models(client)

    if available:
        skip_words = ("image", "tts", "live", "audio", "embedding", "imagen", "veo", "aqa", "robotics", "computer-use")
        extras = sorted(
            name for name in available
            if "flash" in name
            and name not in chain
            and not any(word in name for word in skip_words)
        )
        if extras and not _EXTRAS_ANNOUNCED:
            print(f"   ➕ Added extra models found for your API key: {', '.join(extras)}", flush=True)
            _EXTRAS_ANNOUNCED = True
        chain.extend(extras)

    return chain


def _clean_markdown(text: str) -> str:
    """Removes ```markdown fences that models sometimes wrap around the whole report."""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def _is_transient(err: str) -> bool:
    """Errors that usually disappear if we wait a moment or try another model."""
    markers = (
        "503", "UNAVAILABLE", "overloaded", "high demand",
        "500", "INTERNAL", "504", "DEADLINE_EXCEEDED",
        "429", "RESOURCE_EXHAUSTED",
        "timed out", "timeout", "Timeout", "ConnectError", "ReadError", "RemoteProtocolError",
        "Connection", "disconnected",
    )
    return any(m in err for m in markers)


def generate_with_fallback(client, contents, config=None):
    """Tries many models, several times, with backoff.

    A 503 'high demand' error is temporary and comes from Google's side, so instead of
    giving up after one pass through the models, the whole chain is retried in rounds
    with a growing pause in between."""
    available = _get_available_models(client)
    model_chain = _build_model_chain(client)
    dead = set()   # models that are missing or out of daily quota: skip them in later rounds
    last_error = None

    for round_no in range(1, MAX_ROUNDS + 1):
        if round_no > 1:
            pause = ROUND_PAUSE * (round_no - 1)
            print(f"\n   ⏳ All models busy. Waiting {pause}s, then trying again (round {round_no}/{MAX_ROUNDS})...", flush=True)
            time.sleep(pause)

        for model_name in model_chain:
            if model_name in dead:
                continue
            if available is not None and model_name not in available:
                if round_no == 1:
                    print(f"   ⏭️ Model {model_name} is not available for your API key. Skipping.", flush=True)
                dead.add(model_name)
                continue

            print(f"   🤖 Attempting generation with model: {model_name}... (round {round_no}/{MAX_ROUNDS})", flush=True)

            for attempt in range(1, PER_MODEL_TRIES + 1):
                started = time.time()
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config,
                    )
                    text = getattr(response, "text", None) if response else None
                    if text:
                        print(f"   ✅ Success using {model_name} ({time.time() - started:.0f}s)!", flush=True)
                        return _clean_markdown(text)

                    last_error = "Empty response (possibly blocked by safety filters)"
                    print(f"   ⚠️ {model_name} (try {attempt}/{PER_MODEL_TRIES}) returned an empty response.", flush=True)

                except Exception as e:
                    last_error = e
                    err = str(e)
                    print(f"   ⚠️ {model_name} (try {attempt}/{PER_MODEL_TRIES}, {time.time() - started:.0f}s) failed: {err[:200]}", flush=True)

                    # Bad key / no permission: retrying or switching models won't help
                    if any(code in err for code in ("401", "403", "API_KEY_INVALID", "PERMISSION_DENIED")):
                        raise RuntimeError(f"❌ Authentication problem, check your GEMINI_API_KEY: {e}")

                    # Model doesn't exist: never try it again
                    if "404" in err or "NOT_FOUND" in err:
                        print(f"   🔄 {model_name} not found. Switching to next model...", flush=True)
                        dead.add(model_name)
                        break

                    # Daily quota exhausted: waiting won't help today, never try it again
                    if "RESOURCE_EXHAUSTED" in err and "PerDay" in err:
                        print(f"   🔄 Daily quota used up for {model_name}. Switching to next model...", flush=True)
                        dead.add(model_name)
                        break

                    # Not a temporary problem (e.g. 400 bad request): skip this model
                    if not _is_transient(err):
                        print(f"   🔄 Non-retryable error on {model_name}. Switching to next model...", flush=True)
                        break

                # Short wait before the second try on the same model, with a little randomness
                if attempt < PER_MODEL_TRIES:
                    wait = 3 * attempt + random.uniform(0, 2)
                    print(f"   ⏳ Retrying {model_name} in {wait:.0f}s...", flush=True)
                    time.sleep(wait)
            else:
                print(f"   🔄 Switching to next model...", flush=True)

    raise RuntimeError(
        f"❌ All Gemini models failed after {MAX_ROUNDS} rounds. Last error: {last_error}\n"
        f"   👉 503 means Google's servers are overloaded: just click the button again in a few minutes.\n"
        f"   👉 429 daily quota: wait for the reset, enable billing in Google AI Studio, or use a key from another project."
    )


def load_multimodal_inputs() -> str:
    """Loads both the audio transcript and the visual OCR text into a single unified data context."""
    transcript_path = OUTPUTS_DIR / "transcript.txt"
    visual_path = OUTPUTS_DIR / "visual.txt"

    combined_content = []

    if transcript_path.exists():
        print("📥 Loading spoken audio transcript...", flush=True)
        audio_text = transcript_path.read_text(encoding="utf-8").strip()
        if audio_text:
            combined_content.append(audio_text)

    if visual_path.exists():
        print("📥 Loading visual presentation text...", flush=True)
        visual_text = visual_path.read_text(encoding="utf-8").strip()
        if visual_text:
            combined_content.append(visual_text)

    if not combined_content:
        raise FileNotFoundError(
            "No transcript content found in outputs/. Please ensure transcript.txt or visual.txt contain data."
        )

    return "\n\n".join(combined_content)


def generate_bilingual_reports(meeting_data: str):
    client = get_client()

    # -------------------------------------------------------------
    # 1. GENERATE ENGLISH REPORT
    # -------------------------------------------------------------
    english_prompt = f"""
You are an expert AI technical meeting assistant. Generate a single, highly professional, unified Markdown meeting report from the raw meeting notes provided below.

STRICT INSTRUCTION:
- Do NOT mention "OCR", "Audio", "Transcripts", "Visuals", or "Slides" anywhere in the final report.
- Treat all provided information as ONE cohesive meeting record and synthesize it into clear, thematic sections.
- Output raw Markdown only. Do NOT wrap the report in code fences.

Format the output strictly according to this structure:

# 🚀 Meeting Intelligence Report

> **Summary at a glance:** [One short sentence capturing the overall meeting]

---

## 📌 1. Executive Summary

| | |
|---|---|
| **🎯 Core Objective** | [A concise 2-3 sentence overview of the meeting's primary goal] |
| **⭐ Major Takeaway** | [The single most important conclusion or outcome of the entire session] |

---

## 💡 2. Core Discussion & Key Insights

### 🔹 [Topic 1 Title]
- [Key detail or explanation from the meeting]
- [Supporting point, metric, or example]

### 🔹 [Topic 2 Title]
- [Key detail or explanation from the meeting]
- [Supporting point, metric, or example]

---

## 🎯 3. Key Decisions & Strategic Takeaways

| # | Decision / Takeaway | Context & Explanation |
|---|---|---|
| 1 | **[Key Point / Decision 1]** | [Context and explanation] |
| 2 | **[Key Point / Decision 2]** | [Context and explanation] |

---

## ✅ 4. Action Items & Next Steps

- [ ] **[Task Description 1]** — *Owner:* `@Assignee` | *Timeline:* [Timeframe]
- [ ] **[Task Description 2]** — *Owner:* `@Assignee` | *Timeline:* [Timeframe]

---

*✨ Report compiled automatically by Ethiopian AI Meeting Assistant.*

Here is the raw meeting record:
{meeting_data}

Generate only the final English meeting report:
"""

    print(f"\n🤖 Generating English Meeting Intelligence Report...", flush=True)
    english_report = generate_with_fallback(client, english_prompt)

    # Save the English report right away so it is not lost if the Amharic step fails
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / "meeting_notes_en.md").write_text(english_report, encoding="utf-8")
    print("💾 English report saved to outputs/meeting_notes_en.md", flush=True)

    print("⏳ Pausing 2 seconds before Amharic generation...", flush=True)
    time.sleep(2)

    # -------------------------------------------------------------
    # 2. GENERATE AMHARIC REPORT
    # -------------------------------------------------------------
    amharic_prompt = f"""
You are an expert bilingual AI meeting assistant fluent in Amharic. Based on the raw meeting notes provided below, write a comprehensive, highly professional meeting intelligence report completely written in Amharic (አማርኛ).

STRICT INSTRUCTION:
- Write the entire report natively in professional Amharic (Ge'ez script).
- Do NOT mention "OCR", "Audio", "Transcripts", "Visuals", or "Slides".
- Synthesize all information cohesively into clean thematic sections with proper Markdown tables, bold text, and bullet points.
- Output raw Markdown only. Do NOT wrap the report in code fences.

Format the output strictly according to this structure:

# 🚀 የስብሰባ ማጠቃለያ ሪፖርት (Meeting Intelligence Report)

> **አጠቃላይ ቅኝት:** [ስብሰባውን በአጭር ቃል የሚገልጽ ዓረፍተ ነገር]

---

## 📌 1. ዋና ዋና ሃሳቦች (Executive Summary)

| | |
|---|---|
| **🎯 ዋና ዓላማ** | [የስብሰባው ዋና ግብ እና ጭብጥ በ2-3 ዓረፍተ ነገር] |
| **⭐ ዋና ድምዳሜ** | [ከሰብሰባው የተገኘው በጣም ጠቃሚ ውጤት ወይም ውሳኔ] |

---

## 💡 2. ዋና ዋና ውይይቶች እና ሃሳቦች (Core Discussion & Key Insights)

### 🔹 [ርዕስ 1]
- [ከስብሰባው የተወሰደ ጠቃሚ ዝርዝር ሃሳብ ወይም ማብራሪያ]
- [ደጋፊ ነጥብ ወይም ምሳሌ]

### 🔹 [ርዕስ 2]
- [ከስብሰባው የተወሰደ ጠቃሚ ዝርዝር ሃሳብ ወይም ማብራሪያ]
- [ደጋፊ ነጥብ ወይም ምሳሌ]

---

## 🎯 3. ቁልፍ ውሳኔዎች (Key Decisions)

| ተራ | ውሳኔ / ቁልፍ ነጥብ | ማብራሪያ እና አውድ |
|---|---|---|
| 1 | **[ውሳኔ 1]** | [ማብራሪያ] |
| 2 | **[ውሳኔ 2]** | [ማብራሪያ] |

---

## ✅ 4. ቀጣይ ተግባራት እና እርምጃዎች (Action Items)

- [ ] **[ተግባር 1]** — *ባለቤት:* `@አካል` | *ጊዜ ገደብ:* [ጊዜ]
- [ ] **[ተግባር 2]** — *ባለቤት:* `@አካል` | *ጊዜ ገደብ:* [ጊዜ]

---

*✨ ሪፖርቱ በኢትዮጵያ ኤአይ የስብሰባ ረዳት (Ethiopian AI Meeting Assistant) በራስ-ሰር ተዘጋጀ።*

Here is the raw meeting record to translate, summarize, and structure:
{meeting_data}

Generate only the final Amharic meeting report:
"""

    print(f"\n🤖 Generating Amharic Meeting Intelligence Report (የስብሰባ ሪፖርት በአማርኛ)...", flush=True)
    amharic_report = generate_with_fallback(client, amharic_prompt)

    return english_report, amharic_report


if __name__ == "__main__":
    print("=" * 50, flush=True)
    print("      🎙️    Testing Gemini Multi-Model Fallback", flush=True)
    print("=" * 50 + "\n", flush=True)

    try:
        raw_data = load_multimodal_inputs()
        print(f"📄 Loaded raw data ({len(raw_data)} characters). Processing...", flush=True)
        en_rep, amh_rep = generate_bilingual_reports(raw_data)

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUTS_DIR / "meeting_notes_en.md").write_text(en_rep, encoding="utf-8")
        (OUTPUTS_DIR / "meeting_notes_amh.md").write_text(amh_rep, encoding="utf-8")

        print("\n✅ Success! Reports generated and saved successfully via fallback chain.")
    except Exception as e:
        print(f"\n❌ Summarizer test failed: {e}")
        traceback.print_exc()