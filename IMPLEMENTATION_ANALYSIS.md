# Implementation Analysis: deployment/app_gradio.py & Docker/

## 1. Application Architecture

### deployment/app_gradio.py - Main Gradio Interface

**Entry Point:**
```python
def main() -> None:
    dependencies = load_dependencies()
    prompts = load_prompt_templates(PROMPT_PATH)
    state = AssistantState(deps=dependencies, prompt_template=prompts)
    app = build_interface(state)
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=share_env in {"1", "true", "yes"}
    )

if __name__ == "__main__":
    main()
```

**Key Components:**

1. **load_dependencies()** - Initializes RAG pipeline
   - Creates OpenSearch client (if OPENSEARCH_HOST set)
   - Loads embedding model (Sentence Transformers)
   - Initializes Ollama chat adapter
   - Creates HybridRetriever for document search
   - Returns AssistantDependencies object

2. **build_interface()** - Creates Gradio UI
   - Professional header with branding
   - Real-time health monitoring with visual indicators
   - Three tabs: Document Ingestion | Research Chat | Configuration
   - Chat with conversation history
   - Document upload with progress tracking
   - Model configuration settings
   - Responsive design with custom CSS

3. **Health Monitoring**
   - Real-time Ollama status checking
   - Visual indicators: 🟢 (healthy) 🟡 (slow) 🔴 (unreachable) ⚪ (checking)
   - Adaptive polling intervals
   - Toast notifications when service becomes unreachable

4. **Security Features**
   - Rate limiting on uploads and chat (20 req/min)
   - Input sanitization (XSS, SQL injection protection)
   - File validation (type, size, malware scanning)
   - Security headers

5. **RAG Pipeline Functions**
   - `ingest_files()` - Process uploaded PDFs (OCR, embeddings, indexing)
   - `answer_question()` - Retrieve docs, generate prompt, query LLM
   - `run_health_check()` - Monitor Ollama service

---

## 2. Docker Setup (deployment/aws/docker/)

### Dockerfile.app - Gradio Container

**Structure:**
- Multi-stage build for efficiency
- Python 3.11-slim base
- System deps: tesseract, ffmpeg, etc.
- Installs requirements.txt + requirements-lambda.txt
- Copies entire application

**Environment Variables (NEW):**
```dockerfile
ENV ENVIRONMENT=local \
    OPENSEARCH_HOST= \
    OLLAMA_BASE_URL= \
    OLLAMA_MODEL= \
    OLLAMA_FALLBACK_MODEL= \
    OLLAMA_TIMEOUT=240 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2 \
    SECURITY_ENABLED=false \
    ENABLE_ANALYTICS=false
```

**CMD:** `["python", "-m", "awslambdaric", "lambda_app_handler.lambda_handler"]`
- Uses AWS Lambda Runtime Interface Client for Lambda execution
- Docker Compose overrides with: `python deployment/app_gradio.py`

### Dockerfile.landing - FastAPI Landing Page

**Same pattern as Dockerfile.app:**
- Lightweight Python 3.11-slim
- Minimal system dependencies
- Clear production/local environment support
- CMD: awslambdaric for Lambda

### Dockerfile.worker - Background Processing

**Purpose:** Document ingestion worker
- Watches input directory for files
- Processes PDFs with OCR
- Generates embeddings
- Indexes into OpenSearch

---

## 3. Docker Compose Setup (docker-compose.dev.yml)

### Services

**opensearch**
```yaml
image: opensearchproject/opensearch:2.18.0
ports: 9200:9200
environment:
  - discovery.type: single-node
  - plugins.security.disabled: "true"
```

**ollama**
```yaml
image: ollama/ollama:latest
ports: 11434:11434
volumes: ${HOME}/.ollama:/root/.ollama
```

**rag-app**
```yaml
build: ../../.. / deployment/aws/docker/Dockerfile.app
ports: 7860:7860
environment:
  OPENSEARCH_HOST: http://opensearch:9200  # Internal hostname
  OLLAMA_BASE_URL: http://ollama:11434     # Internal hostname
  OLLAMA_MODEL: ${OLLAMA_MODEL:-gemma3:1b}
  OLLAMA_FALLBACK_MODEL: ${OLLAMA_FALLBACK_MODEL:-phi3:mini}
command: ["python", "deployment/app_gradio.py"]  # Override Lambda CMD
```

**landing**
```yaml
ports: 3000:3000
environment:
  APP_URL: ${APP_URL:-http://localhost:7860}  # Local fallback
command: ["python", "-m", "landing.main"]
```

---

## 4. Data Flow

### Local Execution (Docker Compose)
```
User Browser (http://localhost:3000)
    ↓
landing/main.py (FastAPI)
    ↓ (links to http://rag-app:7860)
deployment/app_gradio.py (Gradio)
    ↓
load_dependencies()
    ├→ OpenSearch (http://opensearch:9200)
    ├→ Ollama (http://ollama:11434)
    └→ HybridRetriever
    
Document Upload Flow:
    User ↓
    Gradio file upload
    ↓
    ingest_files() → ingest_and_index_document()
    ↓ (with security checks)
    Sentence Transformers (embeddings)
    ↓
    OpenSearch (indexing)

Chat Flow:
    User question ↓
    handle_question() → answer_question()
    ↓
    HybridRetriever.retrieve() (BM25 + vector search)
    ↓
    Format context → generate prompt
    ↓
    OllamaChatAdapter.invoke_messages()
    ↓
    Ollama service (http://ollama:11434)
    ↓
    Format response with citations
    ↓
    Update Gradio chatbot
```

### AWS Lambda Execution
```
Lambda URL Request
    ↓
lambda_app_handler.lambda_handler()
    ↓ (Mangum ASGI adapter)
deployment.app_gradio.build_interface()
    ↓
load_dependencies()
    ├→ OpenSearch (AWS managed)
    ├→ Ollama (EC2/ECS service)
    └→ HybridRetriever
    
(Same flow as above, but with:
 - OpenSearch via https://domain.us-east-1.es.amazonaws.com:9200
 - Ollama via https://ollama.your-domain.com)
```

---

## 5. Configuration Flow

### Environment Variables Resolution

**Landing Page (landing/main.py):**
1. Tries to load from environment: `os.getenv("APP_URL")`
2. If not set:
   - Production → raises ValueError
   - Local → defaults to "http://localhost:7860"

**Gradio App (deployment/app_gradio.py):**
1. `load_dependencies()` checks `os.getenv("OLLAMA_BASE_URL")`
2. `update_llm_settings()` validates it's set

**Docker Compose:**
- Loads from `.env` file with defaults
- Example `.env`:
  ```
  OLLAMA_MODEL=gemma3:1b
  OLLAMA_FALLBACK_MODEL=phi3:mini
  OLLAMA_TIMEOUT=240
  APP_URL=http://localhost:7860
  ENABLE_ANALYTICS=false
  ```

**Terraform (for AWS):**
- Passes variables to Lambda environment
- Example `terraform.tfvars`:
  ```hcl
  ollama_base_url = "https://ollama.company.com"
  opensearch_host = "domain.us-east-1.es.amazonaws.com:9200"
  ollama_model = "llama2"
  ```

---

## 6. Security Implementation

### Input Validation
- File upload validation (type, size, malware)
- Query sanitization (XSS, SQL injection)
- Rate limiting per IP per endpoint

### Security Middleware
Located in `rag_pipeline/security.py`:
- `SecurityMiddleware` class
- `rate_limiter` - IP-based throttling
- `sanitizer` - Input/file validation

---

## 7. Current Testing

### Local Testing with docker-start.sh
```bash
# Start services
./docker-start.sh start

# View logs
./docker-start.sh logs

# Check status
./docker-start.sh status

# Run health checks
./docker-start.sh test

# Cleanup
./docker-start.sh clean
```

### What Works
✓ Docker Compose orchestrates all services
✓ app_gradio.py loads and runs correctly
✓ Environment variables pass correctly
✓ Health monitoring shows service status
✓ Document upload and chat work
✓ OpenSearch indexing works
✓ Ollama integration works

### What Was Fixed
✓ Added ENVIRONMENT=local to Dockerfiles
✓ Added environment variable validation in code
✓ Updated Terraform to pass all variables
✓ Made docker-start.sh work with correct paths

---

## 8. Deployment Checklist

### Before Local Testing
- [ ] Verify docker-compose.dev.yml exists at deployment/aws/docker/
- [ ] Check .env file with model defaults
- [ ] Ensure ports 3000, 7860, 9200, 11434 are available

### Before AWS Deployment
- [ ] Test locally with `./docker-start.sh start`
- [ ] Build and push container images
- [ ] Set terraform.tfvars with production URLs
- [ ] Run `terraform apply`
- [ ] Verify Lambda logs

---

## Notes

1. **Lambda Cold Start**: ~30-45 seconds due to Gradio initialization
2. **Model Caching**: Ollama caches models in volume, first pull takes time
3. **Memory**: Lambda needs 1GB+ memory for Gradio + dependencies
4. **Timeout**: Lambda timeout set to 180s for Gradio cold start
5. **Health Checks**: UI shows real-time Ollama status (updates every 30-45s)

