# Pre-Deployment Checklist
*Complete these steps before running your AWS deployment*

---

## Quick Status Check

Run this command to see what's ready:
```bash
cd /Users/peter/AI_ML_Projects/AI_RAG
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=15
```

**Expected Error**: "AWS CLI is not installed" (We'll fix this below)

---

## Required Preparations

### 1. Install AWS CLI
```bash
# Option A: Using Homebrew (recommended for macOS)
brew install awscli

# Option B: Using pip
pip install awscli

# Verify installation
aws --version
```

### 2. Configure AWS Credentials
```bash
# Run AWS configuration
aws configure

# You'll need:
# - AWS Access Key ID (from AWS Console → IAM)
# - AWS Secret Access Key (from AWS Console → IAM)  
# - Default region: us-east-1 (recommended for lowest costs)
# - Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### 3. Set Up Billing Alerts (CRITICAL for students!)
```bash
# Check current month costs (should be $0 before deployment)
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost

# Create billing alert at $15 (80% of $20 budget)
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "RAG-Ultra-Budget-Alert",
    "BudgetLimit": {
      "Amount": "20",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN", 
      "Threshold": 80
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "your-email@example.com"
    }]
  }]'
```

### 4. Verify Python Environment
```bash
cd /Users/peter/AI_ML_Projects/AI_RAG

# Check Python version
python --version  # Should be 3.11+

# Verify dependencies
pip install -r requirements.txt

# Test local app (optional)
python deployment/app_gradio.py
```

---

## Deployment Day Checklist

### Before Running Deployment:
- [ ] AWS CLI installed and configured
- [ ] Billing alerts set up at 80% of budget  
- [ ] Current month costs = $0
- [ ] Region set to us-east-1 (lowest costs)
- [ ] Email notifications enabled
- [ ] 30 minutes of uninterrupted time

### During Deployment:
- [ ] Monitor CloudFormation events in AWS Console
- [ ] Watch for any error messages in terminal
- [ ] Check costs in real-time (AWS Cost Explorer)
- [ ] Take screenshots for portfolio documentation

### After Deployment:
- [ ] Test the deployed application
- [ ] Verify all services are running
- [ ] Check actual costs vs estimates
- [ ] Document the architecture for interviews
- [ ] Set up daily cost monitoring

---

## Ultra-Budget Deployment Command

Once everything is ready, run:
```bash
cd /Users/peter/AI_ML_Projects/AI_RAG
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=20
```

**Expected Cost**: $8-18/month
**Deployment Time**: 20-30 minutes
**Services Created**: Lambda + S3 + DynamoDB + Function URLs

---

## Troubleshooting Quick Fixes

### If AWS CLI fails:
```bash
# Check if AWS CLI is in PATH
which aws

# If not found, add to shell profile
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### If credentials don't work:
```bash
# Check current credentials
aws configure list

# Reconfigure if needed
aws configure

# Test with simple command
aws s3 ls
```

### If deployment fails:
```bash
# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name rag-assistant-ultra

# View stack events
aws cloudformation describe-stack-events --stack-name rag-assistant-ultra

# Emergency cleanup
aws cloudformation delete-stack --stack-name rag-assistant-ultra
```

---

## Expected Deployment Flow

1. **Prerequisites Check** (2 min)
2. **CloudFormation Stack Creation** (5 min)
3. **Lambda Function Deployment** (3 min)
4. **S3 Bucket Configuration** (2 min)
5. **DynamoDB Table Setup** (1 min)
6. **Function URLs Configuration** (2 min)
7. **Testing and Validation** (5 min)

**Total**: ~20 minutes for ultra-budget mode

---

**You're ready for deployment success!** 

The ultra-budget mode is perfect for demonstrating your cost optimization skills in job interviews.