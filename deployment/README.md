# 🚀 AWS Deployment Guide
*Quick reference for deploying Quest Analytics RAG Assistant to AWS*

---

## 📋 Overview

This guide provides **streamlined deployment instructions** for the Quest Analytics RAG Assistant on AWS. For comprehensive strategy, architecture details, and cost optimization, see the [AWS Deployment Roadmap](aws/AWS_DEPLOYMENT_ROADMAP.md).

📚 **Additional AWS Documentation:**
- [Infrastructure Setup](aws/docs/infrastructure-setup.md) - AWS account preparation
- [Services Configuration](aws/docs/services-configuration.md) - Detailed service configs
- [Troubleshooting Guide](aws/docs/troubleshooting.md) - Common issues & solutions

---

## ⚡ Quick Deploy (Student-Optimized)

### Prerequisites
- AWS account with student credits (recommended)
- AWS CLI configured (`aws configure`)
- Docker installed locally
- 30 minutes deployment time

### One-Click Deployment
```bash
# Navigate to project root
cd AI_RAG

# Run student-optimized deployment
./scripts/deploy-student-stack.sh
```

**Estimated Cost**: $15-50/month with student credits

---

## 🛠️ Manual Deployment Steps

### 1. Prepare Environment
```bash
# Set deployment variables
export STACK_NAME="rag-assistant-student"
export AWS_REGION="us-east-1"
export ENVIRONMENT="dev"
```

### 2. Deploy Infrastructure
```bash
# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file infrastructure/student-stack.yml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --region $AWS_REGION
```

### 3. Update Lambda Functions
```bash
# Package and deploy Lambda functions
cd lambda-functions/query-processor
pip install -r requirements.txt -t ./
zip -r ../../query-processor.zip .

# Update function code
aws lambda update-function-code \
  --function-name ${STACK_NAME}-query-processor \
  --zip-file fileb://../../query-processor.zip
```

### 4. Deploy Web Interface
```bash
# Upload static web assets to S3
aws s3 sync static-web/ s3://your-web-bucket/
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Core settings for Lambda functions
OPENSEARCH_ENDPOINT=your-opensearch-endpoint
CACHE_TABLE=your-dynamodb-table
DOCUMENT_BUCKET=your-s3-bucket
```

### AWS Services Used
- **Lambda**: Serverless compute for RAG processing
- **API Gateway**: REST API endpoints
- **S3**: Document storage + web hosting
- **OpenSearch Serverless**: Vector search
- **DynamoDB**: Response caching
- **CloudFront**: Global CDN (optional)

---

## 📊 Monitoring & Costs

### Cost Monitoring
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### Performance Monitoring
- **CloudWatch**: Lambda metrics and logs
- **X-Ray**: Request tracing (optional)
- **Budgets**: Cost alerts

---

## 🛡️ Security Configuration

### IAM Policies
- Lambda execution role with minimal permissions
- S3 bucket policies for secure access
- OpenSearch access policies

### Secrets Management
- Store sensitive config in AWS Systems Manager
- Use environment variables for Lambda functions
- Enable encryption at rest

---

## 🚀 Scaling Options

### Traffic Growth
- **Low traffic**: Current serverless setup
- **Medium traffic**: Add CloudFront + WAF
- **High traffic**: Consider ECS Fargate

### Cost Optimization
- Use Bedrock Claude 3 Haiku for cost efficiency
- Implement intelligent caching strategies
- Set up automated resource cleanup

---

## 🔄 CI/CD Pipeline

### GitHub Actions Setup
```yaml
name: Deploy RAG Assistant
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to AWS
        run: ./scripts/deploy-student-stack.sh
```

---

## 🆘 Troubleshooting

### Common Issues

**Lambda cold starts too slow**
- Increase memory allocation to 1024MB
- Consider provisioned concurrency for production

**OpenSearch timeout**
- Check security groups and VPC settings
- Verify IAM permissions

**High costs**
- Review CloudWatch logs for unused resources
- Optimize Lambda memory/timeout settings
- Enable response caching

### Debug Commands
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name $STACK_NAME

# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/

# Test API endpoints
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/dev/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'
```

---

## 📚 Additional Resources

- [AWS Deployment Roadmap](../docs/AWS_DEPLOYMENT_ROADMAP.md) - Complete strategy
- [System Design](../docs/system_design.md) - Architecture details
- [Operations Runbook](../docs/ops_runbook.md) - Day-to-day operations
- [AWS Student Resources](https://aws.amazon.com/education/awseducate/)

---

## 🎯 Next Steps

1. **Deploy**: Run the one-click deployment script
2. **Test**: Upload a PDF and ask questions
3. **Monitor**: Set up billing alerts
4. **Optimize**: Review costs after first week
5. **Scale**: Plan for growth using roadmap

**Ready to showcase your cloud skills? Deploy now and demonstrate your AWS expertise to potential employers! 🚀**