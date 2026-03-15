# Quick Start: Production Deployment

## **IMMEDIATE ACTION REQUIRED**

AI RAG Assistant is ready for production! Follow these steps **TODAY**:

### **Step 1: Set Up AWS Account (10 minutes)**
```bash
# 1. Create AWS account (if needed): https://aws.amazon.com/

# 2. Create IAM user for deployment:
#    a) Go to AWS Console → IAM → Users → Create User
#    b) User Name: ai-rag-assistant-deployer
#    c) Select "Provide user access to the AWS Management Console" (optional)
#    d) Select "I want to create an IAM user"
#    e) Next: Attach policies directly → Search "AdministratorAccess" → Select it
#    f) Next: Review → Create user
#    g) Go to Security credentials tab → Create access key

#    Create Access Keys (Your Current Step):
#    Click on User: Click on the newly created user ai-rag-assistant-deployer
#    Security Credentials Tab: Click "Security credentials" tab
#    Create Access Key: Scroll down to "Access keys" section → Click "Create access key"
#    h) Use case: Select "Command Line Interface (CLI)" → Check acknowledgment → Next
#    i) Tag (optional): Add description "AI RAG Assistant deployment" → Create access key
#    j) IMPORTANT: Click "Download .csv file" button immediately (you cannot view these again!)
#    k) Store the downloaded CSV file securely - you'll need it for GitHub Secrets

# 3. Create S3 bucket for Terraform state (replace [random-number] with actual numbers):
#    RECOMMENDED Option B - Create manually in AWS Console:
#    a) Go to AWS Console → S3 → Create bucket
#    b) Bucket name: ai-rag-assistant-terraform-[random-number] (example: ai-rag-assistant-terraform-98765)
#    c) AWS Region: US East (N. Virginia) us-east-1
#    d) Object Ownership: ACLs disabled (recommended) - keep default
#    e) Block Public Access settings: Keep "Block all public access" checked (IMPORTANT for security)
#    f) Bucket Versioning: Enable (recommended for state files)
#    g) Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3) - keep default
#    h) Click "Create bucket"

#    Alternative Option A - If you have AWS CLI configured:
aws configure set aws_access_key_id YOUR_ACCESS_KEY_FROM_CSV
aws configure set aws_secret_access_key YOUR_SECRET_KEY_FROM_CSV  
aws configure set region us-east-1
aws s3 mb s3://ai-rag-assistant-terraform-[random-number]
```

### **Step 2: Configure GitHub Secrets (5 minutes)**
```bash
# Go to: https://github.com/Petlaz/ai_rag_assistant → Settings → Security → Secrets and variables → Actions
# Click on "Repository secrets" tab → Click "New repository secret"
```
**Add these secrets using values from your downloaded CSV:**
1. `AWS_ACCESS_KEY_ID` → Copy "Access key ID" from CSV (starts with AKIA...)
2. `AWS_SECRET_ACCESS_KEY` → Copy "Secret access key" from CSV (40 character string)  
3. `TERRAFORM_STATE_BUCKET` → `ai-rag-assistant-terraform-[random-number]` (same bucket name you created)

### **Step 3: Deploy to Production (15 minutes)**
```bash
# Clone fresh copy
git clone https://github.com/Petlaz/ai_rag_assistant.git
cd ai_rag_assistant

# Deploy infrastructure
cd deployment/aws
terraform init
terraform apply -var="deployment_mode=ultra-budget"

# Push to trigger CI/CD
git push origin main
```

---

## **4-Week Timeline Quick Reference**

| Week | Focus | Key Milestone |
|------|-------|---------------|
| **Week 1-2** | AWS Deployment | Live production system |
| **Week 3** | User Testing | Real user feedback |
| **Week 4** | Optimization | Performance improvements |

---

## **Expected Costs**

**Ultra-Budget Mode**: $8-18/month
- Lambda Functions: $0-5
- S3 Storage: $1-3
- CloudWatch: $2-5
- Data Transfer: $1-5

**Total**: Well within budget for production testing!

---

## **Your Current Status**

- **Code Complete**: 40% optimized performance
- **Infrastructure Ready**: GitHub Actions + Terraform
- **Monitoring Setup**: CloudWatch + MLflow
- **Security Implemented**: Authentication + rate limiting
- **Documentation Complete**: Comprehensive guides

**I am literally ready to deploy RIGHT NOW!** 

---

## **Need Help?**

**Full Guide**: See `PRODUCTION_DEPLOYMENT_ROADMAP.md`  
**Quick Questions**: Check `docs/` directory  
**Emergency**: Use rollback scripts in `scripts/deployment/`

**LET'S GET YOUR AI RAG ASSISTANT LIVE IN PRODUCTION!**