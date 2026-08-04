# 🧠 TextGenius: Psychological Quote & Insight Generator

TextGenius is an AI-powered application that leverages the **Gemini API** to act as an expert in psychology, human behavior, and mindset-building. When given any theme, emotion, or focus area, it generates a profound, original psychological quote paired with a concise cognitive breakdown.

---

## 🚀 Features

- **Custom Persona Generation:** Uses specialized system instructions to emulate a behavioral psychology expert.
- **Dual Interface Support:** Includes both a command-line script (`gemini_quote_app.py`)[cite: 1] and a modern web application interface built with **Streamlit** (`app.py`)[cite: 2].
- **Secure Configuration:** Protects credentials locally using a `.env` file and `python-dotenv`.

---

## 🛠️ Tech Stack

- **Python** (Core Logic)
- **Google GenAI SDK** (Gemini API Integration)[cite: 1, 2]
- **Streamlit** (Web UI Framework)[cite: 2]
- **Python-Dotenv** (Environment Management)

---

## 📂 Project Directory Structure

```text
GENERATIVE_AI_PROJECTS\Beginner_Projects\text-genius\
│
├── .env                  # Local environment file containing your GEMINI_API_KEY
├── .gitignore            # Files and folders ignored by Git
├── app.py                # Streamlit web application interface[cite: 2]
├── gemini_quote_app.py   # Command-line interface application[cite: 1]
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```
