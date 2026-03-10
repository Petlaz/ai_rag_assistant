# Quest Analytics RAG Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenSearch](https://img.shields.io/badge/OpenSearch-2.18.0-005EB8?style=flat&logo=opensearch&logoColor=white)](https://opensearch.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-000000?style=flat&logo=ollama&logoColor=white)](https://ollama.ai/)
[![Gradio](https://img.shields.io/badge/Gradio-6.2.0-FF6C37?style=flat&logo=gradio&logoColor=white)](https://gradio.app/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2.0-121212?style=flat)](https://github.com/langchain-ai/langchain)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready **Retrieval-Augmented Generation** system designed for research teams to intelligently query and analyze scientific literature. Built with hybrid search capabilities, document session isolation, real-time health monitoring, and enterprise-grade deployment architecture.

## Key Features

- **Ultra-Budget AWS Deployment**: Revolutionary $8-18/month cloud deployment using SQLite vector storage and Lambda Function URLs
- **Hybrid Search**: Combines BM25 (sparse) and vector (dense) search for optimal retrieval performance
- **Advanced PDF Processing**: Automated OCR pipeline with metadata extraction and intelligent chunking
- **Document Session Isolation**: Clear previous documents option prevents cross-contamination between research sessions
- **Local LLM Integration**: Ollama-based chat with health monitoring and automatic fallback mechanisms
- **Research-Focused**: Tailored prompts with citation support and safety guardrails for scientific literature
- **Professional UI**: Modern Gradio 6.2.0 interface with custom CSS and real-time status monitoring
- **Production Ready**: Three-tier deployment strategy (Ultra-Budget/Balanced/Full) with comprehensive AWS documentation
- **Analytics & Health**: Built-in usage tracking, performance metrics, and service health dashboards
- **Professional Landing Page**: FastAPI-powered landing page with analytics and modern design

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gradio UI     │    │  RAG Pipeline   │    │     Ollama      │
│  (Port 7860)    │───▶│                 │───▶│   LLM Server    │
│ • Custom CSS    │    │ • Ingestion     │    │  (Port 11434)   │
│ • Health Monitor│    │ • Indexing      │    │ • Health Checks │
│ • Doc Sessions  │    │ • Retrieval     │    │ • Model Fallback│
└─────────────────┘    │ • Embeddings    │    └─────────────────┘
                       │ • Session Mgmt  │    
┌─────────────────┐    │ • Clear Index   │    ┌─────────────────┐
│ Landing Page    │    └─────────────────┘    │   OpenSearch    │
│  (Port 3000)    │             │             │  (Port 9200)    │
│ • Analytics     │             └────────────▶│ • Hybrid Search │
│ • Health Status │                           │ • Index Mgmt    │
└─────────────────┘                           └─────────────────┘
```

### Core Components

| Component | Description | Recent Updates |
|-----------|-------------|----------------|
| **`rag_pipeline/`** | Core RAG functionality: ingestion, indexing, retrieval, embeddings | Document isolation, index clearing, enhanced retrieval |
| **`deployment/`** | Gradio web interface and AWS deployment configurations | Professional UI, health monitoring, three-tier strategy |
| **`llm_ollama/`** | Ollama client integration with health monitoring and documentation | Enhanced health checks, integrated notes/ |
| **`landing/`** | FastAPI landing page with analytics and modern design | Updated titles, fixed analytics, modern lifespan events |
| **`scripts/`** | Deployment automation and utility scripts | Ultra-budget deployment script with mode selection |
| **`tests/`** | Comprehensive test suite with fixtures | Enhanced test coverage for new features |

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

# Configure environment
# Create .env file with your settings
nano .env
```

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
# Set required environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=mistral
export OPENSEARCH_HOST=http://localhost:9200
export OPENSEARCH_INDEX=quest-research
export OPENSEARCH_TLS_VERIFY=false

# Launch the application
python deployment/app_gradio.py
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

Assess system performance with comprehensive evaluation:

```bash
# Test retrieval quality with sample queries
python scripts/eval_retrieval.py data/samples/queries.jsonl --top-k 5

# End-to-end system testing
python scripts/smoke_test.py --pdf sample.pdf --question "research question"

# Component-specific tests
pytest tests/test_retrieval.py -v      # Search functionality
pytest tests/test_ingestion.py -v     # PDF processing
pytest tests/test_ollama_client.py -v # LLM integration
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

Optimized model selection based on use case:

| Use Case | Primary Model | Fallback Model | RAM Requirements |
|----------|--------------|----------------|------------------|
| **Development/Testing** | `phi3:mini` | `gemma3:1b` | 4GB+ |
| **Research (Balanced)** | `mistral:latest` | `phi3:mini` | 8GB+ |
| **Production (Quality)** | `llama3:8b` | `mistral:latest` | 16GB+ |
| **Enterprise (Max Quality)** | `llama3:70b` | `llama3:8b` | 64GB+ GPU |

### Dependencies Update

**Recently Updated:**
- **Gradio**: `6.2.0` (from `4.44.x`) - Fixed schema compatibility issues
- **LangChain**: `1.2.0` ecosystem - Enhanced stability and performance  
- **OpenSearch**: `2.18.0` - Latest stable with improved security
- **SentenceTransformers**: `2.7.0` - Better embedding performance

## Deployment

### Development Environment

```bash
docker compose -f deployment/aws/docker/docker-compose.dev.yml up
```

### Production Deployment

See deployment guides for AWS:
- **[Quick Deploy](deployment/README.md)**: Student-friendly one-click deployment
- **[Complete Strategy](deployment/aws/AWS_DEPLOYMENT_ROADMAP.md)**: Comprehensive roadmap with cost optimization
- **Docker Compose**: Local development configurations
- **CloudWatch** monitoring and cost control

## Project Structure

```
ai_rag_assistant/
├── rag_pipeline/              # Core RAG components
│   ├── ingestion/            # PDF processing & metadata extraction
│   │   ├── __init__.py
│   │   ├── pdf_ocr_pipeline.py      # Enhanced PDF processing
│   │   ├── metadata_extractor.py    # Document metadata extraction
│   │   └── pipeline.py              # Updated with session isolation
│   ├── indexing/             # OpenSearch integration & schema
│   │   ├── __init__.py
│   │   ├── hybrid_indexer.py        # Added clear_previous support
│   │   ├── opensearch_client.py     # Index management functions
│   │   └── schema.json              # OpenSearch mapping schema
│   ├── retrieval/            # Hybrid search & reranking
│   │   ├── __init__.py
│   │   ├── retriever.py             # BM25 + vector search
│   │   └── reranker.py              # Result reranking logic
│   ├── embeddings/           # Sentence transformer wrappers
│   │   ├── __init__.py
│   │   └── sentence_transformer.py  # Embedding model interface
│   └── prompts/              # Research-focused prompt templates
│       ├── guardrails.yaml          # Safety guardrails config
│       └── research_qa_prompt.yaml  # QA prompt templates
├── deployment/               # Web interface & deployment configs
│   ├── __init__.py           # Python package initialization
│   ├── app_gradio.py         # Main Gradio app with professional UI
│   ├── README.md             # Portfolio-focused deployment guide
│   └── aws/                  # Complete AWS deployment system
│       ├── AWS_DEPLOYMENT_ROADMAP.md    # Updated strategic roadmap
│       ├── COST_OPTIMIZATION.md         # Student cost optimization guide
│       ├── ULTRA_BUDGET_IMPLEMENTATION.md # $8-18/month deployment guide
│       ├── PRE_DEPLOYMENT_CHECKLIST.md  # Pre-deployment validation
│       ├── README.md                    # AWS quick start guide
│       ├── docker/           # Docker deployment configurations
│       │   ├── .dockerignore        # Container ignore patterns
│       │   ├── .env.example         # Environment configuration template
│       │   ├── docker-compose.dev.yml # Updated with health checks
│       │   ├── Dockerfile.app       # Application container
│       │   ├── Dockerfile.worker    # Worker container
│       │   └── Dockerfile.landing   # Landing page container
│       └── docs/             # Complete AWS implementation guides
│           ├── README.md            # Three-tier deployment overview
│           ├── infrastructure-setup.md    # AWS account preparation
│           ├── services-configuration.md  # Service configs for all modes
│           └── troubleshooting.md         # Mode-specific troubleshooting
├── llm_ollama/               # Ollama client & adapters
│   ├── adapters.py           # Enhanced Ollama integration
│   ├── client.py             # LLM client with health monitoring
│   ├── README.md             # Ollama-specific documentation
│   └── notes/                # Implementation notes
│       └── 2025_10_ollama_success.md  # Implementation notes
├── landing/                  # Professional landing page
│   ├── __init__.py
│   ├── main.py               # FastAPI app with modern lifespan events
│   └── templates/            # HTML templates
│       └── index.html        # Updated professional landing page
├── scripts/                  # CLI utilities for operations
│   ├── bootstrap_opensearch.sh      # OpenSearch setup
│   ├── deploy-student-stack.sh      # Three-tier AWS deployment script
│   ├── eval_retrieval.py            # Evaluation utilities
│   ├── ingest_watch.py              # File watcher for ingestion
│   ├── run_ingestion.py             # Batch processing
│   └── smoke_test.py                # End-to-end testing
├── tests/                    # Unit & integration tests
│   ├── conftest.py           # Test configuration
│   ├── test_app_endpoints.py    # API endpoint tests
│   ├── test_ingestion.py        # PDF processing tests
│   ├── test_ollama_client.py    # LLM integration tests
│   └── test_retrieval.py        # Search functionality tests
├── data/                     # Data storage
│   └── samples/              # Sample queries and test data
│       └── queries.jsonl     # Sample evaluation queries
├── AI_ENGINEER_WORK_SAMPLE.md   # Professional work sample document
├── CV_PROJECT_ENTRY.md          # CV project entries for job applications
├── TECH_STACK_DOCUMENTATION.md  # Complete technology stack reference
├── .env                      # Environment variables (local)
├── .gitignore               # Enhanced Git ignore rules
├── LICENSE                  # MIT License
├── requirements.txt         # Updated Python dependencies
├── pyproject.toml          # Project configuration
└── README.md               # This comprehensive documentation
```

## AWS Ultra-Budget Deployment

### Three Deployment Modes for Every Budget

| Mode | Monthly Cost | Perfect For | Key Features |
|------|-------------|-------------|--------------|  
| **Ultra-Budget** | $8-18 | Students, Learning, Demos | SQLite vector storage, Function URLs, 24h caching |
| **Balanced** | $15-35 | Small Production, Portfolio | Pinecone/Chroma, API Gateway, Smart caching |
| **Full** | $25-68 | Enterprise Showcase | OpenSearch, CloudFront, Advanced monitoring |

### Quick AWS Deployment

```bash
# Deploy ultra-budget mode (perfect for students!)
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=20

# Deploy balanced mode for small production
./scripts/deploy-student-stack.sh --mode=balanced --budget=40

# Deploy full production mode
./scripts/deploy-student-stack.sh --mode=full --budget=70
```

**Complete Documentation**: See [`deployment/aws/`](deployment/aws/) for comprehensive guides, cost optimization strategies, and troubleshooting.

### Revolutionary Ultra-Budget Innovation

Our **ultra-budget mode** demonstrates cutting-edge cost optimization:

- **SQLite Vector Storage**: Eliminates external database costs ($0 vs $35/month)
- **Lambda Function URLs**: Bypasses API Gateway charges ($0 vs $10/month) 
- **Aggressive Caching**: 24-hour TTL reduces LLM costs by 80%
- **Automatic Cleanup**: 7-day document expiration controls storage costs

This showcases **real engineering innovation** - building enterprise-grade features on startup budgets!

### Recent Structural Changes

- **Created `deployment/aws/docs/`**: Comprehensive AWS implementation guides
- **Moved `AWS_DEPLOYMENT_ROADMAP.md`**: Now in `deployment/aws/` for better organization
- **Enhanced AWS documentation**: 4 focused guides for first-time cloud deployment
- **Added `scripts/deploy-student-stack.sh`**: One-click AWS deployment for students
- **Created `deployment/README.md`**: Quick AWS deployment reference
- **Consolidated documentation**: All AWS content now logically grouped
- **Student-optimized**: Focus on $15-50/month cost-effective deployments
- **Updated Dependencies**: Gradio 6.2.0, LangChain 1.2.0, OpenSearch 2.18.0
- **Added Health Monitoring**: Real-time status checks across all services
- **Document Session Management**: Clear previous documents functionality

## Testing

```bash
# Run all tests
pytest

# Test specific components  
pytest tests/test_retrieval.py -v        # Search functionality
pytest tests/test_ingestion.py -v        # PDF processing
pytest tests/test_ollama_client.py -v    # LLM integration
pytest tests/test_app_endpoints.py -v    # Web interface

# Integration testing
python scripts/smoke_test.py --pdf sample.pdf --question "test query"

# Evaluate retrieval performance
python scripts/eval_retrieval.py data/samples/queries.jsonl --top-k 5
```

## Recent Improvements & Fixes

### Document Session Isolation
- **Problem**: When uploading new PDFs, questions would return results from previously uploaded documents
- **Solution**: Added "Clear Previous Documents" option (default: enabled) that clears the index before adding new documents
- **UI**: New checkbox in Document Ingestion tab with clear status messaging

### Enhanced UI & User Experience
- **Gradio 6.2.0**: Updated from 4.44.x with modern interface and better compatibility
- **Professional Styling**: Custom CSS with gradient headers, status cards, and smooth animations
- **Real-time Health Monitoring**: Live status updates for Ollama and OpenSearch services
- **Progress Indicators**: Clear feedback during document processing

### Dependency Stability
- **LangChain 1.2.0**: Updated ecosystem for better stability and performance
- **OpenSearch 2.18.0**: Latest stable version with improved security and admin password support
- **SentenceTransformers 2.7.0**: Enhanced embedding performance and compatibility

### Infrastructure Improvements
- **Docker Health Checks**: Added health monitoring for all services in docker-compose
- **Environment Variables**: Comprehensive configuration with proper defaults
- **Service Dependencies**: Proper startup order with condition-based waiting

## Troubleshooting

### Common Issues & Solutions

**LLM Status: "Unreachable"**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Set required environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=mistral
```

**PDF Processing Errors**  
```bash
# Verify OpenSearch is running
curl http://localhost:9200/_cluster/health

# Set OpenSearch environment variables  
export OPENSEARCH_HOST=http://localhost:9200
export OPENSEARCH_TLS_VERIFY=false
```

**Port Already in Use**
```bash
# Kill existing processes
pkill -f "python.*app_gradio"
lsof -ti:7860 | xargs kill -9
```

**Docker Service Issues**
```bash  
# Check service status
docker-compose -f deployment/aws/docker/docker-compose.dev.yml ps

# View logs
docker-compose -f deployment/aws/docker/docker-compose.dev.yml logs opensearch
docker-compose -f deployment/aws/docker/docker-compose.dev.yml logs ollama
```

## Documentation

- **[AWS Quick Deploy](deployment/README.md)**: Student-friendly deployment guide
- **[AWS Deployment Roadmap](deployment/aws/AWS_DEPLOYMENT_ROADMAP.md)**: Complete strategy & cost optimization
- **[Ultra-Budget Implementation](deployment/aws/ULTRA_BUDGET_IMPLEMENTATION.md)**: $8-18/month deployment
- **[Cost Optimization](deployment/aws/COST_OPTIMIZATION.md)**: Budget-friendly strategies

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:
- **Email**: research@quest-analytics.example
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Petlaz/ai_rag_assistant/issues)