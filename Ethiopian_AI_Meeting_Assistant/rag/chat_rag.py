import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import random
import re
import time
from pathlib import Path
from google import genai
from google.genai import types
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# Loads GEMINI_API_KEY from your .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Configuration (paths match ingest_db.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_PATH = PROJECT_ROOT / "outputs" / "chroma_db"

# Stable models first. Override in your .env without editing code, e.g.:
#   GEMINI_MODELS=gemini-2.5-flash,gemini-3.5-flash
DEFAULT_MODELS = [
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
]

# Must be the SAME model used in ingest_db.py
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Retry behaviour (kept shorter than the report step, because a person is waiting in the chat)
PER_MODEL_TRIES = 2
MAX_ROUNDS = 2
ROUND_PAUSE = 6
REQUEST_TIMEOUT_MS = 60_000  # 1 minute max per request

_AVAILABLE_MODELS = None  # cache of model names your API key can use
_EMBEDDING_FUNCTION = None  # the embedding model is loaded once (slow); the database is NOT cached


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY environment variable is not set. Please set your API key.")
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )


def is_amharic(text: str) -> bool:
    """Detects if the query contains Ge'ez/Amharic script characters."""
    geez_pattern = re.compile(r'[\u1200-\u137F]')
    return bool(geez_pattern.search(text))


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
        print(f"   ⚠️ Could not list available models ({str(e)[:150]}). Will try each model directly.", flush=True)
        return None


def _build_model_chain(client):
    """Preferred models first, then any other text 'flash' models your key can use.
    Rebuilt on every call so changes to GEMINI_MODELS apply without restarting."""
    env_models = os.environ.get("GEMINI_MODELS", "")
    chain = [m.strip() for m in env_models.split(",") if m.strip()] or list(DEFAULT_MODELS)
    available = _get_available_models(client)

    if available:
        skip_words = ("image", "tts", "live", "audio", "embedding", "imagen", "veo", "aqa", "robotics", "computer-use")
        extras = sorted(
            name for name in available
            if "flash" in name
            and name not in chain
            and not any(word in name for word in skip_words)
        )
        chain.extend(extras)

    return chain


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


def generate_with_fallback(client, prompt):
    """Executes chat generation with fallback across available Gemini models.
    Tries the whole model list in rounds, because 503 'high demand' errors are temporary."""
    available = _get_available_models(client)
    model_chain = _build_model_chain(client)
    dead = set()  # missing models or models with no daily quota left
    last_error = None

    for round_no in range(1, MAX_ROUNDS + 1):
        if round_no > 1:
            pause = ROUND_PAUSE * (round_no - 1)
            print(f"   ⏳ All models busy. Waiting {pause}s, then trying again...", flush=True)
            time.sleep(pause)

        for model_name in model_chain:
            if model_name in dead:
                continue
            if available is not None and model_name not in available:
                dead.add(model_name)
                continue

            for attempt in range(1, PER_MODEL_TRIES + 1):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    text = getattr(response, "text", None) if response else None
                    if text:
                        return text
                    last_error = "Empty response (possibly blocked by safety filters)"
                except Exception as e:
                    last_error = e
                    err = str(e)
                    print(f"   ⚠️ {model_name} (try {attempt}/{PER_MODEL_TRIES}) failed: {err[:200]}", flush=True)

                    # Bad key / no permission: nothing else will work
                    if any(code in err for code in ("401", "403", "API_KEY_INVALID", "PERMISSION_DENIED")):
                        return "❌ Authentication problem. Please check your GEMINI_API_KEY."

                    # Model doesn't exist: never try it again
                    if "404" in err or "NOT_FOUND" in err:
                        dead.add(model_name)
                        break

                    # Daily quota used up: never try it again today
                    if "RESOURCE_EXHAUSTED" in err and "PerDay" in err:
                        print(f"   🔄 Daily quota used up for {model_name}. Trying next model...", flush=True)
                        dead.add(model_name)
                        break

                    # Not temporary (e.g. 400 bad request): skip this model
                    if not _is_transient(err):
                        break

                if attempt < PER_MODEL_TRIES:
                    time.sleep(2 * attempt + random.uniform(0, 1.5))

    err_text = str(last_error) if last_error else ""
    if "RESOURCE_EXHAUSTED" in err_text and "PerDay" in err_text:
        return ("I'm sorry, your Gemini API daily quota is used up for all available models. "
                "Please wait for the quota to reset, enable billing, or use a different API key.")
    if "503" in err_text or "UNAVAILABLE" in err_text or "high demand" in err_text:
        return ("⚠️ Google's Gemini servers are overloaded right now (503). "
                "This is temporary. Please wait a minute and ask the question again.")
    return f"I'm sorry, I could not generate an answer right now. Last error: {err_text[:300] or 'unknown'}"


def _get_embedding_function():
    """Loads the embedding model once and reuses it (loading is slow)."""
    global _EMBEDDING_FUNCTION
    if _EMBEDDING_FUNCTION is None:
        _EMBEDDING_FUNCTION = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    return _EMBEDDING_FUNCTION


def get_vector_store():
    """Opens the ChromaDB database FRESH every time it is called.
    This way the chat always sees the newest data, even right after 'Rebuild knowledge base'
    (an old cached connection would point to the deleted collection and fail)."""
    return Chroma(
        persist_directory=str(CHROMA_PATH),
        embedding_function=_get_embedding_function(),
    )


def knowledge_base_ready() -> bool:
    """True if the database folder exists (ingestion has been run)."""
    return CHROMA_PATH.exists()


def _retrieve(vector_store, query: str, k: int = 6):
    """Retrieves relevant chunks. Amharic questions search the Amharic report first,
    because the embedding model is English-focused."""
    if is_amharic(query):
        try:
            docs = vector_store.similarity_search(query, k=k, filter={"language": "am"})
            if docs:
                return docs
        except Exception as e:
            print(f"   ⚠️ Amharic-filtered search failed ({str(e)[:150]}). Searching all records...", flush=True)
    return vector_store.similarity_search(query, k=k)


def _build_prompt(query: str, retrieved_docs) -> str:
    """Builds the prompt sent to Gemini from the question and the retrieved chunks."""
    context_blocks = []
    for idx, doc in enumerate(retrieved_docs, start=1):
        source = doc.metadata.get("source", "meeting record")
        context_blocks.append(f"[Source {idx} ({source})]:\n{doc.page_content}")
    context_str = "\n\n".join(context_blocks)

    # Match response language with question language
    if is_amharic(query):
        system_instruction = """
እርስዎ የኢትዮጵያ ኤአይ የስብሰባ ረዳት ነዎት። ከተሰጠው የስብሰባ መረጃ (Context) ብቻ በመነሳት ለተጠየቀው ጥያቄ በግልጽ፣ በአጭሩ እና በሙያዊ አማርኛ መልስ ይስጡ።
መረጃው በስብሰባው ማጠቃለያ ውስጥ ከሌለ "ይህ መረጃ በስብሰባው ማጠቃለያ ውስጥ አልተጠቀሰም።" ብለው ይመልሱ።
"""
    else:
        system_instruction = """
You are an expert AI meeting assistant. Answer the user's question accurately based ONLY on the provided meeting context.
Be concise, professional, and clear. If the answer cannot be found in the context, explicitly state "This information was not discussed in the meeting records."
"""

    return f"""
{system_instruction}

--- RETRIEVED MEETING CONTEXT ---
{context_str}

--- USER QUESTION ---
{query}

--- ANSWER ---
"""


def answer_question(query: str, k: int = 6, return_sources: bool = False):
    """Answers one question from the indexed meeting records.
    Use this from app.py (Streamlit) or any other code.

    Returns the answer text. If return_sources=True, returns (answer_text, source_chunks)."""
    query = (query or "").strip()
    if not query:
        msg = "Please type a question."
        return (msg, []) if return_sources else msg

    if not knowledge_base_ready():
        msg = "⚠️ The knowledge base is not built yet. Please click 'Rebuild knowledge base' first."
        return (msg, []) if return_sources else msg

    try:
        client = get_client()
    except ValueError as e:
        return (str(e), []) if return_sources else str(e)

    try:
        vector_store = get_vector_store()
        retrieved_docs = _retrieve(vector_store, query, k=k)
    except Exception as e:
        msg = f"❌ Could not search the knowledge base: {str(e)[:300]}. Try clicking 'Rebuild knowledge base'."
        return (msg, []) if return_sources else msg

    if not retrieved_docs:
        msg = "⚠️ No relevant meeting content found in database."
        return (msg, []) if return_sources else msg

    prompt = _build_prompt(query, retrieved_docs)
    answer = generate_with_fallback(client, prompt)
    return (answer, retrieved_docs) if return_sources else answer


def interactive_chat():
    """Runs an interactive CLI chat interface over the indexed meeting intelligence database."""
    if not CHROMA_PATH.exists():
        print(f"❌ Database folder '{CHROMA_PATH}' not found. Please run ingestion first (`python rag/ingest_db.py`).")
        return

    print("=" * 60, flush=True)
    print("      💬   Ethiopian AI Meeting Assistant — RAG Chat", flush=True)
    print("=" * 60, flush=True)
    print("Type your questions below (supports English & Amharic/አማርኛ).")
    print("Type 'exit' or 'quit' to end the session.\n", flush=True)

    while True:
        try:
            query = input("\n❓ Your Question / ጥያቄ: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("👋 Exiting chat session. Goodbye!")
                break

            print("🔍 Searching meeting records and generating answer...", flush=True)
            answer = answer_question(query)

            print("\n------------------------------------------------------------")
            print("💡 Answer / መልስ:\n")
            print(answer)
            print("------------------------------------------------------------")

        except KeyboardInterrupt:
            print("\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Chat Error: {e}")


if __name__ == "__main__":
    interactive_chat()