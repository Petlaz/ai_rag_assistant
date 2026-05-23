# Lambda Deployment Fix - Summary of Changes

## Root Cause

The Lambda URL was returning "localhost refused to connect" because:

1. **Landing page Lambda** got the correct app Lambda URL but didn't pass it to Gradio
2. **Gradio Lambda** had no environment variables for Ollama or OpenSearch - defaulted to localhost
3. **Code had hardcoded localhost fallbacks** that never checked production requirements
4. **No local Docker setup** made it impossible to test before deploying to AWS

## Files Created

### Docker Infrastructure (NEW)

| File | Purpose |
|------|---------|
| `Dockerfile.app` | Build Gradio app container image |
| `Dockerfile.landing` | Build landing page container image |
| `docker-compose.yaml` | Orchestrate local testing environment |
| `.dockerignore` | Optimize Docker build context |
| `docker-start.sh` | Easy script for starting/stopping services |
| `DOCKER_DEPLOYMENT_GUIDE.md` | Complete deployment documentation |

## Files Modified

### Code Changes (Fixed localhost hardcoding)

#### 1. `landing/main.py`
```python
# BEFORE
APP_URL = os.getenv("APP_URL", "http://localhost:7860")

# AFTER - Fails safely in production if not set
APP_URL = os.getenv("APP_URL")
if not APP_URL:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("APP_URL environment variable is required...")
    APP_URL = "http://localhost:7860"  # Local dev fallback
```

#### 2. `landing/secure_main.py`
Same pattern applied to prevent localhost redirect in production

#### 3. `deployment/app_gradio.py` (Line ~1258)
```python
# BEFORE
base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# AFTER - Proper validation for production
base_url = os.getenv("OLLAMA_BASE_URL")
if not base_url:
    if os.getenv("ENVIRONMENT") == "production":
        return state, "ERROR: OLLAMA_BASE_URL required..."
    base_url = "http://localhost:11434"  # Local dev fallback
```

### Infrastructure Changes (Terraform)

#### 4. `infra/terraform/variables.tf`
Added 10 new variables:
- `ollama_base_url` - Ollama service endpoint (REQUIRED)
- `opensearch_host` - OpenSearch domain (REQUIRED)
- `ollama_model` - Model name
- `ollama_fallback_model` - Fallback model
- `embedding_model_name` - Embeddings model
- `opensearch_index_name` - Index name
- `opensearch_username` - OpenSearch auth
- `opensearch_password` - OpenSearch auth
- `security_enabled` - Security middleware toggle
- `enable_analytics` - Analytics toggle

#### 5. `infra/terraform/lambda.tf`
Updated both Lambda functions with comprehensive environment variables:

**App Lambda** now receives:
- OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL
- OPENSEARCH_HOST, OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD
- EMBEDDING_MODEL_NAME
- Security and analytics settings

**Landing Lambda** now receives:
- APP_URL (correctly set to app Lambda URL)
- LANDING_PORT
- ANALYTICS_ENABLED

## How to Use

### Option 1: Test Locally (RECOMMENDED FIRST)

```bash
# Make script executable
chmod +x docker-start.sh

# Start all services
./docker-start.sh start

# Watch logs
./docker-start.sh logs

# Check status
./docker-start.sh status

# Access at:
# - Landing: http://localhost:3000
# - Gradio: http://localhost:7860
```

### Option 2: Deploy to AWS

1. **Update terraform.tfvars:**
```hcl
environment           = "production"
ollama_base_url      = "https://your-ollama-service"
opensearch_host      = "your-domain.us-east-1.es.amazonaws.com:9200"
opensearch_username  = "admin"
opensearch_password  = "YourSecurePassword"
```

2. **Test locally first:**
```bash
./docker-start.sh start
./docker-start.sh test
```

3. **Build and push containers:**
```bash
docker build -f Dockerfile.app -t ghcr.io/petlaz/rag-assistant:latest .
docker build -f Dockerfile.landing -t ghcr.io/petlaz/rag-landing:latest .
docker push ghcr.io/petlaz/rag-assistant:latest
docker push ghcr.io/petlaz/rag-landing:latest
```

4. **Deploy with Terraform:**
```bash
cd infra/terraform
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Key Improvements

### 1. **Localhost Prevention**
- Code now fails explicitly in production if required variables not set
- Prevents silent fallback to localhost on AWS
- Clear error messages guide users to fix configuration

### 2. **Local Testing**
- Docker Compose provides complete local environment
- OpenSearch, Ollama, Gradio, and Landing page all work together
- Easy to test before AWS deployment

### 3. **Configuration Management**
- All service URLs centralized in Terraform variables
- Environment-specific behavior (local vs production)
- Easy to update endpoints without code changes

### 4. **Better Error Handling**
- Gradio app checks Ollama connection on startup
- Landing page validates app URL is reachable
- Health checks in Docker containers

## Testing Checklist

- [ ] Start Docker services: `./docker-start.sh start`
- [ ] Wait 2-3 minutes for initialization
- [ ] Check status: `./docker-start.sh status`
- [ ] Visit http://localhost:3000 (landing page)
- [ ] Click "Launch App" to go to Gradio
- [ ] Upload a test document
- [ ] Ask a research question
- [ ] Verify source citations work
- [ ] Check logs for errors: `./docker-start.sh logs`
- [ ] Run tests: `./docker-start.sh test`
- [ ] Clean up: `./docker-start.sh clean`

## Before AWS Deployment

⚠️ **CRITICAL** - Must be done before `terraform apply`:

1. **Provision external services:**
   - Set up Ollama service (EC2, ECS, or managed service)
   - Set up OpenSearch domain on AWS
   - OR use container orchestration (ECS Fargate) for both

2. **Update terraform.tfvars with real URLs:**
   ```hcl
   ollama_base_url = "actual-service-url"
   opensearch_host = "actual-opensearch-url"
   ```

3. **Build and push Docker images:**
   ```bash
   docker push ghcr.io/petlaz/rag-assistant:latest
   docker push ghcr.io/petlaz/rag-landing:latest
   ```

4. **Validate locally one more time:**
   ```bash
   ./docker-start.sh start
   ./docker-start.sh test
   # Test upload, chat, etc.
   ./docker-start.sh clean
   ```

## Common Issues & Fixes

### Issue: Landing page shows "Cannot reach app"
**Fix:** Check docker-compose.yaml APP_URL matches rag-app service name

### Issue: Gradio app won't start
**Fix:** Ensure OLLAMA_BASE_URL and OPENSEARCH_HOST are correctly set in docker-compose.yaml

### Issue: "Port already in use"
**Fix:** Change port mappings in docker-compose.yaml (e.g., 7861:7860)

### Issue: Lambda URL still redirects to localhost
**Fix:** Verify terraform.tfvars has ollama_base_url and opensearch_host set, then redeploy

## Next Steps

1. ✅ **Read this summary** - You're here!
2. ⏭️ **Test locally with Docker**
   ```bash
   chmod +x docker-start.sh
   ./docker-start.sh start
   ```
3. ⏭️ **Provision external services** (Ollama + OpenSearch on AWS)
4. ⏭️ **Update terraform.tfvars**
5. ⏭️ **Deploy to AWS**
   ```bash
   cd infra/terraform
   terraform apply -var-file=terraform.tfvars
   ```

## Questions?

- See `DOCKER_DEPLOYMENT_GUIDE.md` for detailed deployment guide
- Check docker-compose.yaml for service configuration
- Review Terraform files for AWS infrastructure
- Use `./docker-start.sh help` for script options

