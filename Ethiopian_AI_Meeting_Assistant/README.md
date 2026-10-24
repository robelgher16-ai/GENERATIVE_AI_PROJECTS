# 🎙️ Ethiopian AI Meeting Assistant

Turn meeting audio or video into structured reports in **English and Amharic (አማርኛ)**, then ask questions about the meeting.

## 🚀 Live Demo

- **Streamlit app:** https://ethiopian-ai-meeting-assistant.streamlit.app/
- **FastAPI backend:** https://ethiopian-ai-meeting-assistant-api.onrender.com
- **API documentation:** https://ethiopian-ai-meeting-assistant-api.onrender.com/docs
- **API health check:** https://ethiopian-ai-meeting-assistant-api.onrender.com/health

## ⚠️ Important: Please Avoid YouTube Links

**Recommended: upload an audio or video file directly instead of pasting a YouTube link.**

YouTube may block automated downloads with messages such as “Sign in to confirm you’re not a bot.” This is a restriction from YouTube and can occur even when the application is configured correctly. As a result, YouTube-link processing is **not guaranteed to work**.

For the most reliable experience:

1. Obtain an audio/video file that you are allowed to use.
2. Choose **Upload file** in the app.
3. Upload the file and start the analysis.

Please do not repeatedly retry a YouTube link after a bot-verification error. Use the file-upload option instead. Do not provide browser cookies or passwords to the app.

## ✨ Features

- 🎧 Process meeting audio and video files.
- 📝 Generate an **English meeting report**.
- 🇪🇹 Generate an **Amharic meeting report (የአማርኛ ሪፖርት)**.
- 💬 Chat with the meeting and ask follow-up questions about its content.
- 🖼️ Optional slide-text extraction using OCR; skip OCR when you want a faster run.
- 🌐 Streamlit user interface backed by a FastAPI service.

## 🧭 How to Use

1. Open the [Ethiopian AI Meeting Assistant](https://ethiopian-ai-meeting-assistant.streamlit.app/).
2. Upload an audio/video file. **File upload is recommended over YouTube links.**
3. Choose whether to skip slide-text (OCR) extraction.
4. Start the analysis and wait for processing to finish.
5. Review the English report and Amharic report.
6. Use the chat section to ask questions about the meeting.

## 🏗️ Architecture

- **Frontend:** Streamlit
- **Backend:** FastAPI
- **Speech transcription:** Whisper-based transcription components
- **Language-model features:** Gemini API
- **Retrieval and chat:** LangChain / vector-store components used by the project
- **Optional visual text extraction:** OpenCV and Tesseract OCR

The deployed frontend communicates with the backend API. The API also exposes interactive documentation at `/docs`.

## 🛠️ Local Development

### Requirements

- Python version compatible with the project's pinned dependencies
- FFmpeg and any system dependencies required by the audio/video processing packages
- A Gemini API key

### Configure environment variables

Create a local `.env` file based on the project's `.env.example` (if present) and add the required secret values. Keep `.env` out of version control.

For the backend, configure the Gemini key in the backend service's environment. For deployment, set secrets in the hosting provider's environment-variable settings rather than hard-coding them into source files.

### Run the backend

From the project directory, activate your virtual environment, install the backend requirements used by this project, then run:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

If your local project uses a different ASGI module or a separate backend requirements file, use the module and requirements file configured for that checkout.

### Run the Streamlit frontend

In a second terminal, set the API URL to your local backend and launch the Streamlit app. On Windows PowerShell:

```powershell
$env:API_URL="http://localhost:8000"
streamlit run app.py
```

Use the actual Streamlit entry-point path if it differs in your checkout.

## 🔐 Security Notes

- Never commit `.env`, API keys, browser cookies, or other credentials.
- Store deployment secrets in Render/Streamlit environment settings.
- Treat uploaded meeting recordings and generated reports as potentially sensitive information.
- Do not upload recordings unless you have permission to process them.

## ⚠️ Limitations

- YouTube may refuse automated downloads; therefore, **direct file upload is the recommended input method**.
- Transcription and generated reports may contain mistakes. Review important names, figures, decisions, and action items.
- Processing speed depends on recording length, model availability, and hosting resources.
- The hosted service may take time to wake up after inactivity.

## 📌 Project

Part of the [`GENERATIVE_AI_PROJECTS`](https://github.com/robelgher16-ai/GENERATIVE_AI_PROJECTS) portfolio repository.

---

Built to make meeting information easier to review in English and Amharic.
