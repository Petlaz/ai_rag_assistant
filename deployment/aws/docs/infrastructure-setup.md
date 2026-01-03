# 🏗️ AWS Infrastructure Setup Guide
*Step-by-step AWS account preparation for RAG Assistant deployment*

---

## 📋 Prerequisites Checklist

### AWS Account Setup
- [ ] Create AWS account (use student email for credits)
- [ ] Activate [AWS Educate](https://aws.amazon.com/education/awseducate/) or [AWS Academy](https://aws.amazon.com/training/awsacademy/)
- [ ] Verify student credits are applied ($100+ recommended)
- [ ] Set up billing alerts at $25, $40, $50

### Local Development Environment
- [ ] Install [AWS CLI v2](https://aws.amazon.com/cli/)
- [ ] Configure AWS credentials (`aws configure`)
- [ ] Install [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) (optional)
- [ ] Verify Docker is running

---

## 🔑 AWS Account Configuration

### 1. Create IAM User for Deployment
```bash
# Create deployment user with programmatic access
aws iam create-user --user-name rag-deployment-user

# Create access keys
aws iam create-access-key --user-name rag-deployment-user

# Attach necessary policies (minimal permissions for security)
aws iam attach-user-policy \
  --user-name rag-deployment-user \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```

### 2. Configure AWS CLI
```bash
# Set up AWS credentials
aws configure

# Verify configuration
aws sts get-caller-identity
aws account get-contact-information
```

### 3. Enable Required AWS Services
```bash
# Verify Bedrock access (required for LLM)
aws bedrock list-foundation-models --region us-east-1

# Check OpenSearch Serverless availability
aws opensearchserverless list-collections --region us-east-1

# Verify Lambda limits
aws lambda get-account-settings --region us-east-1
```

---

## 💰 Cost Management Setup

### Set Up Billing Alerts
```bash
# Create SNS topic for billing alerts
aws sns create-topic --name billing-alerts --region us-east-1

# Subscribe your email to alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:billing-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### Create Budget
```bash
# Create monthly budget with alerts
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

### Budget Configuration Files

**budget.json**:
```json
{
  "BudgetName": "RAG-Assistant-Student-Budget",
  "BudgetLimit": {
    "Amount": "50.00",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {
    "Service": [
      "Amazon Simple Storage Service",
      "AWS Lambda",
      "Amazon API Gateway",
      "Amazon OpenSearch Service",
      "Amazon Bedrock",
      "Amazon DynamoDB"
    ]
  }
}
```

**notifications.json**:
```json
[
  {
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80.0,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [
      {
        "SubscriptionType": "EMAIL",
        "Address": "your-email@example.com"
      }
    ]
  }
]
```

---

## 🌍 Region Selection & Optimization

### Recommended Region: us-east-1 (N. Virginia)
**Why us-east-1?**
- ✅ Lowest pricing for most services
- ✅ All services available (Bedrock, OpenSearch Serverless)
- ✅ Best for student deployments
- ✅ Primary region for AWS free tier

### Region Comparison
| Region | Bedrock | OpenSearch | Lambda | S3 | Cost |
|--------|---------|------------|--------|----|----- |
| us-east-1 | ✅ | ✅ | Cheapest | Cheapest | ⭐⭐⭐ |
| us-west-2 | ✅ | ✅ | +10% | +5% | ⭐⭐ |
| eu-west-1 | ✅ | ✅ | +15% | +10% | ⭐ |

---

## 🔐 Security Best Practices

### IAM Policies for Student Deployment
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "lambda:*",
        "apigateway:*",
        "opensearch:*",
        "bedrock:InvokeModel",
        "dynamodb:*",
        "cloudformation:*",
        "iam:PassRole",
        "logs:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "rds:CreateDBInstance",
        "elasticache:CreateCacheCluster"
      ],
      "Resource": "*"
    }
  ]
}
```

### Enable CloudTrail (Optional for Students)
```bash
# Create CloudTrail for basic auditing
aws cloudtrail create-trail \
  --name rag-assistant-trail \
  --s3-bucket-name your-cloudtrail-bucket
```

---

## 🧪 Pre-Deployment Testing

### Verify Service Quotas
```bash
# Check Lambda concurrency limits
aws service-quotas get-service-quota \
  --service-code lambda \
  --quota-code L-B99A9384 \
  --region us-east-1

# Check OpenSearch domain limits
aws service-quotas get-service-quota \
  --service-code opensearch \
  --quota-code L-6408CAAB \
  --region us-east-1
```

### Test Bedrock Access
```bash
# Test Claude 3 Haiku access (cheapest model)
aws bedrock invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"max_tokens":10,"messages":[{"role":"user","content":"Hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  output.json
```

---

## ⚠️ Common First-Time Issues

### Issue 1: Bedrock Model Access
**Problem**: "You don't have access to the model"
**Solution**: 
```bash
# Request model access in Bedrock console
aws bedrock list-foundation-models --region us-east-1
# Go to AWS Console > Bedrock > Model Access > Request Access
```

### Issue 2: Service Quota Limits
**Problem**: "Service quota exceeded"
**Solution**:
```bash
# Request quota increase
aws service-quotas request-service-quota-increase \
  --service-code lambda \
  --quota-code L-B99A9384 \
  --desired-value 1000
```

### Issue 3: CloudFormation Permissions
**Problem**: "Insufficient privileges"
**Solution**: Ensure IAM user has `CloudFormationFullAccess` policy

---

## 🚀 Ready for Deployment?

### Pre-Flight Checklist
- [ ] AWS CLI configured and tested
- [ ] Student credits activated
- [ ] Billing alerts set up
- [ ] Region selected (us-east-1 recommended)
- [ ] Required services accessible
- [ ] IAM permissions configured

### Next Steps
1. **Run Quick Deploy**: `./scripts/deploy-student-stack.sh`
2. **Monitor Costs**: Check billing daily for first week
3. **Test Functionality**: Upload a PDF and ask questions
4. **Optimize**: Review usage patterns and costs

---

## 📚 Additional Resources

- [AWS Student Portal](https://aws.amazon.com/education/awseducate/)
- [AWS Pricing Calculator](https://calculator.aws/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [OpenSearch Serverless Pricing](https://aws.amazon.com/opensearch-service/pricing/)
- [AWS Support](https://aws.amazon.com/support/) (basic tier included)

**Ready to deploy your first AWS RAG Assistant? You've got this! 🚀**