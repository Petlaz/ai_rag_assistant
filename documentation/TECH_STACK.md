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
- **NumPy 1.24.0+**
  - Numerical operations and array processing
- **Pandas 2.0.0+**
  - Data manipulation and analysis
- **SciPy**
  - Scientific computing and statistics
  - Used in evaluation and A/B testing scripts
- **Scikit-learn**
  - Machine learning algorithms for model monitoring
  - Used in MLOps pipeline components

### Machine Learning Operations (MLOps)
- **MLflow**
  - Experiment tracking and model versioning
  - Implemented in automated retraining pipeline
  - Model performance monitoring
  - Parameter and metric logging
- **Custom MLOps Pipeline**
  - Automated model retraining workflows
  - Performance drift detection
  - Model lifecycle management

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
  - Complex configuration management
- **Python-dotenv 1.0.0**
  - Environment variable management
  - Secrets handling
- **Comprehensive YAML Configuration System**
  - Monitoring configuration (`monitoring.yaml`)
  - Alerting configuration (`alerting.yaml`)
  - Log analysis configuration (`log_analysis.yaml`)
  - Application settings (`app_settings.yaml`)
  - Logging configuration (`logging.yaml`)
  - Prompt templates (`research_qa_prompt.yaml`, `guardrails.yaml`)

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
  - Custom metrics and dashboards
  - Log aggregation and analysis
- **AWS IAM**
  - Access control and security
  - Least-privilege permissions
- **AWS SES (Simple Email Service)**
  - Production email delivery
  - Alert notifications

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

### Version Control & CI/CD
- **Git**
  - Source code version control
  - Branch-based development workflow
- **GitHub**
  - Code repository hosting
  - Collaboration and code review
- **GitHub Actions** (Infrastructure Ready)
  - CI/CD workflow automation framework
  - `.github/workflows/` directory structure in place
  - Ready for deployment pipeline implementation

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
- **pytest 7.4.0+**
  - Unit testing framework
  - Test automation
- **pytest-asyncio 0.21.0+**
  - Async testing support
- **Custom Test Frameworks**
  - RAG retrieval evaluation
  - End-to-end API testing
  - Performance benchmarking
  - Smoke testing utilities

### Utilities
- **Click 8.1.0+**
  - Command-line interface creation
- **tqdm 4.66.0+**
  - Progress bars for long-running operations
- **Logging**
  - Structured logging with JSON formatting
  - Log rotation and management

### Email & Notifications
- **smtplib** (Python Standard Library)
  - SMTP email sending
- **email.mime** (Python Standard Library)
  - Email message construction

### File Processing & Monitoring
- **Watchdog 3.0.0**
  - File system event monitoring
  - Real-time log file change detection
  - Used in log analysis system
- **Pathlib** (Python Standard Library)
  - Modern path manipulation
- **JSON/JSONL Processing**
  - Sample query management
  - Configuration processing

## Development Environment

### Base Environment
- **Python 3.11-slim Docker Image**
  - Lightweight Python runtime
  - Optimized for production deployment
- **PyEnv**
  - Python version management
  - Virtual environment isolation
- **Virtual Environments**
  - Dependency isolation
  - Clean development environments

### System Dependencies
- **build-essential**
  - Compilation tools for native extensions
- **git**
  - Version control and CI/CD integration
- **curl**
  - HTTP client for health checks

### Data Science & Analytics
- **Jupyter Notebooks**
  - Interactive data exploration
  - RAG quality evaluation
  - Retrieval performance analysis
- **Matplotlib**
  - Data visualization
  - Performance metrics plotting
- **Seaborn**
  - Statistical data visualization
  - Used in monitoring and evaluation scripts

## Monitoring & Observability

### Production Monitoring
- **Custom Production Monitoring System**
  - Real-time system health monitoring
  - Performance metrics collection
  - Cost tracking and optimization
  - Resource utilization monitoring
- **AWS CloudWatch Integration**
  - Custom metrics and dashboards
  - Log aggregation and analysis
  - Alert threshold management
- **Psutil**
  - System resource monitoring
  - CPU, memory, disk utilization
  - Process monitoring

### Intelligent Alerting Framework
- **Multi-Channel Alerting System**
  - Email notifications (SMTP/SES)
  - Slack integration
  - CloudWatch alarms
  - Webhook notifications
- **Alert Aggregation & Noise Reduction**
  - Smart alert batching
  - Escalation policies
  - Rate limiting and deduplication

### Log Analysis System
- **Real-time Log Monitoring**
  - Live log file monitoring with Watchdog
  - Pattern-based log parsing
  - Anomaly detection algorithms
  - Performance metric extraction

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
- **Data Exploration Tools**
  - Jupyter notebook analytics
  - Interactive data visualization
  - Query pattern analysis

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
- OpenSearch with enhanced configuration
- AWS Lambda with optimized memory allocation
- Enhanced monitoring and analytics
- Smart caching strategies

### Full Production Deployment ($25-68/month)
**Technologies Used:**
- Amazon OpenSearch cluster
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

## Automation & Deployment Scripts

### MLOps & Model Management
- **MLflow Integration Scripts**
  - `scripts/mlops/setup_mlops_pipeline.py` - MLflow experiment setup
  - `scripts/mlops/automated_retraining.py` - Model retraining with MLflow tracking
  - `scripts/mlops/model_monitoring.py` - Production model performance monitoring
- **Experiment Tracking**
  - Automated parameter logging
  - Model performance metrics collection
  - Model versioning and comparison

### Deployment Automation
- **Bash Scripting**
  - Infrastructure bootstrapping
  - Deployment automation
  - Environment setup
- **Python Automation Scripts**
  - Data ingestion pipelines
  - Monitoring system setup
  - Test data generation
  - Performance evaluation

### Development Workflow
- **Script-based Operations**
  - `bootstrap_opensearch.sh` - Search infrastructure setup
  - `deploy-student-stack.sh` - Student deployment automation
  - `run_ingestion.py` - Document processing pipeline
  - `eval_retrieval.py` - Retrieval quality assessment
  - `smoke_test.py` - End-to-end testing

### CI/CD Infrastructure
- **GitHub Actions Ready**
  - Workflow directory structure established
  - Ready for automated testing pipeline
  - Deployment automation framework in place
- **MLOps Pipeline Integration**
  - Automated model training and evaluation
  - Performance monitoring workflows
  - Model drift detection capabilities

## Data Processing Architecture

### ETL Pipeline Components
- **Document Ingestion**
  - PDF processing with OCR
  - Metadata extraction
  - Content validation
- **Embedding Generation**
  - Sentence transformer models
  - Vector space optimization
- **Index Management**
  - Hybrid indexing strategies
  - Schema management
  - Performance optimization

### Data Storage Patterns
- **Document Storage**
  - Raw document preservation
  - Processed content caching
  - Metadata indexing
- **Vector Storage**
  - Optimized vector retrieval
  - Similarity search optimization
  - Index health monitoring

---

*Last Updated: March 2026*
*Project: Quest Analytics RAG Assistant*
*Phase 5 Complete: Full Production Monitoring & Analytics Implementation*