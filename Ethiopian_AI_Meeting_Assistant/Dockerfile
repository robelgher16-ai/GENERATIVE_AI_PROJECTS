FROM python:3.11-slim

# System tools your code needs: ffmpeg (yt-dlp + whisper), tesseract (OCR), libgl (opencv)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p outputs downloads

ENV PYTHONUNBUFFERED=1
# Render provides $PORT automatically
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]