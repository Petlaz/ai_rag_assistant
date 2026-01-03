FROM python:3.11-slim as base

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

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV OPENSEARCH_HOST=http://opensearch:9200 \
    OPENSEARCH_INDEX=quest-research \
    OPENSEARCH_TLS_VERIFY=false \
    OLLAMA_BASE_URL=http://ollama:11434 \
    OLLAMA_MODEL=gemma3:1b \
    OLLAMA_FALLBACK_MODEL=phi3:mini \
    OLLAMA_TIMEOUT=240 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_SHARE_LINK=false \
    EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

EXPOSE 7860

CMD ["python", "deployment/app_gradio.py"]
