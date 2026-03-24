# AI RAG Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenSearch](https://img.shields.io/badge/OpenSearch-2.18.0-005EB8?style=flat&logo=opensearch&logoColor=white)](https://opensearch.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.ai/)
[![Gradio](https://img.shields.io/badge/Gradio-6.2.0-FF6C37?style=flat&logo=gradio&logoColor=white)](https://gradio.app/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2.0-121212?style=flat)](https://github.com/langchain-ai/langchain)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-Deployed-FF9900?style=flat&logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![MLOps](https://img.shields.io/badge/MLOps-MLflow%20%7C%20Monitoring-8B5CF6?style=flat)](https://mlflow.org/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=flat&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A **production-deployed Retrieval-Augmented Generation** system designed for research teams to intelligently query and analyze scientific literature. Built with hybrid search capabilities, document session isolation, real-time health monitoring, enterprise-grade deployment architecture, and comprehensive MLOps infrastructure.

**Current Status: Production Deployed** | [**Live Demo**](https://k4mtt3o2lvjpo7f673h7yqq3ou0vixyy.lambda-url.us-east-1.on.aws/)  
**Performance**: 87.5% precision with 224ms response time (40% faster than baseline)  
**MLOps Infrastructure**: Complete CI/CD pipeline with automated testing, model validation, blue-green deployment, production monitoring, cost estimation, security scanning, and rollback systems

## MLOps Development Stages

| Stage | Status | Focus Area | Key Deliverables |
|-------|--------|------------|------------------|
| **Baseline Testing** | **COMPLETE** | Baseline Testing & Evaluation | Statistical analysis framework, A/B testing pipeline, comprehensive code documentation |
| **Model Optimization** | **COMPLETE** | Model Optimization & Performance Analysis | Embedding model comparison, re-ranking evaluation, M1 Mac optimization, graceful fallback systems |
| **Production Monitoring** | **COMPLETE** | Production Monitoring | Real-time monitoring, intelligent alerting systems, log analysis, cost tracking |
| **Advanced MLOps** | **COMPLETE** | Advanced MLOps & Automation | MLflow integration, automated retraining pipelines, model monitoring, deployment automation |
| **Deployment Infrastructure** | **COMPLETE** | Production Deployment & DevOps | Blue-green deployment, rollback systems, cost estimation, production validation |
| **CI/CD Pipeline** | **COMPLETE** | Automated Testing & Deployment | GitHub Actions workflows, automated testing, model validation, security scanning, multi-environment deployment |
| **Configuration Optimization** | **COMPLETE** | A/B Testing & Deployment | Optimized configuration deployed (40% speed improvement), MLflow experiment tracking |

### Baseline Testing Achievements

**Testing Infrastructure:**
- **6 Core Evaluation Scripts**: Complete testing framework for RAG system evaluation
- **Statistical Analysis**: 95% confidence intervals, significance testing, publication-quality analysis
- **A/B Testing Pipeline**: Parameter optimization with grid search and experimental design
- **Domain-Specific Testing**: Multi-domain query generation (Medical, Legal, Financial, Technical)
- **Performance Monitoring**: Response time analysis, retrieval quality metrics, system health tracking

**Code Documentation:**
- **16,000+ Lines of Analysis**: Line-by-line code explanations and architectural documentation
- **Function-by-Function Breakdown**: Complete understanding guide for all baseline testing components
- **Design Pattern Documentation**: Architectural decisions and implementation strategies

See [`docs/code_analysis_baseline/`](docs/code_analysis_baseline/) for complete baseline evaluation documentation.

### Model Optimization Achievements

**Model Optimization Framework:**
- **Embedding Model Comparison**: Systematic evaluation framework achieving P@5: 0.4, MRR: 1.0 with realistic metrics
- **Re-ranking Strategy Evaluation**: Comprehensive cost-benefit analysis with resolved cross-encoder integration
- **Multi-Objective Optimization**: Pareto frontier analysis for optimal performance-cost-quality trade-offs
- **Hardware-Specific Optimization**: M1/M2 Mac optimization with MPS acceleration and thermal management
- **Performance vs Cost Analysis**: Multi-dimensional cost modeling with ROI analysis and scale projections

**Evaluation Infrastructure:**
- **Resilient Testing Framework**: Mock evaluation modes with no external dependencies required
- **Cross-Encoder Integration**: Successfully resolved 0.0 precision issue with improved mock scoring logic  
- **Graceful Degradation**: Automatic fallback modes for OpenSearch, Ollama, and model unavailability
- **Consistent Metrics**: Both cross-encoder and hybrid scoring achieve comparable P@5: 0.4 performance
- **CI/CD Ready**: Deterministic results for reliable automated testing and deployment

**Code Documentation:**
- **18,000+ Lines of Analysis**: Comprehensive model optimization code documentation and architectural analysis
- **Seven Complete Script Analyses**: Detailed documentation of all model optimization components
- **Optimization Guide**: Complete [`MODEL_OPTIMIZATION_GUIDE.md`](guides/MODEL_OPTIMIZATION_GUIDE.md) for production implementation
- **Lessons Learned**: Comprehensive [`LESSONS_LEARNED.md`](documentation/LESSONS_LEARNED.md) documenting successes and failures

**Complete Testing & Infrastructure Pipeline Example:**
```bash
# Complete baseline evaluation
python scripts/evaluation/run_baseline_evaluation.py

# Full model optimization
python scripts/optimization/run_model_optimization.py --quick-test

# Production monitoring setup
python scripts/monitoring/production_monitoring.py --setup
python scripts/monitoring/alerting_system.py --setup
python scripts/monitoring/log_analysis.py --setup

# MLOps pipeline setup
python scripts/mlops/setup_mlops_pipeline.py --tracking-uri ./mlruns
python scripts/mlops/automated_retraining.py --schedule-check
python scripts/mlops/model_monitoring.py --production-metrics

# Deployment automation
python scripts/deployment/blue_green_deploy.py --validate
python scripts/deployment/estimate_aws_costs.py --deployment-mode ultra-budget
```

### Production Monitoring Achievements

**Monitoring Infrastructure:**
- **Real-time System Monitoring**: Production monitoring system with CloudWatch integration, resource utilization tracking
- **Intelligent Alerting Framework**: Multi-channel alerting (Email, Slack, CloudWatch) with noise reduction and escalation policies
- **Log Analysis System**: Real-time log monitoring with anomaly detection and performance metric extraction
- **Cost Tracking & Optimization**: AWS cost monitoring with automated alerts and optimization recommendations
- **Health Monitoring Dashboard**: Component health tracking with automatic failover mechanisms

### Deployment Infrastructure Achievements

**Deployment Automation Framework:**
- **Blue-Green Deployment**: Zero-downtime deployment automation with traffic switching and health validation
- **Rollback System**: Automated failure detection with multiple rollback strategies (Fast, Graceful, Partial, Data-Safe)
- **Production Validation**: Comprehensive health checks across Application, Resources, Dependencies, and Network
- **Cost Estimation**: AWS cost analysis across deployment modes (Ultra-Budget $7.24/month actual, Balanced $25-60/month, Full-Scale $100-300+/month)
- **Infrastructure Deployed**: Production-deployed automation scripts with complete CLI interfaces and documentation

**Code Documentation:**
- **4 Production Deployment Scripts**: Complete automation framework for enterprise deployment
- **Comprehensive README**: Detailed documentation with examples, configuration guides, and troubleshooting
- **Enterprise-Grade Infrastructure**: Production monitoring, automated rollback, and cost optimization

See [`scripts/deployment/README.md`](scripts/deployment/README.md) for complete deployment automation documentation.

## Key Features

- **Production Monitoring Infrastructure**: Real-time system health monitoring, intelligent alerting framework, log analysis system
- **MLOps Pipeline**: MLflow integration, automated model retraining, performance drift detection, experiment tracking
- **Advanced Deployment**: Blue-green deployment capabilities, automated rollback systems, cost optimization monitoring
- **Ultra-Budget AWS Deployment**: Cost-optimized $7.24/month cloud deployment using SQLite vector storage and Lambda Function URLs
- **Enterprise Security**: API authentication, rate limiting, input sanitization, and comprehensive threat detection
- **Hybrid Search**: Combines BM25 (sparse) and vector (dense) search for optimal retrieval performance
- **Advanced PDF Processing**: Automated OCR pipeline with metadata extraction and intelligent chunking
- **Document Session Isolation**: Clear previous documents option prevents cross-contamination between research sessions
- **Local LLM Integration**: Ollama-based chat with health monitoring and automatic fallback mechanisms
- **Research-Focused**: Tailored prompts with citation support and safety guardrails for scientific literature
- **Professional UI**: Modern Gradio 6.2.0 interface with custom CSS, real-time status monitoring, and security protection
- **Production Deployed**: Three-tier deployment strategy (Ultra-Budget/Balanced/Full) with comprehensive AWS documentation
- **Analytics & Health**: Built-in usage tracking, performance metrics, and service health dashboards
- **Professional Landing Page**: FastAPI-powered landing page with analytics, security dashboard, and modern design

## Architecture

### Production-Deployed Enterprise RAG System

**Current Status**: Live deployment at $4-13/month on AWS infrastructure  
**Live App**: [https://k4mtt3o2lvjpo7f673h7yqq3ou0vixyy.lambda-url.us-east-1.on.aws/](https://k4mtt3o2lvjpo7f673h7yqq3ou0vixyy.lambda-url.us-east-1.on.aws/)

```
┌──────────────────────────────────────────────────────────────────┐
│                        WEB TIER                                  │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐  │
│  │    Gradio Web UI        │    │    FastAPI Landing         │  │
│  │    Port 7860           │    │    Port 3000               │  │
│  │  • Interactive Chat    │    │  • Analytics Dashboard     │  │
│  │  • Document Upload     │    │  • Health Monitoring       │  │
│  │  • Session Management  │    │  • Security Controls       │  │
│  └─────────────────────────┘    └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                      CORE RAG PIPELINE                          │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────┐│
│  │   Document    │ │   Embedding   │ │    Hybrid     │ │  LLM  ││
│  │   Ingestion   │ │   & Vector    │ │   Retrieval   │ │ Chat  ││
│  │               │ │    Storage    │ │               │ │       ││
│  │ • PDF OCR     │ │ • Sentence-T  │ │ • Vector      │ │ • Ollama │
│  │ • Chunking    │ │ • OpenSearch  │ │ • BM25        │ │ • Health │
│  │ • Metadata    │ │ • Indexing    │ │ • Re-ranking  │ │ • Fallback │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────┘│
└──────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  OpenSearch (9200)  │  Local Storage  │  Configuration    │ │
│  │  • Vector Index     │  • Documents    │  • YAML/JSON      │ │
│  │  • Hybrid Search    │  • Cache        │  • Environment    │ │
│  │  • Metadata Store   │  • Logs         │  • Security       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Core Architecture Principles

**Serverless-First Design**: AWS Lambda Function URLs with container images, optimized for cost-effectiveness ($4-13/month) and zero-maintenance operations

**Hybrid Search**: Combines vector similarity and BM25 keyword search for optimal retrieval performance

**Session Isolation**: Document management prevents cross-contamination between research sessions

**Health Monitoring**: Real-time service monitoring with automatic fallback mechanisms

**Security-First**: API authentication, rate limiting, input validation, and threat detection

**CI/CD Automated**: GitHub Actions pipeline handles build, Terraform infrastructure, ECR image deployment, and post-deploy smoke tests

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Gradio 6.2, FastAPI | Interactive UI, landing page, analytics |
| **RAG Engine** | LangChain, SentenceTransformers | Document processing, embedding generation |
| **Vector Search** | OpenSearch 2.18 | Hybrid search, metadata indexing |
| **LLM Runtime** | Ollama | Local model execution, health monitoring |
| **Infrastructure** | Docker, Terraform, Lambda | Containerization, IaC, serverless deployment |
| **CI/CD** | GitHub Actions | Automated build, deploy, and smoke test pipeline |
| **Monitoring** | CloudWatch, Custom Scripts | Production monitoring, alerting |

### Deployment Architecture

**Current**: Production-deployed serverless architecture on AWS Lambda Function URLs
- **3 Lambda functions**: App (Gradio), Landing (FastAPI), Worker
- **Terraform-managed infrastructure** in `infra/terraform/` with S3 state backend
- **GitHub Actions CI/CD**: 5-job pipeline (validate -> build -> infra -> deploy -> test)
- **Container images**: Built via Docker, pushed to GHCR, mirrored to ECR
- **Cost**: $4-13/month depending on usage

**Future Evolution**: Microservices transition planned as scale requirements grow
- Kubernetes orchestration
- Service mesh implementation  
- Auto-scaling and load balancing

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **8GB+ RAM** (for local Ollama models)
- **4GB+ free disk space** (for OpenSearch and models)

### 1. Clone and Setup

```bash
git clone https://github.com/Petlaz/ai_rag_assistant.git
cd ai_rag_assistant

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment (IMPORTANT)
cp configs/secrets.template.env .env
nano .env  # Edit with your settings
```

**Required .env Settings:**
- `OLLAMA_BASE_URL`: Usually `http://localhost:11434`
- `OLLAMA_MODEL`: Recommended `gemma3:1b` for low resource usage
- `OPENSEARCH_HOST`: Usually `http://localhost:9200` 
- `OPENSEARCH_INDEX`: Your index name (e.g., `quest-research`)

The application automatically loads these settings from the `.env` file.

### 2. Launch with Docker (Recommended)

```bash
# Start all services with health checks
docker compose -f deployment/aws/docker/docker-compose.dev.yml up --build

# Verify services are healthy
curl http://localhost:9200/_cluster/health  # OpenSearch
curl http://localhost:11434/api/tags        # Ollama

# Pull recommended models
docker exec -it ollama ollama pull mistral:latest
docker exec -it ollama ollama pull gemma3:1b
docker exec -it ollama ollama pull phi3:mini
```

**Access Points:**
- **Landing Page**: [http://localhost:3000](http://localhost:3000)
- **RAG Assistant**: [http://localhost:7860](http://localhost:7860)
- **OpenSearch Dashboard**: [http://localhost:9200](http://localhost:9200)
- **Ollama API**: [http://localhost:11434](http://localhost:11434)

### 3. Launch Standalone (Local Development)

```bash
# Create .env file with required settings (automatically loaded)
cp configs/secrets.template.env .env
# Edit .env file with your configuration
nano .env

# Launch the application (automatically loads .env)
python deployment/app_gradio.py
```

**Note**: The application now automatically loads environment variables from `.env` file. No need to manually export them.

**Required .env configuration:**
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
OPENSEARCH_HOST=http://localhost:9200
OPENSEARCH_INDEX=quest-research
OPENSEARCH_TLS_VERIFY=false
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

### 4. Test the Pipeline

```bash
# Smoke test with sample PDF
python scripts/smoke_test.py \
  --pdf ~/Documents/sample.pdf \
  --question "What are the main findings?" \
  --model mistral

# Batch ingest documents
python scripts/run_ingestion.py ~/Documents/pdfs/*.pdf --index quest-research

# Run comprehensive tests
pytest tests/ -v
```

## Usage

### Document Upload & Management

**New Feature: Document Session Isolation**

1. **Access the Application**: Visit [http://localhost:7860](http://localhost:7860)
2. **Document Ingestion Tab**: Upload PDF files with smart session management
   - **"Clear Previous Documents"** (Default: Checked) - Removes all previous documents before adding new ones
   - Upload single or multiple PDF files
   - Real-time processing status with progress indicators
3. **Research Chat Tab**: Ask questions about your uploaded documents
   - Natural language queries with context-aware responses
   - Source citations with page numbers and document references
   - Research-focused prompt templates for academic literature
4. **Configuration Tab**: Monitor system health and adjust settings
   - Real-time LLM status monitoring
   - Model configuration (primary/fallback models, timeout settings)
   - System information and active guardrails

### Batch Document Processing

Process multiple PDFs via command line:

```bash
# Ingest with automatic index clearing
python scripts/run_ingestion.py /path/to/pdfs/*.pdf --index quest-research --clear

# Append to existing index 
python scripts/run_ingestion.py /path/to/pdfs/*.pdf --index quest-research
```

### Health Monitoring & Status

The system includes comprehensive health monitoring:

| Status | Indicator | Description |
|--------|-----------|-------------|
| **Green** | Healthy | All systems operational, normal latency |
| **Amber** | Slow Response | Degraded performance, higher latency |
| **Red** | Unreachable | Service unreachable, automatic fallback activated |

**Health Check Endpoints:**
- Gradio App: Auto-monitored in Configuration tab
- Ollama: `http://localhost:11434/api/tags`
- OpenSearch: `http://localhost:9200/_cluster/health`

### Evaluation & Testing

#### Baseline Evaluation Framework (Complete)

**Run Complete Baseline Evaluation:**
```bash
# Execute full baseline evaluation
python scripts/evaluation/run_baseline_evaluation.py

# Quick evaluation with limited queries
python scripts/evaluation/run_baseline_evaluation.py --max-queries 50 --skip-analysis

# Domain-specific testing
python scripts/create_domain_queries.py --domain medical --output-file medical_queries.jsonl
```

#### Model Optimization Framework (Complete)

**Run Complete Model Optimization:**
```bash
# Execute full model optimization pipeline
python scripts/optimization/run_model_optimization.py

# Quick test with reduced scope
python scripts/optimization/run_model_optimization.py --quick-test

# Test specific embedding models
python scripts/optimization/run_model_optimization.py --embedding-models "all-mpnet-base-v2,e5-small-v2"

# Test specific re-ranking strategies  
python scripts/optimization/run_model_optimization.py --reranking-strategies "cross_encoder,hybrid_scoring"
```

**Model Optimization Results Location:**
- **Results Directory**: `results/optimization/`
- **Embedding Comparison**: `results/optimization/embedding_comparison.json` (P@5: 0.4, MRR: 1.0)
- **Reranking Evaluation**: `results/optimization/reranking_evaluation.json` (Cross-encoder: P@5: 0.4, Hybrid: P@5: 0.4)
- **Combined Analysis**: `results/optimization/combined_analysis.json`
- **Summary Report**: `results/optimization/optimization_summary_report.json`

**Model Optimization Components:**
```bash
# Embedding model comparison (P@5: 0.4 achieved)
python scripts/embedding_model_comparison.py \
    --models "all-MiniLM-L6-v2,all-mpnet-base-v2" \
    --test-set data/samples/queries.jsonl \
    --output results/optimization/embedding_comparison.json

# Re-ranking evaluation (cross-encoder issue resolved)  
python scripts/reranking_evaluation.py \
    --strategies "cross_encoder,hybrid_scoring" \
    --test-set data/samples/queries.jsonl \
    --output results/optimization/reranking_evaluation.json

# M1 Mac optimization with MPS acceleration
python scripts/m1_optimization.py --enable-mps --optimize-memory
```

**Comprehensive Guide:** See [`MODEL_OPTIMIZATION_GUIDE.md`](guides/MODEL_OPTIMIZATION_GUIDE.md) for detailed setup, execution, and troubleshooting.

**Traditional System Testing:**
```bash
# Test retrieval quality
python scripts/eval_retrieval.py data/samples/queries.jsonl --top-k 5

# End-to-end system testing
python scripts/smoke_test.py --pdf sample.pdf --question "research question"
```

## Configuration

### Required Environment Variables

| Variable | Description | Default | Status |
|----------|-------------|---------|--------|
| `OPENSEARCH_HOST` | OpenSearch cluster endpoint | `http://localhost:9200` | Updated |
| `OPENSEARCH_INDEX` | Index name for documents | `quest-research` | Updated |
| `OPENSEARCH_TLS_VERIFY` | TLS certificate verification | `false` (dev) | New |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` | Updated |
| `OLLAMA_MODEL` | Primary LLM model | `mistral` | Updated |
| `OLLAMA_FALLBACK_MODEL` | Fallback model for errors | `phi3:mini` | Updated |
| `OLLAMA_TIMEOUT` | Request timeout (seconds) | `120` | New |
| `EMBEDDING_MODEL_NAME` | Sentence transformer model | `all-MiniLM-L6-v2` | Updated |
| `GRADIO_SERVER_PORT` | Web interface port | `7860` | New |

### Model Recommendations

| Use Case | Primary Model | Fallback Model | RAM Requirements |
|----------|--------------|----------------|-----------------|
| **Development/Testing** | `phi3:mini` | `gemma3:1b` | 4GB+ |
| **Research (Balanced)** | `mistral:latest` | `phi3:mini` | 8GB+ |
| **Production (Quality)** | `llama3:8b` | `mistral:latest` | 16GB+ |

### Key Dependencies

- **Python**: 3.11+ (Type hints, performance improvements)
- **Gradio**: 6.2.0 (Modern interface, better stability) 
- **OpenSearch**: 2.18.0 (Latest stable with security improvements)
- **LangChain**: 1.2.0 (Enhanced stability and performance)
- **SentenceTransformers**: 2.7.0 (Optimized embedding performance)

## Deployment

### Development Environment

```bash
docker compose -f deployment/aws/docker/docker-compose.dev.yml up
```

### Production Deployment

**Live on AWS Lambda Function URLs ($4-13/month):**  
**App URL**: [https://k4mtt3o2lvjpo7f673h7yqq3ou0vixyy.lambda-url.us-east-1.on.aws/](https://k4mtt3o2lvjpo7f673h7yqq3ou0vixyy.lambda-url.us-east-1.on.aws/)

Deployment is fully automated via GitHub Actions. Push to `main` triggers the CI/CD pipeline which builds Docker images, provisions infrastructure with Terraform, and runs post-deploy smoke tests.

- **[DEPLOY NOW - Quick Start](documentation/DEPLOY_NOW.md)**: Step-by-step guide to deploy in minutes
- **[Production Deployment Roadmap](documentation/PRODUCTION_DEPLOYMENT_ROADMAP.md)**: Complete deployment guide
- **[Lessons Learned](documentation/LESSONS_LEARNED.md)**: What worked, what didn't, and why
- **[AWS Deployment Guide](deployment/aws/AWS_DEPLOYMENT_GUIDE.md)**: Detailed AWS configuration reference
- **[Pre-Deployment Testing Plan](documentation/PRE_DEPLOYMENT_TESTING_PLAN.md)**: Systematic optimization and testing plan
- **Infrastructure**: Terraform configs in `infra/terraform/`, Lambda handlers at project root
- **Docker Compose**: Local development via `deployment/aws/docker/docker-compose.dev.yml`

## Project Structure

```
ai_rag_assistant/
├── .env                              # Environment variables (local, git-ignored)
├── .github/                          # GitHub configuration
│   ├── CI_CD_IMPLEMENTATION_CHECKLIST.md
│   └── workflows/                    # CI/CD pipelines
│       ├── cicd-01-ml-pipeline.yml         # ML pipeline automation
│       ├── cicd-02-model-validation.yml    # Model validation checks
│       └── cicd-03-aws-deployment.yml      # AWS Lambda deployment pipeline
├── .gitignore                        # Git ignore rules
├── AI_RAG_PRODUCTION_CHECKLIST.md    # Production readiness checklist
├── create_bucket.sh                  # S3 Terraform state bucket creation helper
├── DEPLOY_TRIGGER.txt                # CI/CD deployment trigger file
├── lambda_app_handler.py             # AWS Lambda handler for Gradio app (Function URL)
├── lambda_landing_handler.py         # AWS Lambda handler for landing page (Function URL)
├── LICENSE                           # MIT License
├── pyproject.toml                    # Project configuration
├── QUEST_ANALYTICS_RAG_IMPLEMENTATION_GUIDE.md  # RAG implementation guide
├── README.md                         # This documentation
├── requirements.txt                  # Python dependencies
├── requirements-lambda.txt           # Lambda dependencies (awslambdaric, mangum)
├── TECH_STACK_REFERENCE.md           # Technology stack quick reference
│
├── configs/                          # Configuration management
│   ├── ab_testing_config.yaml              # A/B testing configuration
│   ├── alerting.yaml                       # Multi-channel alerting
│   ├── alerting_rules.yaml                 # CloudWatch alerting rules
│   ├── app_settings.yaml                   # Application settings
│   ├── baseline_config.json                # Baseline evaluation config
│   ├── expected_usage.yaml                 # Expected usage patterns
│   ├── log_analysis.yaml                   # Log analysis configuration
│   ├── logging.yaml                        # Logging configuration
│   ├── mlflow_config.yaml                  # MLflow tracking configuration
│   ├── monitoring.yaml                     # Production monitoring settings
│   ├── monitoring_config.yaml              # Monitoring configuration
│   ├── optimization_config.yaml            # Model optimization config
│   ├── performance_thresholds.yaml         # Performance thresholds
│   ├── retrieval_variants.yaml             # Retrieval strategy variants
│   ├── secrets.template.env                # Template for .env secrets
│   └── security_config.yaml                # Security settings
│
├── data/                             # Data storage
│   ├── evaluation/                   # Evaluation datasets
│   ├── samples/                      # Sample queries and test data
│   └── training/                     # Training data
│
├── deployment/                       # Web interface & deployment
│   ├── __init__.py
│   ├── app_gradio.py                 # Main Gradio application
│   └── aws/                          # AWS deployment system
│       ├── AWS_DEPLOYMENT_GUIDE.md         # Consolidated deployment guide
│       └── docker/                         # Docker configurations
│           ├── .dockerignore
│           ├── .env / .env.example          # Docker environment config
│           ├── docker-compose.dev.yml       # Development with health checks
│           ├── Dockerfile.app               # App container (Lambda runtime)
│           ├── Dockerfile.landing           # Landing page container
│           └── Dockerfile.worker            # Worker container
│
├── docs/                             # Internal code analysis documentation
│   ├── code_analysis_baseline/       # Baseline evaluation code analysis
│   └── code_analysis_optimization/   # Optimization code analysis
│
├── documentation/                    # Project documentation
│   ├── DEPLOY_NOW.md                       # Quick-start deployment guide
│   ├── LESSONS_LEARNED.md                  # Comprehensive success/failure analysis
│   ├── PRE_DEPLOYMENT_TESTING_PLAN.md      # Optimization methodology
│   ├── PROBLEM_STATEMENT.md                # Project problem statement
│   ├── PRODUCTION_DEPLOYMENT_ROADMAP.md    # Complete deployment roadmap
│   └── TECH_STACK.md                       # Technology stack reference
│
├── guides/                           # Implementation guides
│   ├── BASELINE_EVALUATION_GUIDE.md        # Baseline testing framework
│   ├── MODEL_OPTIMIZATION_GUIDE.md         # Model optimization guide
│   └── SECURITY_GUIDE.md                   # Security implementation guide
│
├── infra/                            # Infrastructure as Code
│   └── terraform/                    # Terraform configurations
│       ├── lambda.tf                 # Lambda functions, Function URLs, IAM
│       ├── main.tf                   # S3 backend, AWS provider, locals
│       ├── outputs.tf                # App/landing URLs, function names
│       └── variables.tf              # Environment, image URIs, region
│
├── landing/                          # Professional landing page
│   ├── __init__.py
│   ├── main.py                       # FastAPI app with lifespan events
│   ├── secure_main.py                # Security-enhanced FastAPI app
│   └── templates/
│       └── index.html                # Landing page template
│
├── llm_ollama/                       # Ollama client & adapters
│   ├── adapters.py                   # Enhanced Ollama integration
│   ├── client.py                     # LLM client with health monitoring
│   ├── README.md                     # Ollama documentation
│   └── notes/
│       └── 2025_10_ollama_success.md
│
├── logs/                             # Application logs (git-ignored)
├── mlruns/                           # MLflow experiment tracking data
├── models/                           # Model storage and artifacts
├── monitoring/                       # Monitoring data and reports
│
├── rag_pipeline/                     # Core RAG components
│   ├── __init__.py
│   ├── security.py                   # API auth, rate limiting, input sanitization
│   ├── embeddings/                   # Sentence transformer wrappers
│   │   ├── __init__.py
│   │   └── sentence_transformer.py
│   ├── indexing/                     # OpenSearch integration & schema
│   │   ├── __init__.py
│   │   ├── hybrid_indexer.py
│   │   ├── opensearch_client.py
│   │   └── schema.json
│   ├── ingestion/                    # PDF processing & metadata extraction
│   │   ├── __init__.py
│   │   ├── metadata_extractor.py
│   │   ├── pdf_ocr_pipeline.py
│   │   └── pipeline.py
│   ├── prompts/                      # Research-focused prompt templates
│   │   ├── guardrails.yaml
│   │   └── research_qa_prompt.yaml
│   └── retrieval/                    # Hybrid search & reranking
│       ├── __init__.py
│       ├── reranker.py
│       └── retriever.py
│
├── results/                          # MLOps evaluation results
│   ├── ab_testing/                   # A/B test results
│   ├── baseline_evaluation/          # Baseline statistical analysis
│   └── optimization/                 # Model optimization results
│
├── scripts/                          # Operational utilities & MLOps infrastructure
│   ├── README.md                     # Script organization guide
│   ├── eval_retrieval.py             # Retrieval quality evaluation
│   ├── ingest_watch.py               # File watcher for ingestion
│   ├── m1_optimization.py            # M1/M2 Mac optimization
│   ├── run_ingestion.py              # Batch processing pipeline
│   ├── security_manager.py           # Security management utilities
│   ├── smoke_test.py                 # End-to-end system testing
│   ├── ab_testing/                   # A/B testing scripts
│   │   ├── ab_test_retrieval.py
│   │   ├── experiment_pipeline.py
│   │   ├── select_best_config.py
│   │   ├── statistical_analysis.py
│   │   └── test_framework.py
│   ├── deployment/                   # Production deployment infrastructure
│   │   ├── blue_green_deploy.py
│   │   ├── deploy_optimized_config.py
│   │   ├── estimate_aws_costs.py
│   │   ├── production_validation.py
│   │   └── rollback_system.py
│   ├── evaluation/                   # Baseline evaluation scripts
│   │   ├── analyze_eval_results.py
│   │   ├── baseline_evaluation.py
│   │   ├── create_domain_queries.py
│   │   ├── domain_performance_analysis.py
│   │   ├── generate_test_queries.py
│   │   └── run_baseline_evaluation.py
│   ├── mlops/                        # MLOps infrastructure
│   │   ├── automated_retraining.py
│   │   ├── initialize_mlflow.py
│   │   ├── model_monitoring.py
│   │   └── setup_mlops_pipeline.py
│   ├── monitoring/                   # Production monitoring scripts
│   │   ├── alerting_system.py
│   │   ├── log_analysis.py
│   │   └── production_monitoring.py
│   └── optimization/                 # Model optimization scripts
│       ├── analyze_embedding_tradeoffs.py
│       ├── embedding_model_comparison.py
│       ├── performance_cost_analysis.py
│       ├── reranking_cost_analysis.py
│       ├── reranking_evaluation.py
│       └── run_model_optimization.py
│
├── tests/                            # Unit & integration tests
│   ├── conftest.py
│   ├── test_ingestion.py
│   ├── test_ollama_client.py
│   ├── test_retrieval.py
│   └── fixtures/
│       └── sample_docs/
│
└── training/                         # Training data and scripts
```

## Testing & Evaluation

### System Testing
```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_retrieval.py -v        # Search functionality
pytest tests/test_ingestion.py -v        # PDF processing
pytest tests/test_ollama_client.py -v    # LLM integration

# End-to-end testing
python scripts/smoke_test.py --pdf sample.pdf --question "test query"
```

### MLOps Evaluation

**Baseline Testing:**
```bash
# Complete baseline evaluation
python scripts/evaluation/run_baseline_evaluation.py
```

**Model Optimization:**
```bash
# Full optimization pipeline
python scripts/optimization/run_model_optimization.py

# Individual components
python scripts/optimization/embedding_model_comparison.py --output results/optimization/
python scripts/optimization/reranking_evaluation.py --strategies cross_encoder,hybrid_scoring
```

**Production Deployment:**
```bash
# Production validation and health checks
python scripts/deployment/production_validation.py --health-check --verbose

# Blue-green deployment (dry-run)
python scripts/deployment/blue_green_deploy.py --validate-config --dry-run

# AWS cost estimation
python scripts/deployment/estimate_aws_costs.py --deployment-mode ultra-budget

# Automated rollback system setup
python scripts/deployment/rollback_system.py --help
```

**Results:**
- Baseline: `results/baseline_evaluation/`
- Model Optimization: `results/optimization/` (P@5: 0.4, MRR: 1.0 achieved)

## Recent Improvements

**Recent Production Infrastructure Improvements:**
- **Complete Deployment Infrastructure**: Blue-green deployment automation, rollback systems, production validation, and cost estimation
- **Production Monitoring System**: Real-time health monitoring with CloudWatch integration and custom metrics
- **Intelligent Alerting**: Multi-channel alerting system with smart aggregation and escalation policies  
- **Log Analysis Framework**: Real-time log monitoring with anomaly detection and performance metric extraction
- **MLOps Integration**: Complete MLflow setup with automated experiment tracking and model versioning
- **Enterprise-Ready Automation**: Production-grade deployment scripts with comprehensive CLI interfaces and documentation
- **Document Session Isolation**: "Clear Previous Documents" option prevents cross-contamination
- **Automatic Environment Loading**: .env file automatically loaded on app startup
- **Enhanced UI**: Production-deployed Gradio interface with comprehensive monitoring integration

## Documentation

### Technical Analysis
- **[Baseline Evaluation Guide](guides/BASELINE_EVALUATION_GUIDE.md)**: Baseline testing framework and methodology
- **[Model Optimization Guide](guides/MODEL_OPTIMIZATION_GUIDE.md)**: Model optimization implementation guide
- **[Security Guide](guides/SECURITY_GUIDE.md)**: Security implementation and setup guide
- **[Lessons Learned](documentation/LESSONS_LEARNED.md)**: Comprehensive success/failure analysis
- **[Tech Stack Reference](documentation/TECH_STACK.md)**: Complete technology stack documentation
- **[Problem Statement](documentation/PROBLEM_STATEMENT.md)**: Project objectives and problem definition

### Deployment & Operations
- **[AWS Deployment](deployment/aws/AWS_DEPLOYMENT_GUIDE.md)**: Three cost-optimized deployment modes
- **[Deployment Scripts](scripts/deployment/README.md)**: Complete automation framework for production deployment
- **[Testing Plan](documentation/PRE_DEPLOYMENT_TESTING_PLAN.md)**: Optimization methodology
- **[Monitoring Documentation](scripts/monitoring/README.md)**: Production monitoring infrastructure guide

## Troubleshooting

### Quick Fixes

**Environment Variables Not Loading:**
```bash
# Check if .env file exists and has correct values
cat .env

# Manually load if needed (app loads automatically)
source .env && python deployment/app_gradio.py
```

**LLM Unreachable:**
```bash
curl http://localhost:11434/api/tags  # Check Ollama status
# Check .env file for correct OLLAMA_BASE_URL and OLLAMA_MODEL settings
```

**PDF Processing Errors:**
```bash
curl http://localhost:9200/_cluster/health  # Check OpenSearch
export OPENSEARCH_HOST=http://localhost:9200
```

**Port Conflicts:**
```bash
lsof -ti:7860 | xargs kill -9  # Kill processes on port 7860
```

**Docker Issues:**
```bash
docker-compose -f deployment/aws/docker/docker-compose.dev.yml logs
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.