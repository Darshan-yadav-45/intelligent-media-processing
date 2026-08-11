FROM python:3.12-slim

# System deps: tesseract-ocr for OCR, libgl1/libglib for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads
RUN chmod +x start.sh

# Render (and most PaaS free tiers) assign the port dynamically via $PORT -
# don't hardcode 8000 in the CMD, read it at runtime instead (see start.sh).
EXPOSE 8000

CMD ["./start.sh"]