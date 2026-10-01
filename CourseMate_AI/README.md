# CourseMate AI

**CourseMate AI** is a **Retrieval-Augmented Generation (RAG) + Generative AI** application that allows users to ask questions about course materials and receive AI-generated answers grounded in a knowledge base.

The project combines **PDF processing, text chunking, Gemini embeddings, ChromaDB vector search, RAG retrieval, Generative AI, FastAPI, and Streamlit** into a complete deployed AI application.

---

## Live Demo

### Streamlit Frontend

**Live Application:**
https://generativeaiprojects-86fumuwz2wdauvhmrbm3ya.streamlit.app/

### FastAPI Backend

**API Documentation / Swagger:**
https://generative-ai-projects-uxv3.onrender.com/docs

---

## Project Overview

CourseMate AI follows a two-part architecture:

```text
                    CourseMate AI
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
   Streamlit Frontend             FastAPI Backend
                                      │
                                      ▼
                              RAG + Generative AI
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                         ▼                         ▼
                     ChromaDB                  Gemini
                  Vector Database          Generative AI
                         │
                         ▼
                  Retrieved Context
                         │
                         └──────────────┐
                                        ▼
                                  AI-generated
                                     Answer
```

---

## How It Works

The system processes course material and creates a searchable vector knowledge base.

### Knowledge Base Creation

```text
PDF Course Material
        ↓
    PDF Loader
        ↓
   Text Extraction
        ↓
    Text Chunking
        ↓
 Gemini Embeddings
        ↓
      ChromaDB
```

### Question Answering

```text
User Question
      ↓
Streamlit Frontend
      ↓
FastAPI Backend
      ↓
Question Embedding
      ↓
ChromaDB Similarity Search
      ↓
Relevant Context
      ↓
Generative AI
      ↓
Generated Answer
      ↓
Streamlit
```

---

## RAG Pipeline

The Retrieval-Augmented Generation pipeline consists of:

1. **Document Loading** — course material is loaded from PDF files.
2. **Text Splitting** — documents are divided into smaller chunks.
3. **Embedding Generation** — chunks are converted into vector representations using Gemini embeddings.
4. **Vector Storage** — embeddings are stored in ChromaDB.
5. **Similarity Search** — relevant chunks are retrieved for a user's question.
6. **Context Augmentation** — retrieved content is provided as context to the generative model.
7. **Answer Generation** — the model generates the final response.

---

## Project Structure

```text
CourseMate_AI/
│
├── api/
│   └── ...
│
├── data/
│   └── ...
│
├── chroma_db/
│   ├── chroma.sqlite3
│   └── ...
│
├── app.py
├── create_database.py
├── main.py
├── local_main.py
├── local_create_database.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Main Files

### `app.py`

The Streamlit frontend.

It provides the user interface for submitting questions and displaying the generated answers.

### `create_database.py`

Creates the ChromaDB knowledge base.

The script:

```text
PDF
 ↓
Document Loader
 ↓
Text Chunks
 ↓
Gemini Embeddings
 ↓
ChromaDB
```

### `chroma_db/`

Contains the generated ChromaDB vector database used for retrieval.

The current knowledge base was successfully generated from the course material.

Example local generation output:

```text
Loaded 2 pages.
Created 3 chunks.
Embedded 3/3 chunks

Vector database created successfully with Gemini embeddings!
Total chunks stored: 3
```

### `api/`

Contains the backend API components.

### `requirements.txt`

Contains the Python dependencies required to run the project.

---

## Technologies

| Technology      | Purpose                        |
| --------------- | ------------------------------ |
| Python          | Main programming language      |
| Streamlit       | Frontend / user interface      |
| FastAPI         | Backend REST API               |
| LangChain       | LLM and RAG orchestration      |
| ChromaDB        | Vector database                |
| Gemini          | Embeddings and Generative AI   |
| RAG             | Retrieval-Augmented Generation |
| Render          | Backend deployment             |
| Streamlit Cloud | Frontend deployment            |
| GitHub          | Source-code management         |

---

## API

The FastAPI backend is deployed on Render.

### Swagger Documentation

https://generative-ai-projects-uxv3.onrender.com/docs

### Question Endpoint

```text
POST /ask
```

The endpoint receives a user question and processes it through the CourseMate AI RAG pipeline.

---

## Local Installation

Clone the repository:

```bash
git clone https://github.com/robelgher16-ai/GENERATIVE_AI_PROJECTS.git
```

Navigate to the project:

```bash
cd "GENERATIVE_AI_PROJECTS/CourseMate_AI"
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a local `.env` file:

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

**Never commit your API key to GitHub.**

The `.env` file is excluded through `.gitignore`.

---

## Create the Knowledge Base

Run:

```bash
python create_database.py
```

This creates the ChromaDB vector database from the available course material.

The generated database is stored in:

```text
chroma_db/
```

---

## Run Locally

Start the Streamlit application:

```bash
streamlit run app.py
```

The application can then be accessed through the local Streamlit URL shown in the terminal.

---

## Deployment

### Frontend — Streamlit Cloud

```text
GitHub
   ↓
Streamlit Cloud
   ↓
CourseMate AI
```

**Live frontend:**

https://generativeaiprojects-86fumuwz2wdauvhmrbm3ya.streamlit.app/

### Backend — Render

```text
GitHub
   ↓
Render
   ↓
FastAPI
   ↓
RAG + Generative AI
```

**Live API:**

https://generative-ai-projects-uxv3.onrender.com/docs

---

## Complete Deployment Architecture

```text
                         USER
                          │
                          ▼
                ┌──────────────────┐
                │    Streamlit     │
                │     Frontend     │
                └────────┬─────────┘
                         │
                         │ HTTP Request
                         ▼
                ┌──────────────────┐
                │     FastAPI      │
                │     Backend      │
                │     Render       │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │       RAG        │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │     ChromaDB     │
                │  Vector Database │
                └────────┬─────────┘
                         │
                    Retrieved
                     Context
                         │
                         ▼
                ┌──────────────────┐
                │      Gemini      │
                │  Generative AI   │
                └────────┬─────────┘
                         │
                    AI Response
                         │
                         ▼
                ┌──────────────────┐
                │    Streamlit     │
                │   Final Answer   │
                └──────────────────┘
```

---

## Features

- PDF-based knowledge base
- Document loading
- Text chunking
- Gemini embeddings
- ChromaDB vector storage
- Semantic similarity search
- Retrieval-Augmented Generation
- Generative AI question answering
- FastAPI backend
- Streamlit frontend
- REST API
- Swagger API documentation
- Cloud deployment
- GitHub version control

---

## Current Project Status

**Status: Deployed**

| Component                   | Status    |
| --------------------------- | --------- |
| RAG pipeline                | Complete  |
| PDF processing              | Complete  |
| Text chunking               | Complete  |
| Gemini embeddings           | Complete  |
| ChromaDB knowledge base     | Complete  |
| FastAPI backend             | Deployed  |
| Render API                  | Live      |
| Streamlit frontend          | Deployed  |
| Streamlit ↔ API integration | Connected |
| GitHub repository           | Updated   |
| Documentation               | Updated   |

---

## Future Improvements

- Support multiple course materials
- Multiple PDF uploads
- Conversation memory
- Source citations
- Improved retrieval strategies
- Metadata filtering
- User-specific knowledge bases
- Persistent cloud vector database
- Streaming responses
- RAG evaluation
- Answer-quality evaluation
- Improved UI/UX
- Authentication

---

## Author

**Robel Gebregziabher**

AI / Machine Learning Engineer
Information Technology Student

GitHub:
https://github.com/robelgher16-ai

---

## Project Repository

**Generative AI Projects**

https://github.com/robelgher16-ai/GENERATIVE_AI_PROJECTS
