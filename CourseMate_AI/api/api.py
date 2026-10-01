import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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

app = FastAPI(
    title="CourseMate AI API",
    description="RAG API for course document question answering",
    version="1.0.0",
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_DIR = str(
    BASE_DIR / "chroma_db"
)

COLLECTION_NAME = "coursemate_gemini"

EMBEDDING_MODEL = "gemini-embedding-001"
CHAT_MODEL = "gemini-3.8-flash"


# --------------------------------------------------
# API Key
# --------------------------------------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing."
    )


# --------------------------------------------------
# Embedding Model
# --------------------------------------------------

embedding_model = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL,
    google_api_key=api_key,
)


# --------------------------------------------------
# Chroma Vector Database
# --------------------------------------------------

vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_DIR,
    embedding_function=embedding_model,
)


# --------------------------------------------------
# Retriever
# --------------------------------------------------

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 4,
        "fetch_k": 10,
        "lambda_mult": 0.5,
    },
)


# --------------------------------------------------
# Gemini LLM
# --------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model=CHAT_MODEL,
    temperature=0,
    google_api_key=api_key,
)


# --------------------------------------------------
# Prompt
# --------------------------------------------------

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful AI learning assistant.

Use ONLY the provided context to answer the question.

Do not use outside knowledge.

If the answer is not present in the context,
say:

"I could not find the answer in the document."

Give clear and educational explanations
when the answer is available in the context.
""",
        ),
        (
            "human",
            """Context:

{context}

Question:

{question}
""",
        ),
    ]
)


# --------------------------------------------------
# Request Model
# --------------------------------------------------

class QuestionRequest(BaseModel):

    question: str


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "CourseMate AI API is running",
        "status": "ok",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):

    try:

        # ------------------------------------------
        # Retrieve relevant documents
        # ------------------------------------------

        docs = retriever.invoke(
            request.question
        )


        # ------------------------------------------
        # No documents found
        # ------------------------------------------

        if not docs:

            return {
                "answer": (
                    "I could not find the answer "
                    "in the document."
                ),
                "sources": [],
            }


        # ------------------------------------------
        # Build context
        # ------------------------------------------

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )


        # ------------------------------------------
        # Build prompt
        # ------------------------------------------

        final_prompt = prompt.invoke(
            {
                "context": context,
                "question": request.question,
            }
        )


        # ------------------------------------------
        # Generate answer
        # ------------------------------------------

        response = llm.invoke(
            final_prompt
        )


        # ------------------------------------------
        # Build source information
        # ------------------------------------------

        sources = []

        for doc in docs:

            page = doc.metadata.get(
                "page"
            )

            sources.append(
                {
                    "document": Path(
                        str(
                            doc.metadata.get(
                                "source",
                                "Unknown source",
                            )
                        )
                    ).name,

                    "page": (
                        page + 1
                        if isinstance(page, int)
                        else "Unknown"
                    ),
                }
            )


        # ------------------------------------------
        # Return response
        # ------------------------------------------

        return {
            "answer": response.text,
            "sources": sources,
        }


    except Exception as error:

        error_text = str(
            error
        ).lower()


        # ------------------------------------------
        # Gemini quota / rate limit
        # ------------------------------------------

        if any(
            value in error_text
            for value in (
                "429",
                "quota",
                "resource_exhausted",
                "rate limit",
            )
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota has been reached. "
                    "Please try again later."
                ),
            )


        # ------------------------------------------
        # Gemini authentication
        # ------------------------------------------

        if any(
            value in error_text
            for value in (
                "401",
                "403",
                "api key",
                "api_key",
                "permission_denied",
                "unauthenticated",
            )
        ):

            raise HTTPException(
                status_code=401,
                detail=(
                    "Gemini API authentication failed. "
                    "Please check the API key."
                ),
            )


        # ------------------------------------------
        # Other errors
        # ------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred while processing "
                "the question."
            ),
        )