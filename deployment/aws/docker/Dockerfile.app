# Quest Analytics RAG Assistant - Main Application Container
# Production-ready Docker image for the Gradio web application with all dependencies
# Supports both local development and AWS Lambda deployment

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app
ENV PYTHONPATH=/app

# Install system dependencies required for sentence-transformers / opensearch / tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    libmagic1 \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-lambda.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-lambda.txt

COPY . /app
COPY lambda_app_handler.py /app/

# Environment defaults - can be overridden at runtime
# CRITICAL: These should be explicitly set in production (Lambda, etc.)
ENV ENVIRONMENT=local \
    OPENSEARCH_HOST= \
    OPENSEARCH_INDEX=quest-research \
    OPENSEARCH_TLS_VERIFY=false \
    OLLAMA_BASE_URL= \
    OLLAMA_MODEL= \
    OLLAMA_FALLBACK_MODEL= \
    OLLAMA_TIMEOUT=240 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SHARE_LINK=false \
    EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2 \
    SECURITY_ENABLED=false \
    ENABLE_ANALYTICS=false

EXPOSE 7860

# Use AWS Lambda Runtime Interface Client for Lambda container execution
# Falls back to direct Python execution for local/Docker Compose use
CMD ["python", "-m", "awslambdaric", "lambda_app_handler.lambda_handler"]
