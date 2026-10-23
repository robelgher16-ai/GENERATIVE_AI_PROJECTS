# Ethiopian AI Meeting Assistant

An AI-powered meeting analysis application that transforms meeting audio and video into searchable, bilingual meeting reports in **English and Amharic**. It combines speech transcription, visual text extraction, Gemini-powered report generation, and retrieval-augmented generation (RAG).

## Live Applications

- **Render:** https://ethiopian-ai-meeting-assistant.onrender.com
- **Streamlit Cloud:** https://ethiopian-ai-meeting-assistant.streamlit.app/

## Features

- **Audio transcription:** Extract spoken content from meetings using Faster-Whisper.
- **Video analysis:** Extract text from slides and video frames using OpenCV and Tesseract OCR.
- **Bilingual reports:** Generate English and Amharic meeting notes using Google Gemini.
- **AI meeting chat:** Ask questions about meeting content in English or Amharic.
- **Retrieval-augmented generation:** Search meeting records using ChromaDB and FastEmbed.
- **Downloadable reports:** Export generated meeting notes as Markdown files.
- **Interactive dashboard:** Monitor pipeline progress and inspect transcripts, extracted text, reports, and chat sources.

## Technology Stack

| Component          | Technology                           |
| ------------------ | ------------------------------------ |
| User interface     | Streamlit                            |
| API backend        | FastAPI                              |
| Speech recognition | Faster-Whisper                       |
| Video processing   | OpenCV                               |
| OCR                | Tesseract OCR                        |
| Generative AI      | Google Gemini                        |
| Vector database    | ChromaDB                             |
| Embeddings         | FastEmbed                            |
| Language           | Python                               |
| Deployment         | Render and Streamlit Community Cloud |

## Project Structure

```text
Ethiopian_AI_Meeting_Assistant/
├── app.py                  # Streamlit user interface
├── api.py                  # FastAPI backend
├── core/
│   ├── transcriber.py      # Audio transcription
│   ├── video_processor.py  # Video analysis and OCR
│   └── summarizer.py       # Bilingual report generation
├── rag/
│   ├── ingest_db.py        # Knowledge-base ingestion
│   └── chat_rag.py         # Retrieval and question answering
├── outputs/
│   ├── transcript.txt
│   ├── visual.txt
│   ├── meeting_notes_en.md
│   └── meeting_notes_amh.md
├── downloads/              # Downloaded or uploaded media
├── requirements.txt
├── packages.txt
├── Dockerfile
├── .env.example
└── README.md
```

_The structure above describes the main application components; generated files and optional configuration files may not exist until created._

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/robelgher16-ai/GENERATIVE_AI_PROJECTS.git
cd GENERATIVE_AI_PROJECTS/Ethiopian_AI_Meeting_Assistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install the required system tools as well:

- FFmpeg for media processing.
- Tesseract OCR with English and Amharic language data.

### 4. Configure the Gemini API key

Create a `.env` file in the project directory:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder with your own API key. Never commit `.env` or publish your API key.

### 5. Run the Streamlit application

```bash
streamlit run app.py
```

Open the local URL printed in the terminal.

### 6. Run the FastAPI backend

In a separate terminal, activate the same environment and run:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` to explore the API endpoints.

## How It Works

1. **Input:** Provide a YouTube URL or upload a supported audio or video file.
2. **Transcription:** Convert speech into text with Faster-Whisper.
3. **Visual extraction:** Analyze video frames and extract slide text using OCR.
4. **Report generation:** Use Gemini to create English and Amharic meeting notes.
5. **Knowledge-base ingestion:** Index meeting content in ChromaDB with FastEmbed.
6. **Interactive Q&A:** Ask questions and receive answers grounded in the meeting records.
7. **Export:** Read and download the generated reports.

## Deployment

The application can be deployed using Render or Streamlit Community Cloud.

- **Render:** Configure the service using the repository's Dockerfile and the appropriate application entry point.
- **Streamlit Community Cloud:** Set the main file path to `Ethiopian_AI_Meeting_Assistant/app.py`.

Configure `GEMINI_API_KEY` through the hosting provider's environment variables or secrets settings. Install FFmpeg and Tesseract OCR wherever the processing pipeline runs.

If the Streamlit interface runs the processing modules directly, those dependencies must be available in the Streamlit deployment. A separately deployed FastAPI backend is needed only if the frontend is configured to call it.

## Security and Limitations

- Keep API keys and other secrets out of source control.
- Large media files can require significant processing time and memory.
- Transcription and OCR accuracy depend on audio quality, video resolution, language, and background noise.
- Generated reports should be reviewed for accuracy before being used as official meeting records.
- Persistent storage may be needed if generated reports and vector databases must survive hosting restarts.

## Future Improvements

- Add support for Tigrinya and additional Ethiopian languages.
- Improve speaker identification and timestamped transcripts.
- Export reports to PDF and Word.
- Add user accounts and persistent meeting history.
- Improve background processing for long recordings.
- Expand the system with multilingual semantic search.

## Author

**Robel Gebregziabher**

AI Engineer | Generative AI | Machine Learning | Computer Vision

## License

Add a license that matches how you intend to distribute and reuse this project.
