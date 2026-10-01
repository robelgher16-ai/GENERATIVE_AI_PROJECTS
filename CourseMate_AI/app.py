import logging
import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)


# --------------------------------------------------
# Setup
# --------------------------------------------------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("coursemate")


# --------------------------------------------------
# Configuration
# Must match create_database.py
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

CHROMA_DIR = str(
    BASE_DIR / "chroma_db"
)

COLLECTION_NAME = "coursemate_gemini"

EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001",
)

CHAT_MODEL = os.getenv(
    "GEMINI_CHAT_MODEL",
    "gemini-3.8-flash",
)


# --------------------------------------------------
# Retriever Configuration
# --------------------------------------------------

RETRIEVER_K = 4
RETRIEVER_FETCH_K = 10
RETRIEVER_LAMBDA = 0.5


# --------------------------------------------------
# Application Messages
# --------------------------------------------------

NOT_FOUND_ANSWER = (
    "I could not find the answer in the document."
)


# --------------------------------------------------
# Prompt
# --------------------------------------------------

SYSTEM_PROMPT = """You are a helpful AI learning assistant.

Use ONLY the provided context to answer the question.

Do not use outside knowledge.

If the answer is not present in the context,
say:

"I could not find the answer in the document."

Give clear and educational explanations
when the answer is available in the context.
"""


HUMAN_PROMPT = """Context:

{context}

Question:

{question}
"""


# --------------------------------------------------
# Custom Exceptions
# --------------------------------------------------

class SetupError(Exception):
    """Raised for setup problems safe to show to users."""


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="CourseMate AI",
    page_icon="📚",
    layout="wide",
)


# --------------------------------------------------
# Custom Styling
# --------------------------------------------------

st.markdown(
    """
    <style>

        .block-container {
            max-width: 900px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .cm-title {
            text-align: center;
            font-size: clamp(1.8rem, 5vw, 2.6rem);
            font-weight: 700;
            margin-bottom: 0;
        }

        .cm-tagline {
            text-align: center;
            font-size: clamp(1rem, 2.5vw, 1.2rem);
            font-weight: 500;
            opacity: 0.85;
            margin-bottom: 0.25rem;
        }

        .cm-desc {
            text-align: center;
            font-size: 0.95rem;
            opacity: 0.65;
            margin-bottom: 1.5rem;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Page Header
# --------------------------------------------------

st.markdown(
    '<div class="cm-title">📚 CourseMate AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="cm-tagline">AI Learning Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="cm-desc">'
    "Ask questions about your course documents and get "
    "answers grounded in your own materials, with "
    "page-level sources."
    "</div>",
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def classify_error(error: Exception) -> str:
    """
    Convert technical exceptions into safe,
    user-friendly messages.

    Technical details are logged separately
    and are never exposed in the UI.
    """

    text = str(error).lower()

    # Gemini quota / rate limit
    if any(
        value in text
        for value in (
            "429",
            "quota",
            "resource_exhausted",
            "rate limit",
        )
    ):
        return (
            "Gemini is currently unavailable because "
            "the API quota or rate limit may have been reached. "
            "Please try again later."
        )

    # Authentication / permissions
    if any(
        value in text
        for value in (
            "api key",
            "api_key",
            "401",
            "403",
            "permission_denied",
            "unauthenticated",
        )
    ):
        return (
            "Gemini rejected the API key. "
            "Please check GEMINI_API_KEY in your .env file."
        )

    # Model unavailable
    if (
        ("404" in text or "not found" in text)
        and "model" in text
    ):
        return (
            "The configured Gemini model is unavailable. "
            "Please check the model name in your configuration."
        )

    # Network / connection problems
    if (
        isinstance(
            error,
            (
                httpx.HTTPError,
                ConnectionError,
                TimeoutError,
            ),
        )
        or "10054" in text
    ):
        return (
            "Could not reach Gemini. "
            "Please check your internet connection "
            "or Gemini service availability."
        )

    return (
        "Something went wrong while generating "
        "the answer. Please try again."
    )


def get_api_key() -> str:
    """Load and validate the Gemini API key."""

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise SetupError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file and restart the app."
        )

    return api_key


def format_source(doc) -> dict:
    """
    Extract display-friendly metadata
    from a retrieved document chunk.
    """

    raw_source = doc.metadata.get(
        "source",
        "Unknown source",
    )

    page = doc.metadata.get(
        "page"
    )

    return {
        "document": Path(
            str(raw_source)
        ).name,

        # PyPDFLoader uses 0-based page indexes.
        "page": (
            page + 1
            if isinstance(page, int)
            else "Unknown"
        ),

        "text": doc.page_content,
    }


def render_sources(
    sources: list,
) -> None:
    """Display retrieved document sources."""

    with st.expander(
        "📖 View retrieved sources"
    ):

        for i, source in enumerate(
            sources,
            start=1,
        ):

            st.markdown(
                f"**Source {i}**"
            )

            st.caption(
                f"Document: `{source['document']}`  |  "
                f"Page: `{source['page']}`"
            )

            st.write(
                source["text"]
            )

            if i < len(sources):
                st.divider()


def build_context(
    sources: list,
) -> str:
    """Build the context sent to the LLM."""

    return "\n\n".join(
        (
            f"[Source: {source['document']}, "
            f"page {source['page']}]\n"
            f"{source['text']}"
        )
        for source in sources
    )


# --------------------------------------------------
# RAG Initialization
# Cached so the system is not recreated
# on every Streamlit interaction.
# --------------------------------------------------

@st.cache_resource
def initialize_rag():

    # ----------------------------------------------
    # API Key
    # ----------------------------------------------

    api_key = get_api_key()


    # ----------------------------------------------
    # Gemini Embeddings
    # ----------------------------------------------

    embedding_model = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
    )


    # ----------------------------------------------
    # Chroma Directory
    # ----------------------------------------------

    if not Path(
        CHROMA_DIR
    ).exists():

        raise SetupError(
            "The knowledge base was not found. "
            "Run create_database.py first."
        )


    # ----------------------------------------------
    # Chroma Vector Database
    # ----------------------------------------------

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,
        embedding_function=embedding_model,
    )


    # ----------------------------------------------
    # Knowledge Base Check
    # ----------------------------------------------

    # This reads local Chroma metadata.
    # It does not call Gemini.

    document_count = (
        vectorstore._collection.count()
    )

    if document_count == 0:

        raise SetupError(
            "The knowledge base is empty. "
            "Run create_database.py first."
        )


    # ----------------------------------------------
    # Retriever
    # ----------------------------------------------

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": RETRIEVER_K,
            "fetch_k": RETRIEVER_FETCH_K,
            "lambda_mult": RETRIEVER_LAMBDA,
        },
    )


    # ----------------------------------------------
    # Gemini LLM
    # ----------------------------------------------

    llm = ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0,
        google_api_key=api_key,
    )


    # ----------------------------------------------
    # Prompt
    # ----------------------------------------------

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SYSTEM_PROMPT,
            ),
            (
                "human",
                HUMAN_PROMPT,
            ),
        ]
    )


    return (
        retriever,
        llm,
        prompt,
        document_count,
    )


# --------------------------------------------------
# Session State
# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = []


# --------------------------------------------------
# Load RAG System
# --------------------------------------------------

rag_ready = True
document_count = 0
setup_message = ""


try:

    (
        retriever,
        llm,
        prompt,
        document_count,
    ) = initialize_rag()


except SetupError as error:

    rag_ready = False

    setup_message = str(error)

    logger.error(
        "Setup problem: %s",
        error,
    )


except Exception:

    rag_ready = False

    setup_message = (
        "CourseMate AI could not start. "
        "Please check the terminal for details."
    )

    logger.exception(
        "Unexpected initialization failure"
    )


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.header(
        "📚 CourseMate AI"
    )

    st.caption(
        "Retrieval-Augmented Generation "
        "for course materials"
    )

    st.divider()


    # ----------------------------------------------
    # Knowledge Base
    # ----------------------------------------------

    st.subheader(
        "Knowledge Base"
    )

    if rag_ready:

        st.metric(
            "Stored chunks",
            document_count,
        )

    else:

        st.caption(
            "Not available"
        )


    st.divider()


    # ----------------------------------------------
    # AI System
    # ----------------------------------------------

    st.subheader(
        "AI System"
    )

    st.markdown(
        f"""
- **LLM:** `{CHAT_MODEL}`
- **Embeddings:** `{EMBEDDING_MODEL}`
- **Vector DB:** Chroma
- **Retrieval:** MMR (top {RETRIEVER_K})
"""
    )


    st.divider()


    # ----------------------------------------------
    # Clear Chat
    # ----------------------------------------------

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.rerun()


# --------------------------------------------------
# Stop if RAG is not ready
# --------------------------------------------------

if not rag_ready:

    st.error(
        setup_message
    )

    st.stop()


# --------------------------------------------------
# Empty State
# --------------------------------------------------

if not st.session_state.messages:

    st.info(
        "👋 Welcome to CourseMate AI"
    )

    st.markdown(
        """
        Ask questions about your course materials
        and learn from your documents.

        **Example questions:**

        - What is a GRU?
        - What are the two main gates in a GRU?
        - Explain the GRU mathematical formulation.
        """
    )


# --------------------------------------------------
# Display Chat History
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

        if message.get(
            "sources"
        ):

            render_sources(
                message["sources"]
            )


# --------------------------------------------------
# Chat Input
# --------------------------------------------------

query = st.chat_input(
    "Ask a question about your course documents..."
)


# --------------------------------------------------
# Handle New Question
# --------------------------------------------------

if query:

    # ----------------------------------------------
    # Display User Question
    # ----------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            query
        )


    # ----------------------------------------------
    # Save User Message
    # ----------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": query,
        }
    )


    answer = None
    sources = []


    # ----------------------------------------------
    # Generate Answer
    # ----------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "Searching the course documents..."
        ):

            try:

                # ----------------------------------
                # Retrieve Documents
                # ----------------------------------

                docs = retriever.invoke(
                    query
                )


                # ----------------------------------
                # No Documents Found
                # ----------------------------------

                if not docs:

                    answer = (
                        NOT_FOUND_ANSWER
                    )


                else:

                    # ------------------------------
                    # Format Sources
                    # ------------------------------

                    sources = [
                        format_source(doc)
                        for doc in docs
                    ]


                    # ------------------------------
                    # Build Context
                    # ------------------------------

                    context = build_context(
                        sources
                    )


                    # ------------------------------
                    # Build Prompt
                    # ------------------------------

                    final_prompt = (
                        prompt.invoke(
                            {
                                "context": context,
                                "question": query,
                            }
                        )
                    )


                    # ------------------------------
                    # Generate Answer
                    # ------------------------------

                    response = llm.invoke(
                        final_prompt
                    )


                    # ------------------------------
                    # Extract Answer
                    # ------------------------------

                    answer = (
                        response.text or ""
                    ).strip()


                    # ------------------------------
                    # Empty Response
                    # ------------------------------

                    if not answer:

                        logger.warning(
                            "Gemini returned an empty response"
                        )

                        answer = (
                            "Gemini returned an empty response. "
                            "Please try rephrasing your question."
                        )


            except Exception as error:

                # ----------------------------------
                # Log Technical Error
                # ----------------------------------

                logger.exception(
                    "Failed while answering a question"
                )


                # ----------------------------------
                # User-Friendly Error
                # ----------------------------------

                answer = classify_error(
                    error
                )

                # Keep retrieved sources.
                # Retrieval may have succeeded even
                # if Gemini generation failed.


        # ------------------------------------------
        # Display Answer
        # ------------------------------------------

        st.markdown(
            answer
        )


        # ------------------------------------------
        # Display Retrieved Sources
        # ------------------------------------------

        if sources:

            render_sources(
                sources
            )


    # ----------------------------------------------
    # Save Assistant Message
    # ----------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        }
    )