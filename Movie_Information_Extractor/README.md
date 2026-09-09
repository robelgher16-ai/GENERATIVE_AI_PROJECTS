# 🎬 Movie Information Extractor

<p align="center">
  <img src="screenshots/local-home.png" width="100%" alt="Movie Information Extractor Home">
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![LangChain](https://img.shields.io/badge/LangChain-LLM-green)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![Pydantic](https://img.shields.io/badge/Pydantic-Validation-purple)
![Gemini](https://img.shields.io/badge/Gemini-Google-orange?logo=google)
![TinyLlama](https://img.shields.io/badge/TinyLlama-Local%20LLM-black)
![License](https://img.shields.io/badge/License-MIT-yellow)

</p>

<p align="center">
  <b>Extract structured movie information from natural language using Generative AI.</b>
</p>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Application Screenshots](#-application-screenshots)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Problem Statement](#-problem-statement)
- [Project Goal](#-project-goal)
- [Architecture](#️-architecture)
- [Technologies](#-technologies)
- [Requirements](#-requirements)
- [Project Development Phases](#-project-development-phases)
- [Project Structure](#-project-structure)
- [Movie Data Schema](#-movie-data-schema)
- [Environment Variables](#-environment-variables)
- [Local AI Version](#-local-ai-version)
- [Supported Models](#-supported-models)
- [Gemini API Version](#️-gemini-api-version)
- [Running the Application](#️-running-the-application)
- [Example Input](#-example-input)
- [Example Output](#-example-output)
- [Structured Output](#-structured-output)
- [Pydantic Validation](#️-pydantic-validation)
- [Error Handling](#️-error-handling)
- [Testing](#-testing)
- [Security](#-security)
- [Limitations](#️-limitations)
- [Future Improvements](#-future-improvements)
- [Learning Outcomes](#-learning-outcomes)
- [License](#-license)
- [Author](#-author)
- [Project Status](#-project-status)

---

## 🌟 Overview

**Movie Information Extractor** is an AI-powered application that transforms **unstructured movie descriptions** into **structured, validated JSON** using Large Language Models.

The project supports **two AI engines**:

- 🤖 **Local AI** — TinyLlama (runs completely on your computer)
- ☁️ **Cloud AI** — Google Gemini via LangChain

Built with **Python, LangChain, Pydantic, Streamlit, Transformers, and UV**, this project demonstrates the complete lifecycle of a modern Generative AI application — from prompt engineering to deployment-ready documentation.

For example, given:

> Inception is a 2010 science-fiction action film directed by Christopher Nolan. The movie stars Leonardo DiCaprio and Tom Hardy.

The system extracts:

```json
{
  "title": "Inception",
  "release_year": 2010,
  "genre": ["Science Fiction", "Action"],
  "director": "Christopher Nolan",
  "cast": ["Leonardo DiCaprio", "Tom Hardy"],
  "rating": null,
  "summery": "A skilled thief enters people's dreams to steal information."
}
```

This demonstrates how an LLM can transform **unstructured text → structured data**.

---

## 📸 Application Screenshots

### 🏠 1. Local Version — Home Page

![Local Home](screenshots/local-home.png)

The default interface of the TinyLlama version where users can paste a movie description and extract structured information locally.

---

### ☁️ 2. Gemini API Version

![API Home](screenshots/api-home.png)

The cloud-powered version uses Google Gemini through LangChain for more accurate structured extraction.

---

### 🎬 3. Extracted Movie Information

![Movie Result](screenshots/movie-result.png)

After processing, the application displays:

- Movie title
- Release year
- Director
- Genres
- Cast
- Rating
- Summary

using a modern Streamlit card layout.

---

### 📄 4. Structured JSON Output

![JSON Output](screenshots/json-output.png)

The validated Pydantic output is displayed as formatted JSON and can be downloaded with one click.

---

### ⚠️ 5. Error Handling

![Error Screen](screenshots/error-screen.png)

If the language model returns invalid or malformed JSON, the application catches the error and shows a user-friendly validation message instead of crashing.

---

## ✨ Features

### 🤖 AI Features

- Natural language movie understanding
- Structured information extraction
- Prompt engineering with LangChain
- Pydantic schema validation
- Local TinyLlama inference
- Google Gemini API integration
- Missing-value handling
- JSON normalization

### 🖥️ UI Features

- Modern Streamlit interface
- Dark professional design
- Genre badges
- Cast badges
- Movie information cards
- JSON viewer
- Raw model output viewer
- Download JSON button
- Example input generator
- Friendly error messages

### 🔐 Privacy

- TinyLlama works **100% locally**
- No API key required for local mode
- Gemini credentials stored securely in `.env`

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/RobelGebregziabher/movie-information-extractor.git
cd movie-information-extractor
```

### 2. Create a Virtual Environment with UV

```powershell
uv venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
uv sync
```

Or, alternatively:

```powershell
uv pip install -r requirements.txt
```

### 4. Run the Local (TinyLlama) Version

```powershell
streamlit run app_local.py
```

### 5. Run the Gemini API Version

Add your key to `.env`:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

Then run:

```powershell
streamlit run app_api.py
```

Streamlit will open a local URL in your browser — paste a movie description and click **Extract Movie Information**.

> 📖 Full setup details, environment variables, and troubleshooting are covered in the sections below.

---

## ❓ Problem Statement

Movie information is often stored in unstructured formats such as:

- Articles
- Reviews
- News
- Wikipedia-style descriptions
- Documents
- Web pages
- Natural-language text

Extracting information manually from these sources can be slow and inconsistent.

This project uses an LLM to automatically identify and organize important movie information into a predictable structure.

---

## 🎯 Project Goal

The main goal is to build a reliable AI application capable of:

1. Accepting unstructured movie text.
2. Understanding the movie information.
3. Extracting relevant fields.
4. Producing structured JSON.
5. Validating the extracted information with Pydantic.
6. Displaying the results through a Streamlit interface.
7. Supporting both local and API-based LLMs.

---

## 🏗️ Architecture

```text
                 MOVIE INFORMATION EXTRACTOR
                           │
             ┌─────────────┴─────────────┐
             │                           │
       LOCAL VERSION                API VERSION
             │                           │
         TinyLlama                    Gemini
             │                           │
             └─────────────┬─────────────┘
                           │
                       LangChain
                           │
                  ChatPromptTemplate
                           │
                    Movie Description
                           │
                    LLM Processing
                           │
                    Structured JSON
                           │
                     JSON Parsing
                           │
                       Pydantic
                           │
                  Validated Movie Data
                           │
             ┌─────────────┼─────────────┐
             │             │             │
           Streamlit      JSON        Download
              UI          View           JSON
```

---

## 🧠 Technologies

| Technology     | Purpose                                |
| -------------- | --------------------------------------- |
| Python         | Programming language                   |
| UV             | Python package/environment management  |
| LangChain      | LLM application framework              |
| LangChain Core | Prompt templates and core abstractions |
| Google Gemini  | Cloud LLM                              |
| TinyLlama      | Local LLM                              |
| Hugging Face   | Local model integration                |
| Transformers   | Local model execution                  |
| PyTorch        | Deep learning framework                |
| Pydantic       | Data validation                        |
| python-dotenv  | Environment variable management        |
| Streamlit      | Web application UI                     |
| Pytest         | Automated testing                      |
| Git            | Version control                        |
| GitHub         | Code hosting                           |

---

## 📦 Requirements

- Python 3.13+
- UV package manager
- 8 GB RAM recommended for TinyLlama
- Internet connection (Gemini version only)

Install dependencies:

```bash
uv sync
```

---

## 🚀 Project Development Phases

The project was developed progressively.

### Phase 1 — UV + LangChain Setup

The project environment was created using UV.

Main concepts:

- UV installation
- Virtual environments
- Package management
- LangChain installation
- Project initialization

---

### Phase 2 — Environment & Security

Environment variables were introduced for API credentials.

Implemented:

- `.env`
- `.env.example`
- `.gitignore`
- Environment variable loading
- Secret protection

---

### Phase 3 — Chat Models

Two different LLM approaches were implemented.

**API Model** — Google Gemini through LangChain.

**Local Model** — TinyLlama through Hugging Face.

This phase demonstrated the difference between:

```text
Cloud LLM
   ↓
API Request
   ↓
Model Response
```

and:

```text
Local LLM
   ↓
Local Model
   ↓
Local Inference
```

---

### Phase 4 — Prompt Engineering

A professional movie extraction prompt was created.

The prompt instructs the model to:

- Extract movie information.
- Avoid guessing.
- Return `NULL` for unknown values.
- Follow a specific schema.
- Produce structured information.

Prompt structure:

```text
System Instructions
        ↓
Movie Extraction Rules
        ↓
User Movie Description
        ↓
LLM
```

---

### Phase 5 — Structured Output

Pydantic was introduced to define the movie schema.

The system validates the model output before displaying it.

The API version uses LangChain's structured-output parsing approach.

The local version uses JSON extraction followed by Pydantic validation because smaller local models such as TinyLlama may produce additional text around JSON.

---

### Phase 6 — Streamlit UI

A complete Streamlit interface was developed.

The UI includes:

- Application header
- Sidebar
- Movie input
- Example button
- Extraction button
- Movie result card
- Genre badges
- Cast badges
- Rating
- Summary
- JSON output
- Raw model output
- Download button
- Error messages

---

### Phase 7 — Testing & Error Handling

Testing was introduced for:

- Pydantic movie validation
- JSON extraction
- Valid JSON
- Markdown-wrapped JSON
- Invalid model responses

The application also handles:

- Invalid JSON
- Missing fields
- Empty values
- Unexpected model output
- Validation errors

---

### Phase 8 — Documentation

Professional project documentation was added.

This includes:

- README
- Installation instructions
- Architecture
- Project structure
- Usage instructions
- Security information
- Future improvements
- Testing information

---

### Phase 9 — Git & GitHub

The project is prepared for version control using Git.

Sensitive files such as `.env` and the virtual environment are excluded using `.gitignore`.

---

## 📁 Project Structure

```text
movie-information-extractor/
│
├── app_local.py
├── app_api.py
│
├── chatmodels/
│   ├── __init__.py
│   ├── api.py
│   └── locally.py
│
├── screenshots/
│   ├── local-home.png
│   ├── api-home.png
│   ├── movie-result.png
│   ├── json-output.png
│   └── error-screen.png
│
├── tests/
│   ├── __init__.py
│   ├── test_movie_model.py
│   └── test_json_parser.py
│
├── .env
├── .env.example
├── .gitignore
│
├── README.md
├── LICENSE
├── requirements.txt
│
├── pyproject.toml
├── uv.lock
└── .python-version
```

### Important

The following files should **never be committed**:

```text
.env
.venv/
*.pth
*.pt
*.bin
*.safetensors
```

---

## 🧾 Movie Data Schema

The extracted movie information follows this schema:

```python
class Movie(BaseModel):
    title: str
    release_year: Optional[int]
    genre: List[str]
    director: Optional[str]
    cast: List[str]
    rating: Optional[float]
    summery: str
```

### Fields

| Field          | Type            | Description         |
| -------------- | --------------- | -------------------- |
| `title`        | `str`           | Movie title          |
| `release_year` | `int \| None`   | Movie release year   |
| `genre`        | `List[str]`     | Movie genres         |
| `director`     | `str \| None`   | Movie director       |
| `cast`         | `List[str]`     | Main cast members    |
| `rating`       | `float \| None` | Movie rating         |
| `summery`      | `str`           | Short movie summary  |

> **Note:** The field name `summery` is preserved for compatibility with Version 1.0. It will be renamed to `summary` in a future release.

---

## 🔐 Environment Variables

Create a `.env` file in the project root.

For the Gemini API version:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

The local TinyLlama version does **not** require an API key.

### Important Security Rule

Never commit `.env` to GitHub.

Your `.gitignore` should contain:

```gitignore
.env
```

If an API key is accidentally pushed to GitHub, revoke or rotate it immediately.

---

## 🤖 Local AI Version

The local version uses:

```text
TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

The model runs locally through:

```text
Hugging Face
       ↓
Transformers
       ↓
LangChain HuggingFace
       ↓
TinyLlama
       ↓
Movie Extraction
```

### Advantages

- No API key
- Local inference
- Better privacy
- Can work without sending movie text to a cloud API
- Useful for learning local LLM deployment

### Limitations

TinyLlama is a relatively small model.

It may sometimes produce:

- Additional explanation
- Incorrect JSON
- Multiple JSON objects
- Schema text
- Unexpected formatting

Therefore, the local application includes additional JSON extraction and validation logic.

---

## 🤖 Supported Models

| Mode  | Model                     |
| ----- | ------------------------- |
| Local | TinyLlama-1.1B-Chat-v1.0  |
| Cloud | Gemini 2.5 Flash          |

The application lets you run completely offline using TinyLlama or use Google's Gemini model for stronger extraction accuracy.

---

## ☁️ Gemini API Version

The API version uses Google Gemini through LangChain.

The general workflow is:

```text
Movie Text
     ↓
ChatPromptTemplate
     ↓
Gemini
     ↓
Structured Response
     ↓
Pydantic Validation
     ↓
Streamlit
```

The Gemini version generally provides stronger instruction following than the small local TinyLlama model.

---

## ▶️ Running the Application

### Local Version

Activate the environment:

```powershell
.venv\Scripts\activate
```

Run:

```powershell
streamlit run app_local.py
```

---

### Gemini API Version

Make sure your `.env` contains your Google API key.

Then run:

```powershell
streamlit run app_api.py
```

Streamlit will provide a local web address where the application can be opened in your browser.

---

## 📝 Example Input

```text
Inception is a 2010 science-fiction action film directed by Christopher Nolan. The movie stars Leonardo DiCaprio, Joseph Gordon-Levitt, Ellen Page, Tom Hardy, and Ken Watanabe. The story follows Dom Cobb, a skilled thief who enters people's dreams to steal information. The film was produced by Warner Bros.
```

---

## 📤 Example Output

```json
{
  "title": "Inception",
  "release_year": 2010,
  "genre": ["Science Fiction", "Action"],
  "director": "Christopher Nolan",
  "cast": [
    "Leonardo DiCaprio",
    "Joseph Gordon-Levitt",
    "Ellen Page",
    "Tom Hardy",
    "Ken Watanabe"
  ],
  "rating": null,
  "summery": "A skilled thief enters people's dreams to steal information."
}
```

---

## 🧩 Structured Output

One of the main goals of this project is converting:

```text
Unstructured Natural Language
```

into:

```text
Structured Data
```

For example:

```text
"Inception is a 2010 science-fiction film..."
```

becomes:

```json
{
  "title": "Inception",
  "release_year": 2010,
  "genre": ["Science Fiction"]
}
```

This type of transformation is useful for:

- Data pipelines
- Information extraction
- Document processing
- Search systems
- RAG applications
- Knowledge bases
- AI agents
- Database population
- Automation

---

## 🛡️ Pydantic Validation

Pydantic ensures that the extracted information follows the expected structure.

For example:

```python
movie = Movie.model_validate(data)
```

If the model produces an invalid structure, the application can catch the validation error rather than blindly trusting the LLM output.

This creates the pipeline:

```text
LLM Output
    ↓
JSON Extraction
    ↓
Data Normalization
    ↓
Pydantic Validation
    ↓
Validated Data
```

---

## ⚠️ Error Handling

The application handles several possible failures.

### Invalid JSON

```text
LLM
 ↓
Invalid Output
 ↓
JSON Extraction Fails
 ↓
User-Friendly Error
```

### Missing Information

Unknown information is represented using values such as:

```json
null
```

or:

```json
[]
```

depending on the field.

### Pydantic Validation Error

If the extracted information does not match the expected schema, the application reports a validation error.

---

## 🧪 Testing

The project includes automated tests using Pytest.

Run:

```powershell
pytest
```

Example test:

```python
def test_movie_model():
    movie = Movie(
        title="Inception",
        release_year=2010,
        genre=["Science Fiction", "Action"],
        director="Christopher Nolan",
        cast=["Leonardo DiCaprio"],
        rating=8.8,
        summery="A thief enters people's dreams."
    )

    assert movie.title == "Inception"
    assert movie.release_year == 2010
    assert movie.director == "Christopher Nolan"
```

JSON parsing tests verify:

- Valid JSON
- Markdown-wrapped JSON
- Invalid responses

---

## 🔒 Security

This project uses environment variables for API credentials.

### Never commit:

```text
.env
```

### Never hard-code:

```python
GOOGLE_API_KEY = "your-real-key"
```

Instead:

```python
from dotenv import load_dotenv

load_dotenv()
```

and store credentials inside `.env`.

A safe example file can be provided as:

```text
.env.example
```

with:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

---

## ⚠️ Limitations

### Local Model

TinyLlama is a small language model and may not always follow strict JSON instructions.

Possible issues include:

- Hallucinated information
- Incorrect formatting
- Incomplete extraction
- Additional text
- Incorrect field values

Therefore, model output should not automatically be treated as guaranteed factual information.

---

### Gemini API

The API version depends on:

- Internet connectivity
- API availability
- API limits
- API credentials

---

### Movie Information

The application extracts information from the text provided by the user.

It does not independently verify movie information against an external database.

Therefore:

```text
Extraction ≠ Fact Verification
```

---

## 🚀 Future Improvements

The project can be expanded significantly.

### Version 2

- Better JSON repair
- Improved validation
- More robust model fallback
- Better logging
- More unit tests

### Version 3

Add external movie databases:

```text
Movie Text
    ↓
LLM Extraction
    ↓
Movie Database
    ↓
Fact Verification
    ↓
Validated Movie
```

### Version 4

Add RAG:

```text
Movie Documents
       ↓
Document Loader
       ↓
Chunking
       ↓
Embeddings
       ↓
Vector Database
       ↓
Retriever
       ↓
LLM
       ↓
Movie Information
```

### Version 5

Add an AI Agent capable of:

- Searching movie information
- Comparing movies
- Finding actors
- Finding directors
- Summarizing reviews
- Answering movie questions

### Version 6

Deploy the application using:

- Docker
- Cloud deployment
- CI/CD
- GitHub Actions

---

## 📚 Learning Outcomes

This project demonstrates practical knowledge of:

### Python

- Classes
- Functions
- Type hints
- Error handling
- Environment variables

### LangChain

- Chat models
- Prompt templates
- Output parsing
- Hugging Face integration

### Generative AI

- LLM prompting
- Structured generation
- Local LLMs
- API-based LLMs
- Model limitations

### Pydantic

- Data schemas
- Validation
- Structured data
- Type safety

### Streamlit

- Interactive UI
- Session state
- Cached resources
- Custom CSS
- Downloadable results

### Software Engineering

- Virtual environments
- Dependency management
- Testing
- Git
- GitHub
- Project documentation
- Secret management

---

## 🔄 Complete Project Lifecycle

```text
PHASE 1
UV + LangChain
      ↓
PHASE 2
Environment + Security
      ↓
PHASE 3
Chat Models
      ↓
PHASE 4
Prompt Engineering
      ↓
PHASE 5
Structured Output
      ↓
PHASE 6
Streamlit UI
      ↓
PHASE 7
Testing + Error Handling
      ↓
PHASE 8
Documentation
      ↓
PHASE 9
Git + GitHub
      ↓
PHASE 10
Final Review
      ↓
PROJECT COMPLETE
```

---

## 💡 Why This Project Matters

Although the application is relatively small, it demonstrates an important pattern used in modern AI engineering:

```text
Natural Language
       ↓
LLM
       ↓
Structured Data
       ↓
Validation
       ↓
Application
```

This pattern appears in many production AI systems, including:

- Resume parsers
- Invoice extraction
- Medical document processing
- Customer-support systems
- Legal document analysis
- RAG pipelines
- AI agents
- Enterprise automation

The project therefore serves as a foundation for more advanced **Generative AI and AI Engineering applications**.

---

## 📜 License

This project is licensed under the MIT License.

See the `LICENSE` file for details.

---

## 👨‍💻 Author

**Robel**

AI / Machine Learning Engineer in training.

Focused on:

- Artificial Intelligence
- Machine Learning
- Deep Learning
- Generative AI
- NLP
- Computer Vision
- AI Engineering

---

## ⭐ Project Status

| Feature              | Status |
| --------------------- | ------ |
| Local TinyLlama        | ✅     |
| Gemini API             | ✅     |
| Prompt Engineering     | ✅     |
| Structured Output      | ✅     |
| Pydantic Validation    | ✅     |
| Streamlit UI           | ✅     |
| Testing                | ✅     |
| GitHub Ready           | ✅     |

**Current Release:** `Version 1.0`

---

## 🎬 Final Result

The **Movie Information Extractor** demonstrates a complete beginner-to-intermediate Generative AI application lifecycle:

```text
IDEA
 ↓
ENVIRONMENT
 ↓
LLM
 ↓
PROMPT
 ↓
STRUCTURED OUTPUT
 ↓
VALIDATION
 ↓
UI
 ↓
TESTING
 ↓
DOCUMENTATION
 ↓
GITHUB
```

**Project 1 — Movie Information Extractor 🚀**
