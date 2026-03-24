# Quick Start: Production Deployment

## **How It Actually Works**

The app runs on **AWS Lambda Function URLs** — no EC2 instances, no ECS clusters, no load balancers. The CI/CD pipeline (`git push origin main`) handles everything automatically.

### Architecture
```
GitHub Actions (CI/CD)
  1. Builds Docker images (app, landing, worker)
  2. Pushes to GHCR + mirrors to ECR
  3. Terraform creates/updates Lambda functions from container images
  4. Lambda Function URLs provide public HTTPS endpoints
  5. Post-deployment tests verify the live URL returns 200
```

### Lambda Functions Created by Terraform (`infra/terraform/lambda.tf`)
| Function | Image | Memory | Timeout | Purpose |
|----------|-------|--------|---------|---------|
| `{env}-ai-rag-assistant-app` | `Dockerfile.app` | Configurable | 60s | Main RAG interface |
| `{env}-ai-rag-assistant-landing` | `Dockerfile.landing` | 256 MB | 60s | Landing page |
| `{env}-ai-rag-assistant-worker` | `Dockerfile.worker` | Configurable | 300s | Background processing |

Each function gets a **Function URL** with `NONE` authorization (public access).

---

## **Prerequisites (One-Time Setup)**

### Step 1: AWS Account + IAM User (10 minutes)
```bash
# 1. Create AWS account: https://aws.amazon.com/
# 2. Create IAM user: AWS Console -> IAM -> Users -> Create User
#    Name: ai-rag-assistant-deployer
#    Policy: AdministratorAccess
#    Create access key (CLI use case) -> Download CSV immediately
```

### Step 2: S3 Bucket for Terraform State
```bash
# AWS Console -> S3 -> Create bucket
#   Name: ai-rag-assistant-terraform-<random-number>
#   Region: us-east-1
#   Block all public access: YES
#   Versioning: Enabled
```

### Step 3: GitHub Secrets (5 minutes)
Go to `https://github.com/Petlaz/ai_rag_assistant` -> Settings -> Secrets -> Actions

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | From CSV (starts with `AKIA...`) |
| `AWS_SECRET_ACCESS_KEY` | From CSV (40-char string) |
| `TERRAFORM_STATE_BUCKET` | `ai-rag-assistant-terraform-<your-number>` |

---

## **Deploy**

```bash
git push origin main
```

That's it. GitHub Actions runs the full pipeline:
1. **validate-deployment** — checks required files exist
2. **build-and-push** — builds 3 Docker images, pushes to GHCR + ECR
3. **deploy-infrastructure** — `terraform apply` creates Lambda functions + Function URLs
4. **deploy-application** — runs validation scripts
5. **post-deployment-tests** — curls the Function URL, expects 200 + HTML

### Manual trigger
Go to Actions -> "Deploy to AWS" -> Run workflow -> pick environment/mode.

---

## **What Happens Inside Lambda**

The app container runs `lambda_app_handler.lambda_handler` via `awslambdaric`.

**Request routing:**
- `GET /health` -> 200 JSON (`{"status": "healthy"}`)
- `GET /` (and other page requests) -> 200 HTML (fallback page)
- `/api/*`, `/queue/*`, `/config` -> Mangum/Gradio ASGI handler

**Key detail:** Gradio's Jinja2 templates don't work in Lambda (no `.launch()` call), so page requests return our own HTML. See `documentation/LESSONS_LEARNED.md` for the full story.

---

## **Verify It's Working**

```bash
# Get your Function URL from Terraform output or AWS Console
APP_URL="https://<your-id>.lambda-url.us-east-1.on.aws/"

# Health check
curl -s "$APP_URL/health" | python -m json.tool

# Main page (should return HTML with "Quest Analytics")
curl -s -o /dev/null -w "%{http_code}" "$APP_URL"
# Expected: 200
```

---

## **Costs (Ultra-Budget Mode)**

| Service | Monthly Cost |
|---------|-------------|
| Lambda | $0-5 (pay per request) |
| ECR | $1-2 (image storage) |
| S3 | $0.50 (Terraform state) |
| CloudWatch | $2-5 (logs) |
| **Total** | **$4-13/month** |

---

## **Troubleshooting**

| Problem | Fix |
|---------|-----|
| 500 from Function URL | Check CloudWatch logs: Lambda console -> Monitor -> View logs |
| `000` response code | Cold start timeout — increase Lambda timeout or retry after 30s |
| Terraform state error | Verify S3 bucket name matches `TERRAFORM_STATE_BUCKET` secret |
| Image not found | Check GHCR packages are public: github.com -> Packages |
| Post-deploy test fails | Check if Function URL returns 200 — `curl -v $APP_URL` |

---

## **Useful Links**

- **Full deployment guide**: `documentation/PRODUCTION_DEPLOYMENT_ROADMAP.md`
- **Lessons learned**: `documentation/LESSONS_LEARNED.md`
- **Terraform config**: `infra/terraform/`
- **Docker configs**: `deployment/aws/docker/`
- **CI/CD workflow**: `.github/workflows/cicd-03-aws-deployment.yml`
- **Lambda handler**: `lambda_app_handler.py`
- **Rollback**: `scripts/deployment/rollback_system.py`