# Tech Stack Documentation - Quest Analytics RAG Assistant

## Overview
This document provides a comprehensive reference of all technologies, frameworks, and tools used in the Quest Analytics RAG Assistant project. Updated to reflect the current clean project architecture and deployment modes.

## Programming Languages

### Primary Language
- **Python 3.11+**
  - Core application development
  - AI/ML pipeline implementation
  - Web services and APIs
  - Data processing and analysis

## AI/ML & NLP Technologies

### Language Models & AI Services
- **Ollama** (Latest)
  - Local LLM deployment and management
  - Model serving with health monitoring
  - Support for multiple models (Mistral, Gemma3:1b, Phi3:mini)
  - Automatic fallback mechanisms
- **Amazon Bedrock Claude Haiku**
  - Cloud-based LLM inference for production
  - Cost-effective text generation
  - Integrated with AWS ultra-budget deployment

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
  - Function URLs for direct API endpoints (no API Gateway costs)
  - Automatic scaling and pay-per-request pricing
- **Amazon S3**
  - Document storage with lifecycle policies
  - Static asset hosting
  - Automatic cleanup after 7 days (ultra-budget mode)
- **Amazon DynamoDB**
  - Response caching with 24-hour TTL
  - Cost-effective NoSQL storage
  - Automatic item expiration
- **Amazon Bedrock**
  - Claude Haiku LLM inference
  - Pay-per-token pricing model
- **AWS CloudWatch**
  - Monitoring and logging
  - Cost tracking and alerts
- **AWS IAM**
  - Access control and security
  - Least-privilege permissions

### Infrastructure as Code
- **AWS CloudFormation** (via deployment scripts)
  - Infrastructure provisioning
  - Resource management
  - Environment consistency

## Containerization & Development

### Containerization
- **Docker**
  - Application containerization
  - Multi-service development environment
  - Consistent deployment across platforms
- **Docker Compose**
  - Multi-container orchestration
  - Development stack management
  - Service dependency management

## Development Tools

### Package Management
- **pip** (Primary)
  - Python package installation
  - Requirements management via requirements.txt
- **pyproject.toml** (Configuration)
  - Project metadata and configuration
  - Build system requirements

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
**Technologies Used:**
- SQLite vector storage (embedded in Lambda)
- AWS Lambda with Function URLs
- Amazon S3 with lifecycle policies
- DynamoDB caching with 24-hour TTL
- Bedrock Claude Haiku for LLM inference
- Aggressive caching and cleanup automation

### Balanced Deployment ($15-35/month)
**Technologies Used:**
- External vector database (Pinecone or Chroma)
- AWS API Gateway + Lambda
- Enhanced monitoring and analytics
- Smart caching strategies

### Full Production Deployment ($25-68/month)
**Technologies Used:**
- Amazon OpenSearch Serverless
- AWS CloudFront CDN
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

## Performance Metrics

### Current Baseline Performance
- **Precision@5**: 0.72 (Retrieval accuracy)
- **MRR (Mean Reciprocal Rank)**: 0.80 (Ranking quality)  
- **Query Response Time**: < 2 seconds (95th percentile)
- **Ollama Health Check**: < 1 second response time

### Target Performance Goals
- **Precision@5**: > 0.85 (Pre-deployment target)
- **MRR**: > 0.90 (Ranking optimization goal)
- **Query Response Time**: < 1.5 seconds (Performance objective)
- **Cost per Query**: < $0.01 (Ultra-budget mode target)

---

## Version Compatibility

This tech stack is designed for:
- Python 3.11+
- Modern web browsers (Chrome, Firefox, Safari, Edge)
- Linux/Unix environments (macOS, Ubuntu, CentOS)
- Container-based deployments (Docker, AWS Lambda)
- AWS cloud infrastructure

---

*Last Updated: January 2025*
*Project: Quest Analytics RAG Assistant*