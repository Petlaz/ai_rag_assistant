# Tech Stack Documentation - Quest Analytics RAG Assistant

## Overview
This document provides a comprehensive reference of all technologies, frameworks, and tools used in the Quest Analytics RAG Assistant project.

## Programming Languages

### Primary Language
- **Python 3.11+**
  - Core application development
  - AI/ML pipeline implementation
  - Web services and APIs
  - Data processing and analysis

## AI/ML & NLP Technologies

### Language Models
- **Ollama** (Latest)
  - Local LLM deployment and management
  - Model serving with health monitoring
  - Support for multiple models (Gemma3:1b, Phi3:mini)
  - Automatic fallback mechanisms

### ML Frameworks & Libraries
- **LangChain 1.2.0**
  - RAG pipeline orchestration
  - Document processing workflows
  - LLM integration and chaining
- **LangChain Community 0.4.1**
  - Extended integrations and tools
- **LangChain Core 1.2.5**
  - Core abstractions and utilities
- **Sentence Transformers 2.2.0**
  - Vector embeddings generation
  - Semantic similarity computation
- **Transformers 4.35.0**
  - Hugging Face model integration
  - Pre-trained model loading and inference

### Numerical Computing
- **NumPy 1.24.0**
  - Numerical operations and array processing
- **Pandas 2.0.0**
  - Data manipulation and analysis

## Search & Database Technologies

### Search Engine
- **OpenSearch 2.18.0**
  - Hybrid search implementation (BM25 + vector)
  - Document indexing and retrieval
  - Cluster management and health monitoring
- **OpenSearch Python Client 2.4.0**
  - Python integration with OpenSearch
  - Query construction and execution

### Vector Storage Options
- **OpenSearch** (Primary for full deployment)
  - Distributed vector storage
  - Hybrid search capabilities
- **SQLite** (Ultra-budget deployment)
  - Local vector storage
  - Cost-optimized implementation

## Web Technologies

### Backend Framework
- **FastAPI 0.104.0**
  - RESTful API development
  - Async request handling
  - Professional landing page
  - Auto-generated API documentation

### Web Server
- **Uvicorn 0.24.0**
  - ASGI server for FastAPI
  - High-performance async handling

### User Interface
- **Gradio 6.2.0**
  - Interactive web interface
  - Real-time chat functionality
  - Custom CSS styling
  - Health monitoring dashboard

### Template Engine
- **Jinja2 3.1.0**
  - HTML template rendering
  - Dynamic content generation

## Document Processing

### PDF Processing
- **PyPDF 3.17.0**
  - PDF text extraction
  - Document metadata parsing
- **Pytesseract 0.3.10**
  - Optical Character Recognition (OCR)
  - Scanned document processing
- **Pillow 10.0.0**
  - Image processing for OCR pipeline
- **Python-magic 0.4.27**
  - File type detection and validation

## Data Validation & Configuration

### Configuration Management
- **Pydantic 2.5.0**
  - Data validation and type checking
  - Configuration model definitions
- **PyYAML 6.0.1**
  - YAML configuration file parsing
- **Python-dotenv 1.0.0**
  - Environment variable management
  - Secrets handling

## HTTP & Networking

### HTTP Libraries
- **Requests 2.31.0**
  - Synchronous HTTP client
  - External API integration
- **HTTPX 0.25.0**
  - Async HTTP client
  - Modern HTTP/2 support

## Cloud & Infrastructure

### Cloud Platform
- **Amazon Web Services (AWS)**
  - Primary cloud deployment platform
  - Multiple deployment tiers (Ultra-Budget, Balanced, Full)

### AWS Services Used
- **AWS Lambda**
  - Serverless compute for ultra-budget deployment
  - Function URLs for API endpoints
- **Amazon S3**
  - Document storage
  - Static asset hosting
- **AWS CloudWatch**
  - Monitoring and logging
  - Cost tracking and alerts
- **AWS IAM**
  - Access control and security

### Infrastructure as Code
- **Terraform** (Planned)
  - Infrastructure provisioning
  - Resource management
  - Environment consistency

## Containerization & Orchestration

### Containerization
- **Docker**
  - Application containerization
  - Multi-service deployment
  - Development environment consistency
- **Docker Compose**
  - Multi-container orchestration
  - Development stack management

### Container Orchestration
- **Kubernetes**
  - Production container orchestration
  - Scalable deployment management
  - Service discovery and load balancing

## Development Tools

### Package Management
- **Poetry** (Configuration present)
  - Python dependency management
  - Virtual environment handling
- **pip**
  - Python package installation
  - Requirements management

### Code Quality
- **Black 23.9.0**
  - Python code formatting
  - Consistent code style
- **Flake8 6.0.0**
  - Code linting
  - Style guide enforcement

### Testing
- **pytest 7.4.0**
  - Unit testing framework
  - Test automation
- **pytest-asyncio 0.21.0**
  - Async testing support

### Utilities
- **Click 8.1.0**
  - Command-line interface creation
- **tqdm 4.66.0**
  - Progress bars for long-running operations

## Development Environment

### Base Environment
- **Python 3.11-slim Docker Image**
  - Lightweight Python runtime
  - Optimized for production deployment

### System Dependencies
- **build-essential**
  - Compilation tools for native extensions
- **git**
  - Version control
- **curl**
  - HTTP client for health checks

## Monitoring & Observability

### Health Monitoring
- **Custom Health Check System**
  - Component health monitoring
  - Latency tracking
  - Automatic failover mechanisms

### Analytics
- **Built-in Analytics System**
  - Usage tracking
  - Performance metrics
  - User interaction monitoring

## Deployment Architectures

### Ultra-Budget Deployment ($8-18/month)
- SQLite vector storage
- AWS Lambda Function URLs
- Aggressive caching (24-hour TTL)
- Document cleanup (7-day expiration)
- Cost monitoring and alerts

### Balanced Deployment ($15-35/month)
- Managed OpenSearch cluster
- Enhanced monitoring
- Moderate resource allocation

### Full Production Deployment ($25-68/month)
- Full OpenSearch cluster
- Complete monitoring suite
- High availability configuration
- Advanced security features

## Security Features

### Input Validation
- Pydantic model validation
- File type verification
- Content filtering

### Safety Measures
- Research-focused guardrails
- Content safety checks
- Rate limiting capabilities

## Integration Capabilities

### LLM Providers
- Local Ollama deployment
- Model fallback system
- Health monitoring integration

### External Services
- RESTful API endpoints
- Webhook support
- Real-time status updates

## Performance Optimizations

### Caching
- Response caching
- Vector embedding caching
- Session-based optimizations

### Resource Management
- Memory-efficient processing
- Streaming response handling
- Connection pooling

---

## Version Compatibility

This tech stack is designed for:
- Python 3.11+
- Modern web browsers
- Linux/Unix environments
- Container-based deployments

## Future Technology Considerations

### Planned Additions
- Redis caching layer
- Advanced reranking algorithms
- Multi-modal document processing
- Real-time collaboration features

### Potential GPU Acceleration
- PyTorch 2.1.0+ (Optional)
- CUDA support for enhanced performance
- GPU-accelerated vector operations

---

*Last Updated: March 2026*
*Project: Quest Analytics RAG Assistant*