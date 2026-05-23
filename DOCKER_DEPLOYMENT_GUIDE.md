# Docker Deployment Guide - Quest Analytics RAG Assistant

## Overview

This guide explains how to:
1. **Build and test locally** using Docker Compose
2. **Generate both local and public URLs** for testing
3. **Diagnose and fix configuration issues** before AWS deployment
4. **Deploy to AWS Lambda** with proper environment variables

---

## File Structure

The Docker setup is located in `deployment/aws/docker/`:

```
deployment/aws/docker/
├── Dockerfile.app       # Gradio application container
├── Dockerfile.landing   # FastAPI landing page container
├── Dockerfile.worker    # Background job processor
├── docker-compose.dev.yml  # Local development setup
├── .env.example         # Environment variables template
└── .dockerignore        # Optimize build context
```

Convenience script in project root:
- `docker-start.sh` - Easy commands to manage Docker services

---

## Problem Summary

The Lambda URL was redirecting to `localhost`, which is unreachable from a browser because:
- **Landing page** didn't know the correct Gradio app URL
- **Gradio app** was defaulting to `localhost:11434` for Ollama
- **Environment variables** weren't being passed to Lambda functions
- **No local testing setup** made it impossible to validate before AWS

## Solution Implemented

### 1. Fixed Code Configuration

Updated to prevent localhost fallback in production:

#### `/landing/main.py` & `/landing/secure_main.py`
```python
# Before: APP_URL = os.getenv("APP_URL", "http://localhost:7860")
# After: Validates environment and fails safely if not set in production
```

#### `/deployment/app_gradio.py`
```python
# Before: base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# After: Requires explicit configuration in production
```

### 2. Updated Terraform Configuration

#### `/infra/terraform/variables.tf`
Added new variables for service configuration:
- `ollama_base_url` - Ollama service endpoint
- `opensearch_host` - OpenSearch domain endpoint
- `ollama_model` - Model name
- And more...

#### `/infra/terraform/lambda.tf`
Updated Lambda environment variables to pass configuration

### 3. Improved Docker Infrastructure

Enhanced existing Dockerfiles in `deployment/aws/docker/`:
- Better environment variable handling
- Support for both local development and Lambda deployment
- Proper health checks

---

## Local Testing with Docker Compose

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v2.0+
- ~5GB disk space for images and volumes
- 4GB+ RAM available

### Step 1: Make script executable and start services

```bash
cd /Users/peter/Desktop/ai_rag_assistant

# Make script executable
chmod +x docker-start.sh

# Start all services
./docker-start.sh start

# Or run from anywhere with full path
/Users/peter/Desktop/ai_rag_assistant/docker-start.sh start
```

### Step 2: Watch logs for initialization

```bash
./docker-start.sh logs

# Or use docker directly
cd deployment/aws/docker
docker-compose -f docker-compose.dev.yml logs -f
```

**Note:** First startup takes 2-3 minutes while:
- OpenSearch initializes cluster
- Ollama starts server
- Gradio builds interface
- Landing page starts

### Step 3: Verify services

```bash
./docker-start.sh status

# Or check individual services
curl http://localhost:9200           # OpenSearch
curl http://localhost:11434/api/tags # Ollama
curl http://localhost:7860/info      # Gradio
curl http://localhost:3000           # Landing page
```

### Step 4: Access the application

#### Local URLs:
- **Landing Page**: http://localhost:3000
- **Gradio App**: http://localhost:7860
- **OpenSearch**: http://localhost:9200
- **Ollama**: http://localhost:11434

#### Public URL (if needed):
If running on a cloud VM or need external access:
```bash
# Get your machine's IP
ipconfig getifaddr en0  # macOS
ifconfig             # Linux

# Then use: http://<YOUR_IP>:3000 or http://<YOUR_IP>:7860
```

### Step 5: Test the application

1. Open http://localhost:3000 in your browser
2. Click "Launch App" to go to http://localhost:7860
3. Upload a document
4. Ask research questions
5. Verify answers with source citations

### Step 6: Monitor logs

```bash
# View all logs
./docker-start.sh logs

# Or view specific service
cd deployment/aws/docker
docker-compose -f docker-compose.dev.yml logs rag-app

# Search for errors
./docker-start.sh logs | grep -i error
```

### Step 7: Pull models in Ollama (optional)

If Ollama is running but no model loaded:

```bash
# Pull a model
docker exec ollama ollama pull llama2          # 4B model (~7GB)
docker exec ollama ollama pull mistral         # 7B model (~4GB)
docker exec ollama ollama pull neural-chat     # Smaller option
```

---

## Using docker-start.sh Script

```bash
# Start all services
./docker-start.sh start

# Stop services
./docker-start.sh stop

# Restart services
./docker-start.sh restart

# View logs
./docker-start.sh logs

# Check status
./docker-start.sh status

# Run health checks
./docker-start.sh test

# Download models
./docker-start.sh pull-models

# Clean everything
./docker-start.sh clean

# Show help
./docker-start.sh help
```

---

## Troubleshooting Local Setup

### Issue: "docker-compose: command not found"
```bash
# Install Docker Desktop which includes docker-compose
# Or upgrade with: pip install docker-compose
```

### Issue: Port Already in Use
```bash
# Find what's using the port
lsof -i :7860

# Edit deployment/aws/docker/docker-compose.dev.yml:
# ports:
#   - "7861:7860"  # Use 7861 instead

# Then restart
./docker-start.sh restart
```

### Issue: Gradio Container Exits Immediately
```bash
# Check logs
./docker-start.sh logs

# Common causes:
# 1. OLLAMA_BASE_URL not set correctly
# 2. OPENSEARCH_HOST not reachable
# 3. Missing Python dependencies

# Re-build without cache
cd deployment/aws/docker
docker-compose -f docker-compose.dev.yml build --no-cache rag-app
./docker-start.sh restart
```

### Issue: Landing Page Shows "Cannot reach app"
```bash
# Verify APP_URL environment variable in docker-compose.dev.yml
# Should point to the service name: http://rag-app:7860

# Edit the file and restart
./docker-start.sh restart
```

### Issue: OpenSearch Cluster Not Forming
```bash
# Common cause: Not enough memory
# Edit Docker Desktop settings to increase allocated RAM

# Check cluster status
curl http://localhost:9200/_cluster/health

# Should show: "status": "yellow" or "green"
```

---

## AWS Lambda Deployment

### Step 1: Verify Local Setup Works

```bash
# Ensure local Docker setup completes successfully
./docker-start.sh start
./docker-start.sh test

# Upload a document and test chat
# Check all endpoints respond
```

### Step 2: Update Terraform Variables

Create `infra/terraform/terraform.tfvars`:

```hcl
environment           = "production"
deployment_mode       = "balanced"

# CRITICAL: Set these before deploying!
ollama_base_url      = "https://ollama.your-domain.com"
opensearch_host      = "my-domain.us-east-1.es.amazonaws.com:9200"
opensearch_username  = "admin"
opensearch_password  = "SecurePassword123!"

ollama_model          = "llama2"
ollama_fallback_model = "mistral"
embedding_model_name  = "all-MiniLM-L6-v2"
enable_analytics      = true
security_enabled      = true
```

### Step 3: Build Container Images

```bash
cd deployment/aws/docker

# Build Gradio app image
docker build -f Dockerfile.app -t ghcr.io/petlaz/rag-assistant:latest ../../..

# Build landing page image
docker build -f Dockerfile.landing -t ghcr.io/petlaz/rag-landing:latest ../../..

# Push to registry (ECR or GitHub Container Registry)
docker push ghcr.io/petlaz/rag-assistant:latest
docker push ghcr.io/petlaz/rag-landing:latest
```

### Step 4: Deploy with Terraform

```bash
cd infra/terraform

# Initialize Terraform
terraform init \
  -backend-config="bucket=your-tf-bucket" \
  -backend-config="key=ai-rag/terraform.tfstate" \
  -backend-config="region=us-east-1"

# Review changes
terraform plan -var-file=terraform.tfvars

# Apply
terraform apply -var-file=terraform.tfvars
```

### Step 5: Verify Lambda Deployment

```bash
# Get Lambda URLs
terraform output app_function_url
terraform output landing_function_url

# Test landing page
curl https://your-landing-url.lambda-url.us-east-1.on.aws/

# Test Gradio app
curl https://your-app-url.lambda-url.us-east-1.on.aws/info
```

---

## Cleanup

### Local Docker Cleanup

```bash
# Stop all containers
./docker-start.sh stop

# Remove volumes (clears data)
./docker-start.sh clean

# Or manually
cd deployment/aws/docker
docker-compose -f docker-compose.dev.yml down -v
```

### AWS Lambda Cleanup

```bash
cd infra/terraform
terraform destroy -var-file=terraform.tfvars
```

---

## Environment Variables Reference

### Lambda (Production)

| Variable | Required | Example | Purpose |
|----------|----------|---------|---------|
| `ENVIRONMENT` | Yes | `production` | Enables strict validation |
| `OLLAMA_BASE_URL` | Yes | `https://ollama.company.com` | LLM service endpoint |
| `OPENSEARCH_HOST` | Yes | `domain.us-east-1.es.amazonaws.com:9200` | Vector DB endpoint |
| `OLLAMA_MODEL` | Yes | `llama2` | Primary model |
| `EMBEDDING_MODEL_NAME` | No | `all-MiniLM-L6-v2` | Embeddings model |
| `SECURITY_ENABLED` | No | `true` | Enable rate limiting |
| `ENABLE_ANALYTICS` | No | `true` | Track usage |

### Docker Compose (Local)

Same as above, but:
- `OLLAMA_BASE_URL=http://ollama:11434` (internal hostname)
- `OPENSEARCH_HOST=http://opensearch:9200` (internal hostname)
- `ENVIRONMENT=local` (enables localhost fallback)

---

## Additional Resources

- [Gradio Deployment Guide](https://www.gradio.app/guides/deploying-your-app)
- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)



