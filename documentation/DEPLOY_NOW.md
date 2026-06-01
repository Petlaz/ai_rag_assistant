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

## **Beginner AWS Setup: Start Over from Scratch**

If you are new to AWS, follow these step-by-step instructions to create the IAM user, access key, secret key, and S3 bucket required by this project.

### Step 1: Create an AWS Account
1. Go to https://aws.amazon.com/ and sign up for a new AWS account.
2. Complete the registration steps, including email verification and phone number verification.
3. Add a payment method when prompted. The Free Tier is suitable for this project.

### Step 2: Create an IAM User for Deployment
1. Open the AWS Console: https://console.aws.amazon.com/
2. Search for **IAM** and open the IAM service.
3. In the left menu, click **Users**.
4. Click **Add users**.
5. Enter a user name, such as `ai-rag-assistant-deployer`.
6. Under **Select AWS access type**, check **Programmatic access**.
7. Click **Next: Permissions**.
8. Choose **Attach existing policies directly**.
9. Search for and select **AdministratorAccess**.
   - This gives the user full permissions for deployment.
   - For a stricter setup later, use least-privilege permissions.
10. Click **Next: Tags** (optional), then **Next: Review**.
11. Click **Create user**.
12. Download the CSV file or copy both values:
   - `Access key ID`
   - `Secret access key`

> Save these values securely. The secret access key is shown only once.

### Step 3: Create an S3 Bucket for Terraform State
Terraform stores the deployment state in an S3 bucket. Create one now.

1. In the AWS Console, search for **S3** and open the S3 dashboard.
2. Click **Create bucket**.
3. For **Bucket name**, choose a globally unique name, for example:
   - `ai-rag-assistant-terraform-123456`
4. For **Region**, select `us-east-1`.
5. Under **Object Ownership**, choose **ACLs disabled**.
6. Leave **Block all public access** enabled.
7. Click **Create bucket**.

### Step 4: Install and Configure AWS CLI (Optional)
If you want to use AWS CLI locally, install it and configure your credentials.

```bash
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

Then run:

```bash
aws configure
```

Enter:
- `AWS Access Key ID`: your IAM access key ID
- `AWS Secret Access Key`: your secret access key
- `Default region name`: `us-east-1`
- `Default output format`: `json`

### Step 5: Add GitHub Secrets for CI/CD
Your GitHub Actions workflow needs the AWS credentials and S3 bucket name.

1. Open your repository on GitHub: `https://github.com/Petlaz/ai_rag_assistant`
2. Go to **Settings** -> **Secrets and variables** -> **Actions**.
3. Click **New repository secret**.
4. Create these secrets:

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | Your IAM access key ID |
| `AWS_SECRET_ACCESS_KEY` | Your IAM secret access key |
| `TERRAFORM_STATE_BUCKET` | Your S3 bucket name, e.g. `ai-rag-assistant-terraform-123456` |

---

## **When to Add Permissions and When to Create Lambda Functions**

As a beginner, it helps to think of these steps in order:

1. **Add permissions first**
   - Create the IAM deployment user and generate the access key + secret key.
   - Add those credentials to GitHub Secrets before you deploy.
   - The deployment user needs permissions so GitHub Actions can create AWS resources.

2. **Create Lambda functions later**
   - You do not manually create Lambda functions first.
   - Terraform will create the Lambda functions during deployment.
   - This happens when the GitHub Actions workflow runs and applies Terraform.

So the safe order is:
- set up AWS account and IAM user,
- create the S3 bucket,
- add GitHub Secrets,
- then push code and let the workflow create Lambda functions for you.

---

## **Deploy**

After setup, deploy by pushing code to GitHub:

```bash
git push origin main
```

This triggers the GitHub Actions workflow, which:
1. Validates the repository and environment
2. Builds Docker images
3. Pushes images to GHCR and AWS ECR
4. Runs Terraform to create/update Lambda functions
5. Performs post-deployment tests

### Manual trigger
In GitHub Actions, open the **Deploy to AWS** workflow and click **Run workflow**.

---

## **Verify the Deployment**

Use the Lambda Function URL from Terraform output or the AWS Console.

```bash
APP_URL="https://<your-id>.lambda-url.us-east-1.on.aws/"

curl -s "$APP_URL/health" | python -m json.tool
curl -s -o /dev/null -w "%{http_code}" "$APP_URL"
```

Expected response: HTTP `200`.

> If the app page loads but the model status stays stuck on `Checking...`, verify the Lambda app URL is the correct `app` function URL and that `OLLAMA_BASE_URL` points to a reachable Ollama service from Lambda.
>
> In staging or production deployments, `OLLAMA_BASE_URL` must be set in `infra/terraform/terraform.tfvars` or passed through your Terraform variables. `http://localhost:11434` will not work from Lambda.
>
> The live landing page may use a different Function URL than the actual Gradio app URL.

---

## **Start Over Safely**

If you want to reset your deployment and start again:
1. Delete the Lambda functions in AWS Lambda.
2. Delete the S3 bucket used for Terraform state.
3. Delete any project-related ECR repositories.
4. Remove old GitHub secrets if you want to rotate keys.
5. Create a new IAM user and a new S3 bucket by repeating the previous steps.

---

## **What Happens Inside Lambda**

The app container runs `lambda_app_handler.lambda_handler` through `awslambdaric`.

**Request routing:**
- `GET /health` -> 200 JSON (`{"status": "healthy"}`)
- `GET /` -> 200 HTML for the web page
- `/api/*`, `/queue/*`, `/config` -> Mangum/Gradio ASGI handler

Note: Gradio does not use `.launch()` in Lambda, so we return HTML through our own routing layer.

---

## **Troubleshooting**

| Problem | Fix |
|---------|-----|
| Missing AWS keys | Recreate the IAM access key in IAM and re-add GitHub secrets |
| Terraform state error | Confirm `TERRAFORM_STATE_BUCKET` matches your S3 bucket name |
| 500 from Function URL | Check CloudWatch logs in the Lambda console |
| Workflow fails | Review the GitHub Actions run logs and ensure secrets are set |
| App shows `LLM Status: Checking...` | Confirm the app Function URL is correct and `OLLAMA_BASE_URL` is reachable from Lambda |
| Image push failure | Ensure GitHub Container Registry and AWS ECR credentials are available |

---

## **Helpful Links**

- `infra/terraform/` — Terraform deployment configuration
- `.github/workflows/cicd-03-aws-deployment.yml` — CI/CD workflow
- `deployment/aws/docker/` — Docker files for Lambda images
- `lambda_app_handler.py` — Lambda entrypoint
- `documentation/PRODUCTION_DEPLOYMENT_ROADMAP.md` — deployment planning guide
- `documentation/LESSONS_LEARNED.md` — troubleshooting notes
