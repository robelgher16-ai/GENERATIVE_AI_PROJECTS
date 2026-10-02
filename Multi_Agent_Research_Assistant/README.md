# Multi-Agent Research Assistant

An AI-powered research assistant that uses a multi-agent pipeline to
transform a research question into a structured research report.

The system combines web search, webpage reading, report generation, and
report criticism into four stages:

**Search → Reader → Writer → Critic**

## Live Applications

### Streamlit Frontend

https://generativeaiprojects-bqynw32ptopwg6qw3yhjdn.streamlit.app/

The Streamlit application provides the user interface for entering
research topics, viewing search results, reading scraped webpage
content, reviewing the generated report, viewing critic feedback, and
downloading research results.

### FastAPI Backend

https://generative-ai-projects-1.onrender.com

### FastAPI Documentation

https://generative-ai-projects-1.onrender.com/docs

The `/docs` page provides an interactive Swagger UI for testing the API.

## Architecture

```text
User
  │
  ▼
Streamlit Frontend
  │
  │ POST /ask
  ▼
FastAPI Backend
  │
  ▼
Research Pipeline
  │
  ├── Search Agent
  │      └── Finds relevant web sources
  │
  ├── Reader Agent
  │      └── Selects and scrapes a relevant webpage
  │
  ├── Writer
  │      └── Generates the research report
  │
  └── Critic
         └── Reviews the generated report
  │
  ▼
JSON Response
  │
  ▼
Streamlit Results
```

## Features

- Research topic input through a Streamlit interface
- Web search using the DDGS search library
- Reader agent for selecting and scraping web content
- AI-generated research reports
- Critic agent for reviewing generated reports
- Separate result tabs for:
  - Search
  - Reader
  - Report
  - Critic
- Research pipeline status overview
- Developer view for inspecting pipeline state
- Download research reports as:
  - TXT
  - Markdown
  - JSON
- FastAPI backend with Swagger documentation
- Separate frontend and backend deployment

## Agent Pipeline

### 1. Search Agent

The Search Agent receives the research topic and searches the web for
relevant sources.

### 2. Reader Agent

The Reader Agent selects a relevant webpage and retrieves its content
for the next stage of the pipeline.

### 3. Writer

The Writer processes the retrieved information and produces a structured
research report.

### 4. Critic

The Critic reviews the generated report and returns feedback about the
result.

## Project Structure

```text
Multi_Agent_Research_Assistant/
│
├── app.py
├── api.py
├── Agents.py
├── tools.py
├── pipeline.py
├── backuptool.py
├── requirements.txt
├── requirements_streamlit.txt
├── .env
├── .gitignore
└── .venv/
```

### Main Files

File Purpose

---

`app.py` Streamlit frontend
`api.py` FastAPI backend
`pipeline.py` Main research pipeline
`Agents.py` Agent definitions and chains
`tools.py` Search and webpage scraping tools
`requirements.txt` Backend/development dependencies
`requirements_streamlit.txt` Streamlit deployment dependencies

## API

### Endpoint

```text
POST /ask
```

### Request

```json
{
  "topic": "What is machine learning?"
}
```

### Response

```json
{
  "topic": "What is machine learning?",
  "search_results": "...",
  "scraped_content": "...",
  "report": "...",
  "critic_feedback": "..."
}
```

## Local Backend Setup

Clone the repository and move into the project directory:

```bash
cd Multi_Agent_Research_Assistant
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file and add the required API credentials:

```text
GOOGLE_API_KEY=your_google_api_key
SERPER_API_KEY=your_serper_api_key
```

Never commit `.env` or API keys to GitHub.

Run the FastAPI backend:

```bash
python -m uvicorn api:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Local Streamlit Setup

Install the Streamlit dependencies:

```bash
pip install -r requirements_streamlit.txt
```

Run the frontend:

```bash
streamlit run app.py
```

## Deployment

### Backend --- Render

The FastAPI backend is deployed on Render.

Start command:

```text
uvicorn api:app --host 0.0.0.0 --port $PORT
```

Backend:

https://generative-ai-projects-1.onrender.com

### Frontend --- Streamlit Cloud

The Streamlit frontend is deployed separately from the FastAPI backend.

Frontend:

https://generativeaiprojects-bqynw32ptopwg6qw3yhjdn.streamlit.app/

The Streamlit application communicates with the FastAPI `/ask` endpoint.

## Technology Stack

- Python
- Streamlit
- FastAPI
- Uvicorn
- LangChain
- LangGraph
- Google Gemini
- DDGS
- BeautifulSoup
- Requests
- Pydantic
- python-dotenv

## Security

API keys should be stored as environment variables or deployment
secrets.

Do not commit:

```text
.env
```

or expose API keys in source code, README files, screenshots, or public
repositories.

For Streamlit Cloud, secrets should be configured through the
application's **Secrets** settings.

For Render, API keys should be configured through the service's
**Environment Variables**.

## Project Workflow

```text
Research Question
       ↓
Search Agent
       ↓
Web Sources
       ↓
Reader Agent
       ↓
Scraped Content
       ↓
Writer
       ↓
Research Report
       ↓
Critic
       ↓
Feedback
       ↓
Streamlit Interface
```

## Future Improvements

- Add more specialized research agents
- Improve source selection and ranking
- Add citation extraction and source verification
- Add persistent research history
- Add PDF report generation
- Add authentication
- Add configurable research depth
- Add more LLM providers
- Improve error handling and API monitoring

## Author

**Robel Gebregziabher**

AI / Machine Learning / Generative AI Projects

## License

This project is intended for educational and portfolio purposes.
