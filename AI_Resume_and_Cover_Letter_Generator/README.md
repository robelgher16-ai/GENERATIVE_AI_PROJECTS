# AI Resume & Cover Letter Generator

An AI-powered application that helps job seekers create **job-tailored resumes, personalized cover letters, skills matching, and improvement suggestions** based on their existing resume and a target job description.

The project uses **Google Gemini, LangChain, FastAPI, and Streamlit** to provide an end-to-end AI-powered job application workflow.

## Live Application

### Streamlit Frontend

**Live Application:**
https://ai-resume-cover-letter-generator-robel.streamlit.app/

### FastAPI Backend

**Live API:**
https://ai-resume-cover-letter-generator-0mw9.onrender.com

**Interactive Swagger API Documentation:**
https://ai-resume-cover-letter-generator-0mw9.onrender.com/docs

---

## Features

- Generate job-tailored resume content
- Generate personalized cover letters
- Compare resume skills with job requirements
- Identify missing or relevant skills
- Suggest areas for improvement
- AI-powered job application analysis
- FastAPI backend
- Streamlit interactive frontend
- Google Gemini integration
- Environment-variable based API key management
- PDF generation support

---

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
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Technologies

- Python
- Google Gemini
- LangChain
- FastAPI
- Streamlit
- ReportLab
- python-dotenv
- Uvicorn

---

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

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/robelgher16-ai/GENERATIVE_AI_PROJECTS.git
```

### 2. Open the Project

```bash
cd GENERATIVE_AI_PROJECTS/AI_Resume_and_Cover_Letter_Generator
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project directory:

```env
GEMINI_API_KEY=your_google_gemini_api_key
```

> **Never commit your `.env` file or API credentials to GitHub.**

The project `.gitignore` is configured to keep sensitive credentials out of version control.

For deployed applications, configure the API key using the platform's environment-variable or secret-management system.

---

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

---

## Running the Streamlit Frontend

In another terminal:

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

---

## API

The FastAPI backend provides endpoints for AI-powered job application generation and analysis.

### Generate Application Materials

```text
POST /generate
```

The endpoint receives a resume and job description and uses Gemini to generate job-tailored application materials.

Example request:

```json
{
  "resume": "I am a 4th-year Information Technology student with experience in Python, Machine Learning, Deep Learning, Generative AI, FastAPI, Streamlit, and GitHub.",
  "job_description": "We are looking for an AI/ML Engineering Intern with knowledge of Python, machine learning, deep learning, and generative AI."
}
```

### Interactive API Documentation

The complete API documentation is available through the deployed Swagger UI:

https://ai-resume-cover-letter-generator-0mw9.onrender.com/docs

---

## Deployment

### Backend — Render

The FastAPI backend is deployed on Render.

**Live Backend:**

https://ai-resume-cover-letter-generator-0mw9.onrender.com

**Swagger Documentation:**

https://ai-resume-cover-letter-generator-0mw9.onrender.com/docs

Start command:

```bash
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

The `GEMINI_API_KEY` is configured as an environment variable on the deployment platform.

### Frontend — Streamlit Community Cloud

The Streamlit frontend is deployed on Streamlit Community Cloud.

**Live Application:**

https://ai-resume-cover-letter-generator-robel.streamlit.app/

The frontend communicates with the deployed FastAPI backend.

---

## Security

Sensitive files are excluded from Git using `.gitignore`, including:

```text
.env
credentials.json
.venv/
__pycache__/
```

API keys should always be stored using environment variables or the secret-management systems provided by deployment platforms.

---

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
- More advanced job matching
- Resume-to-job compatibility scoring

---

## Author

**Robel Gebregziabher**

Information Technology Student | AI Engineer | Machine Learning & Generative AI

GitHub:
https://github.com/robelgher16-ai

---

## License

This project is intended for educational, portfolio, and development purposes.
