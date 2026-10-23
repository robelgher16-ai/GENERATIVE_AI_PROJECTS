import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import gc
import os
import shutil
import stat
import time
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# Paths are built from this file's location so they work from any terminal folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
CHROMA_PATH = OUTPUTS_DIR / "chroma_db"

# IMPORTANT: ingest_db.py and chat_rag.py must use the SAME embedding model.
# If you change it, run ingest_db.py again to rebuild the database.
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def _remove_readonly(func, path, _exc_info):
    """Helps shutil.rmtree delete read-only files on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _release_chroma_handles():
    """Asks ChromaDB to let go of any open connection to the database files
    (Windows refuses to delete files that are still open)."""
    try:
        try:
            from chromadb.api.shared_system_client import SharedSystemClient
        except ImportError:
            from chromadb.api.client import SharedSystemClient
        SharedSystemClient.clear_system_cache()
    except Exception:
        pass
    gc.collect()


def _reset_database(embedding_function):
    """Empties the old database so a fresh one can be built.

    1) Preferred: delete the old collection through ChromaDB itself. No files are deleted,
       so it works even when Windows or Streamlit still has the folder open.
    2) Fallback: release the handles and delete the folder.
    """
    if not CHROMA_PATH.exists():
        return

    print(f"🧹 Clearing previous database at {CHROMA_PATH}...", flush=True)

    try:
        old_store = Chroma(
            persist_directory=str(CHROMA_PATH),
            embedding_function=embedding_function,
        )
        old_store.delete_collection()
        del old_store
        _release_chroma_handles()
        print("   ✅ Old collection removed.", flush=True)
        return
    except Exception as e:
        print(f"   ⚠️ Could not clear the old collection ({str(e)[:150]}). Trying to delete the folder...", flush=True)

    _release_chroma_handles()
    for attempt in range(1, 4):
        shutil.rmtree(CHROMA_PATH, onerror=_remove_readonly)
        if not CHROMA_PATH.exists():
            print("   ✅ Old database folder deleted.", flush=True)
            return
        print(f"   ⏳ Folder still in use (try {attempt}/3). Waiting...", flush=True)
        time.sleep(2)
        _release_chroma_handles()

    raise PermissionError(
        f"❌ Could not clear the old database at '{CHROMA_PATH}'. "
        "Stop Streamlit (Ctrl+C), delete the 'outputs/chroma_db' folder by hand, "
        "start the app again and click 'Rebuild knowledge base'."
    )


def run_ingestion():
    """Reads generated meeting notes from outputs/ and builds a persistent ChromaDB vector store."""
    print("=" * 60, flush=True)
    print("      📚   Starting RAG Document Ingestion & Indexing", flush=True)
    print("=" * 60 + "\n", flush=True)

    en_file = OUTPUTS_DIR / "meeting_notes_en.md"
    amh_file = OUTPUTS_DIR / "meeting_notes_amh.md"

    documents = []

    # Load English meeting notes if available
    if en_file.exists() and en_file.read_text(encoding="utf-8").strip():
        print(f"📥 Loading English report: {en_file}", flush=True)
        loader_en = TextLoader(str(en_file), encoding="utf-8")
        docs_en = loader_en.load()
        for doc in docs_en:
            doc.metadata["language"] = "en"
            doc.metadata["source"] = "meeting_notes_en.md"
        documents.extend(docs_en)
    else:
        print(f"⚠️ Warning: {en_file} not found or empty.", flush=True)

    # Load Amharic meeting notes if available
    if amh_file.exists() and amh_file.read_text(encoding="utf-8").strip():
        print(f"📥 Loading Amharic report: {amh_file}", flush=True)
        loader_amh = TextLoader(str(amh_file), encoding="utf-8")
        docs_amh = loader_amh.load()
        for doc in docs_amh:
            doc.metadata["language"] = "am"
            doc.metadata["source"] = "meeting_notes_amh.md"
        documents.extend(docs_amh)
    else:
        print(f"⚠️ Warning: {amh_file} not found or empty.", flush=True)

    if not documents:
        raise FileNotFoundError(
            "❌ No report files found in outputs/ to index. Please run the summarizer first (python core/summarizer.py)."
        )

    # Split documents into chunks for embedding
    print("✂️ Chunking documents into context blocks...", flush=True)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 Created {len(chunks)} text chunks from input reports.", flush=True)

    # Generate embeddings locally using FastEmbed (CPU efficient, no API call needed).
    # This is created BEFORE clearing the old database, so if the model fails to load,
    # your existing database is not destroyed.
    print("🧠 Loading embedding model...", flush=True)
    embedding_function = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)

    # Clear the old database (safe on Windows)
    _reset_database(embedding_function)

    print("🧠 Generating embeddings and storing in ChromaDB...", flush=True)
    CHROMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=str(CHROMA_PATH)
    )

    print(f"✅ Ingestion complete! Successfully indexed {len(chunks)} chunks into ChromaDB at '{CHROMA_PATH}'.\n", flush=True)

    # Let go of the build connection so the chat opens the new database cleanly
    del vector_store
    _release_chroma_handles()
    return None


if __name__ == "__main__":
    try:
        run_ingestion()
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")