# Quest Analytics RAG Assistant - Main Application Container
# Production-ready Docker image for the Gradio web application with all dependencies

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app
ENV PYTHONPATH=/app

# Install system dependencies required for sentence-transformers / opensearch
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-lambda.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-lambda.txt

COPY . /app
COPY lambda_app_handler.py /app/

ENV OPENSEARCH_HOST= \
    OPENSEARCH_INDEX=quest-research \
    OPENSEARCH_TLS_VERIFY=false \
    OLLAMA_BASE_URL= \
    OLLAMA_MODEL=gemma3:1b \
    OLLAMA_FALLBACK_MODEL=phi3:mini \
    OLLAMA_TIMEOUT=240 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_SHARE_LINK=false \
    EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2 \
    SECURITY_ENABLED=false

EXPOSE 7860

# Use Lambda handler instead of web server
CMD ["lambda_app_handler.lambda_handler"]
