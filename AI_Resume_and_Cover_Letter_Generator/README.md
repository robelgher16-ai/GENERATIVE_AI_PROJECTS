# AI Resume & Cover Letter Generator

An AI-powered application that helps job seekers create **job-tailored resumes, cover letters, skills matching, and improvement suggestions** based on their existing resume and a target job description.

The project uses **Google Gemini**, **LangChain**, **FastAPI**, and **Streamlit** to provide an AI-powered application workflow.

## Features

- Generate job-tailored resume content
- Generate personalized cover letters
- Compare resume skills with job requirements
- Identify missing or relevant skills
- Suggest areas for improvement
- AI-powered application analysis
- FastAPI backend
- Streamlit interactive frontend
- Environment-variable based API key management
- PDF generation support

## Project Architecture

```text
AI_Resume_and_Cover_Letter_Generator/
│
├── api/
│   └── main.py
│
├── src/
│   └── generator.py
│
├── app.py
├── main.py
├── .gitignore
└── README.md
```

## Technologies

- Python
- Google Gemini
- LangChain
- FastAPI
- Streamlit
- ReportLab
- python-dotenv
- Uvicorn

## How It Works

```text
Resume + Job Description
          │
          ▼
     Streamlit UI
          │
          ▼
      FastAPI API
          │
          ▼
    LangChain + Gemini
          │
          ▼
  AI Application Analysis
          │
          ├── Tailored Resume
          ├── Cover Letter
          ├── Skills Matching
          └── Improvement Areas
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/robelgher16-ai/GENERATIVE_AI_PROJECTS.git
```

### 2. Open the project

```bash
cd GENERATIVE_AI_PROJECTS/AI_Resume_and_Cover_Letter_Generator
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project directory:

```env
GOOGLE_API_KEY=your_google_api_key
```

**Never commit your `.env` file or API credentials to GitHub.**

The project `.gitignore` is configured to keep sensitive credentials out of version control.

## Running the FastAPI Backend

From the project directory:

```bash
uvicorn api.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI automatically provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

## Running the Streamlit Frontend

In another terminal:

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

## API

The backend provides endpoints for AI-powered job application generation and analysis.

Example API workflow:

```text
POST /ask
```

The API receives application-related information and uses Gemini to generate the requested output.

Interactive API documentation is available through FastAPI's Swagger UI.

## Deployment

The project can be deployed using:

### Backend

**Render**

Deploy the FastAPI backend and configure the required environment variables in the Render dashboard.

Example start command:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Frontend

**Streamlit Community Cloud**

Deploy `app.py` and configure the required secrets through the Streamlit settings.

Do not upload API keys directly into the repository.

## Security

Sensitive files are excluded from Git using `.gitignore`, including:

```text
.env
credentials.json
.venv/
__pycache__/
```

API keys should always be stored using environment variables or the secret-management systems provided by the deployment platform.

## Future Improvements

- Resume PDF/DOCX upload
- More advanced resume parsing
- ATS compatibility analysis
- Job description keyword extraction
- Resume scoring and explanation
- Multiple resume templates
- DOCX export
- Improved application tracking
- User authentication
- Application history

## Author

**Robel Gebregziabher**

Information Technology Student | AI Engineer | Machine Learning & Generative AI

GitHub: https://github.com/robelgher16-ai

---

## License

This project is intended for educational, portfolio, and development purposes.
