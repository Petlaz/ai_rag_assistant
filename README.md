# AI RAG Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenSearch](https://img.shields.io/badge/OpenSearch-2.18.0-005EB8?style=flat&logo=opensearch&logoColor=white)](https://opensearch.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.ai/)
[![Gradio](https://img.shields.io/badge/Gradio-6.2.0-FF6C37?style=flat&logo=gradio&logoColor=white)](https://gradio.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-Deployed-FF9900?style=flat&logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow%20%7C%20Monitoring-8B5CF6?style=flat)](https://mlflow.org/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat&logo=githubactions&logoColor=white)](https://github.com/features/actions)

A production-oriented Retrieval-Augmented Generation assistant for research and document analysis. The system ingests PDFs, builds searchable knowledge bases, retrieves the most relevant passages using hybrid search, and answers domain questions with local LLM inference while preserving privacy and keeping infrastructure costs low.

## Status

- Production deployment available on AWS Lambda
- Live app: https://k4mtt3o2lvjpo7f673h7yqq3ou0vixyy.lambda-url.us-east-1.on.aws/
- Core metrics: approximately 224 ms average response time and 87.5% precision in the optimized configuration
- Estimated operating cost: approximately $4-13/month depending on usage and deployment mode

## What We Built

This project is a research-focused RAG system designed to help teams work with scientific literature and other document collections more efficiently. It supports:

- PDF ingestion and document processing
- Chunking, metadata extraction, and embedding generation
- Hybrid search combining BM25 and vector retrieval
- Local LLM-powered Q&A with citation-oriented responses
- Session-based document management to avoid cross-contamination between research tasks
- Monitoring, alerting, and deployment automation for production use

The solution is built for teams that need a practical, low-cost alternative to large external API-based systems while keeping full control over data, search behavior, and deployment decisions.

## Why We Built It

Research teams often work with too many documents to review manually and too much information to process efficiently. Common pain points include:

- slow literature reviews
- difficulty finding relevant evidence across large collections
- fragmented document workflows
- inconsistent retrieval quality when searching domain-specific content
- cost and privacy concerns with public cloud AI APIs

This project addresses those issues by combining:

- document ingestion and indexing
- semantic and lexical retrieval
- local LLM inference
- production monitoring and deployment automation

The result is a system that reduces manual review effort while still being operationally practical for a small team or a cost-conscious research environment.

## Architecture Overview

```text
┌──────────────────────────────┐
│        User Interface        │
│  Gradio + FastAPI landing    │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   RAG Processing Layer       │
│ PDF ingest → chunk → embed  │
│ → hybrid retrieve → LLM      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Search and Storage Layer   │
│  OpenSearch + metadata      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│    Model Runtime Layer       │
│       Ollama + fallback      │
└──────────────────────────────┘
```

### Core design principles

- Hybrid search: combine keyword matching and semantic similarity
- Session isolation: keep document context scoped to the active task
- Local-first inference: reduce privacy and usage-cost concerns
- Modular architecture: separate ingestion, retrieval, UI, and deployment concerns
- Production readiness: monitoring, alerting, rollback, and smoke testing built into the workflow

## Technology Choices and Rationale

### Core stack

| Layer | Technology | Why it was chosen |
|---|---|---|
| Interface | Gradio, FastAPI | Rapid Python-first development with usable UI and landing page |
| Embeddings | SentenceTransformers | Open-source, local, cost-effective, easy to swap models |
| Retrieval | OpenSearch | Supports hybrid search with both vector and keyword retrieval |
| LLM runtime | Ollama | Local execution, privacy-friendly, lower operational cost |
| Deployment | AWS Lambda + Docker | Lightweight serverless deployment with lower cost and simpler ops |
| Infrastructure | Terraform | Reproducible and auditable infrastructure setup |
| CI/CD | GitHub Actions | Integrated automation for build, validation, and deployment |
| Monitoring | CloudWatch, custom scripts | Production visibility and alerting for operational health |

### Why these choices were reasonable

- OpenSearch was preferred over fully managed vector-only services because it supports hybrid search and reduces vendor lock-in.
- Ollama was preferred over cloud-hosted LLM APIs because it keeps sensitive research content local and avoids variable per-query cost.
- SentenceTransformers was selected because it offers an open-source, flexible embedding layer without requiring external API dependencies.
- Gradio was chosen to accelerate development and keep the project focused on the RAG workflow rather than frontend engineering overhead.
- Lambda was preferred where appropriate because it is operationally light and affordable for a research-focused workload.

## Key Features

- Hybrid retrieval using BM25 and vector similarity
- PDF ingestion and metadata extraction
- Local LLM support with model health checks and fallback logic
- Research-oriented prompts and output guardrails
- Production deployment automation
- Monitoring and alerting for application and infrastructure health
- Document session isolation
- Cost-conscious serverless deployment model

## AI-Assisted Development Approach

The project used several AI tools during development. The important point is not that AI wrote the entire system, but that it accelerated prototyping, reduced repetitive implementation work, and helped structure complex components more quickly and consistently.

### Which AI tools were used?

- ChatGPT
- Claude
- GitHub Copilot
- Codex

### How they were used

#### 1. Architecture design and system planning
- assisted with structural decomposition of ingestion, retrieval, indexing, and LLM layers
- helped outline modular boundaries and deployment concerns
- supported early design discussions around performance, privacy, and cost trade-offs

#### 2. Implementation support
- generated boilerplate for API, search client, web UI, and infrastructure code
- helped draft scripts for model evaluation, deployment automation, and monitoring
- assisted with PDF processing and pipeline orchestration logic

#### 3. Security and operational hardening
- supported threat modeling and defensive coding patterns
- helped design logging, monitoring, and alerting workflows
- assisted with infrastructure validation and runtime configuration review

#### 4. Documentation and knowledge transfer
- helped explain complex code paths and summarize system decisions
- generated structured documentation and implementation guides
- supported reproducibility and onboarding for future contributors

### How did we verify the AI-generated code actually worked?

AI-generated code was not treated as final output without validation. Every major implementation was checked against real project behavior using a layered verification workflow:

- unit tests for isolated components
- integration tests for the ingest → embed → index → retrieve flow
- smoke tests for end-to-end application behavior
- production validation checks for configuration and service availability
- performance comparisons against retrieval and latency benchmarks
- manual review of generated code against project requirements, architecture, and security constraints

This kept the AI-assisted workflow grounded in execution, not just generation. In practice, the strongest model was not AI alone, but AI-assisted implementation combined with engineering review and system-level testing.

## AI Suggestions Rejected

Several AI-generated suggestions were considered but rejected because they did not align with the project goals.

### 1. Using a NoSQL document store for metadata
Rejected because the workload benefits from structured metadata and predictable query patterns. The architecture stayed centered on clear, queryable document metadata.

### 2. Replacing OpenSearch with a managed vector database
Rejected due to cost, vendor lock-in, and reduced control over hybrid search behavior.

### 3. Using GPT-4 API for all LLM processing
Rejected due to privacy concerns, higher recurring cost, and latency sensitivity for a document-heavy workflow.

### 4. Using a generic RAG framework instead of a custom pipeline
Rejected because a custom implementation allowed better control over evaluation, optimization, retrieval behavior, and deployment constraints.

### 5. Moving to Kubernetes too early
Rejected because it would add operational complexity without providing a clear benefit for the current scale and cost envelope.

## Performance and Quality

The optimized configuration achieved the following results in project testing:

- average response time: ~224 ms
- baseline comparison: ~40% improvement over the earlier configuration
- precision: ~87.5%
- hybrid retrieval balanced keyword precision and semantic recall

This is not a claim of universal benchmark leadership; it reflects the project’s own evaluation setup and use case.

## Limitations

The current implementation is strong for a focused research workload, but it is not a universal enterprise platform.

- Retrieval quality depends on domain fit and model choice
- Context window limits restrict how much evidence can be included in a single answer
- The architecture is primarily single-tenant and designed for one deployment context
- Ingestion is batch-oriented rather than fully real-time
- Lambda execution constraints impose practical limits on very large jobs
- Authentication is currently simpler than a full enterprise RBAC model
- Observability can be expanded with deeper distributed tracing and richer telemetry

## What We Would Do Differently Next Time

1. Start with broader model benchmarking before locking in the embedding approach.
2. Add monitoring and alerting at project start instead of during later production hardening.
3. Establish automated tests earlier in the lifecycle.
4. Validate real user workflow requirements before finalizing architecture.
5. Put cost modeling in the design phase, not as a post hoc optimization exercise.
6. Build resilience patterns into the initial design instead of retrofitting them.
7. Run structured security review and load testing earlier.
8. Keep documentation updated as code evolves instead of doing it mostly at the end.
9. Use staged deployment patterns more aggressively for production rollouts.
10. Reassess whether self-hosted or managed services are optimal as workload scale grows.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- 8 GB+ RAM for local model workloads
- 4 GB+ free disk space for OpenSearch and model storage

### 1. Clone and set up the environment

```bash
git clone https://github.com/Petlaz/ai_rag_assistant.git
cd ai_rag_assistant

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp configs/secrets.template.env .env
```

### 2. Configure environment variables

The application expects variables such as:

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
OPENSEARCH_HOST=http://localhost:9200
OPENSEARCH_INDEX=quest-research
OPENSEARCH_TLS_VERIFY=false
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

### 3. Start the stack

```bash
docker compose -f deployment/aws/docker/docker-compose.dev.yml up --build
```

### 4. Access the app

- Landing page: http://localhost:3000
- RAG assistant: http://localhost:7860
- OpenSearch: http://localhost:9200
- Ollama API: http://localhost:11434

### 5. Run tests

```bash
pytest tests/ -v
```

## Usage

### Document ingestion

Upload PDFs through the app or run a batch ingestion job:

```bash
python scripts/run_ingestion.py /path/to/pdfs/*.pdf --index quest-research --clear
```

### Querying the system

Use the Gradio interface to ask questions against the indexed documents. The system is optimized for research-style Q&A, evidence retrieval, and source-aware summarization.

### Health checks

The app includes monitoring endpoints and status checks for:

- Gradio app availability
- Ollama status
- OpenSearch health

## Configuration

### Required environment variables

| Variable | Description |
|---|---|
| `OPENSEARCH_HOST` | OpenSearch endpoint |
| `OPENSEARCH_INDEX` | Collection index name |
| `OPENSEARCH_TLS_VERIFY` | TLS verification setting |
| `OLLAMA_BASE_URL` | Ollama server URL |
| `OLLAMA_MODEL` | Default inference model |
| `OLLAMA_FALLBACK_MODEL` | Fallback model |
| `OLLAMA_TIMEOUT` | Request timeout |
| `EMBEDDING_MODEL_NAME` | Embedding model name |
| `GRADIO_SERVER_PORT` | UI port |

## Deployment

### Local development

```bash
docker compose -f deployment/aws/docker/docker-compose.dev.yml up
```

### Production deployment

The project includes infrastructure automation for AWS deployment with Terraform and GitHub Actions. The deployment workflow includes validation, image build, infrastructure provisioning, and post-deployment smoke testing.

Relevant references:

- [docs/DEPLOY_NOW.md](docs/DEPLOY_NOW.md)
- [docs/PRODUCTION_DEPLOYMENT_ROADMAP.md](docs/PRODUCTION_DEPLOYMENT_ROADMAP.md)
- [docs/LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md)
- [deployment/aws/AWS_DEPLOYMENT_GUIDE.md](deployment/aws/AWS_DEPLOYMENT_GUIDE.md)

## Testing and Evaluation

The project includes a practical evaluation workflow for retrieval quality and operational reliability.

### Retrieval and benchmark checks

```bash
python scripts/eval_retrieval.py data/samples/queries.jsonl --top-k 5
python scripts/smoke_test.py --pdf sample.pdf --question "test query"
```

### Baseline evaluation

```bash
python scripts/evaluation/run_baseline_evaluation.py
```

### Model optimization

```bash
python scripts/optimization/run_model_optimization.py --quick-test
```

### Production validation

```bash
python scripts/deployment/production_validation.py --health-check --verbose
```

## Project Structure

```text
ai_rag_assistant/
├── configs/
├── data/
├── deployment/
├── docs/
├── guides/
├── infra/
├── landing/
├── llm_ollama/
├── mlruns/
├── monitoring/
├── rag_pipeline/
├── results/
├── scripts/
├── tests/
├── .github/
├── AI_RAG_PRODUCTION_CHECKLIST.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-lambda.txt
├── requirements.local.txt
├── lambda_app_handler.py
├── lambda_landing_handler.py
├── docker-start.sh
├── LICENSE
└── .gitignore
```

## Documentation References

- [AI_RAG_PRODUCTION_CHECKLIST.md](AI_RAG_PRODUCTION_CHECKLIST.md)
- [TECH_STACK_REFERENCE.md](TECH_STACK_REFERENCE.md)
- [QUEST_ANALYTICS_RAG_IMPLEMENTATION_GUIDE.md](QUEST_ANALYTICS_RAG_IMPLEMENTATION_GUIDE.md)
- [docs/PROBLEM_STATEMENT.md](docs/PROBLEM_STATEMENT.md)
- [docs/LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md)
- [guides/MODEL_OPTIMIZATION_GUIDE.md](guides/MODEL_OPTIMIZATION_GUIDE.md)
- [guides/SECURITY_GUIDE.md](guides/SECURITY_GUIDE.md)

## Final Note

This project is best understood as a practical, cost-aware research assistant that balances retrieval quality, operational simplicity, and deployment realism. It is intended to be usable, extensible, and transparent about what it does well and where future improvements are still needed.
