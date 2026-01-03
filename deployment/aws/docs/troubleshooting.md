# 🐛 AWS Deployment Troubleshooting Guide
*Solutions for common issues across all deployment modes (Ultra-Budget, Balanced, Full)*

---

## 🎯 Mode-Specific Troubleshooting

### 💰 Ultra-Budget Mode Issues

#### SQLite Vector Search Problems
```bash
# Check Lambda function logs
aws logs tail /aws/lambda/rag-assistant-ultra-query --follow

# Common issues:
# 1. SQLite database not persisting (expected - uses /tmp)
# 2. Vector search too slow (optimize embedding size)
# 3. Out of memory (reduce batch size)

# Test SQLite functionality locally
python -c "
import sqlite3
conn = sqlite3.connect('/tmp/test.db')
cursor = conn.cursor()
cursor.execute('SELECT sqlite_version()')
print('SQLite version:', cursor.fetchone()[0])
"
```

#### Lambda Function URL Issues
```bash
# Check Function URL configuration
aws lambda get-function-url-config \
  --function-name rag-assistant-ultra-query

# Common CORS issues - verify headers:
curl -H "Origin: http://localhost:7860" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://your-function-url.lambda-url.region.on.aws/
```

### ⚖️ Balanced Mode Issues

#### Pinecone Connection Problems
```bash
# Test Pinecone connectivity
python -c "
import pinecone
import os
pinecone.init(api_key=os.environ['PINECONE_API_KEY'])
print('Pinecone indexes:', pinecone.list_indexes())
"

# Check index stats
python -c "
import pinecone
index = pinecone.Index('rag-assistant')
print('Index stats:', index.describe_index_stats())
"
```

### 🚀 Full Mode Issues  

#### OpenSearch Serverless Problems
```bash
# Check collection status
aws opensearchserverless batch-get-collection \
  --names rag-assistant-collection

# Test connectivity
curl -X GET "https://your-collection-endpoint.us-east-1.aoss.amazonaws.com/_cluster/health" \
     --aws-sigv4 "aws:amz:us-east-1:aoss" \
     --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY"
```

---

## 🚨 Quick Diagnosis Commands

### Universal Health Checks (All Modes)
```bash
# Verify AWS CLI configuration
aws sts get-caller-identity

# Check active region  
aws configure get region

# Verify student credits remaining
aws billing get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Check deployment mode
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=20 --dry-run
```

### Mode-Specific Health Checks
```bash
# Ultra-Budget Mode
aws lambda get-function-url-config --function-name rag-assistant-ultra-query
aws lambda invoke --function-name rag-assistant-ultra-query /tmp/response.json

# Balanced Mode  
aws apigateway get-rest-apis --query 'items[?name==`rag-assistant-balanced`]'
aws lambda get-function --function-name rag-assistant-balanced-query

# Full Mode
aws cloudformation describe-stacks --stack-name rag-assistant-full
aws opensearchserverless batch-get-collection --names rag-assistant-collection
```

---

## 🔴 Critical Deployment Issues

### Issue 1: CloudFormation Stack Fails to Create

**Symptoms**:
```
CREATE_FAILED: User does not have permission to perform: iam:CreateRole
```

**Root Cause**: Insufficient IAM permissions

**Solution**:
```bash
# Option A: Add PowerUser policy (recommended for students)
aws iam attach-user-policy \
  --user-name your-username \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Option B: Add specific permissions
aws iam attach-user-policy \
  --user-name your-username \
  --policy-arn arn:aws:iam::aws:policy/IAMFullAccess

# Option C: Use CloudShell (if policies don't work)
# Go to AWS Console > CloudShell and run deployment from there
```

**Prevention**:
- Always test permissions before deployment
- Use AWS CloudShell for full admin access
- Create dedicated deployment user with required permissions

---

### Issue 2: Bedrock Model Access Denied

**Symptoms**:
```
ValidationException: You don't have access to the model with the specified model ID.
```

**Root Cause**: Model access not requested in Bedrock console

**Solution**:
```bash
# Step 1: Check available models
aws bedrock list-foundation-models --region us-east-1

# Step 2: Go to AWS Console > Bedrock > Model Access
# Step 3: Request access to Claude 3 Haiku
# Step 4: Wait 5-10 minutes for approval

# Step 5: Verify access
aws bedrock invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"max_tokens":10,"messages":[{"role":"user","content":"test"}]}' \
  --cli-binary-format raw-in-base64-out \
  --region us-east-1 \
  test-output.json
```

**Prevention**:
- Request model access before deployment
- Use us-east-1 region (most models available)
- Test model access with simple API call

---

### Issue 3: Lambda Function Timeout

**Symptoms**:
```
Task timed out after 30.00 seconds
```

**Root Cause**: Default timeout too short for document processing

**Solution**:
```bash
# Update timeout to 5 minutes for query processor
aws lambda update-function-configuration \
  --function-name rag-assistant-student-query-processor \
  --timeout 300

# Update timeout to 15 minutes for document processor
aws lambda update-function-configuration \
  --function-name rag-assistant-student-document-processor \
  --timeout 900

# Update memory for better performance
aws lambda update-function-configuration \
  --function-name rag-assistant-student-query-processor \
  --memory-size 1024
```

**Prevention**:
- Set appropriate timeouts in CloudFormation template
- Monitor function duration in CloudWatch
- Increase memory for faster execution

---

## 🟡 Common Service Issues

### OpenSearch Serverless Issues

**Issue**: Collection creation fails
```bash
# Check service quotas
aws service-quotas get-service-quota \
  --service-code opensearch \
  --quota-code L-8A9A1B75 \
  --region us-east-1

# Request quota increase if needed
aws service-quotas request-service-quota-increase \
  --service-code opensearch \
  --quota-code L-8A9A1B75 \
  --desired-value 10
```

**Issue**: Cannot connect to collection
```python
# Debug OpenSearch connection
import boto3
import json

try:
    client = boto3.client('opensearchserverless', region_name='us-east-1')
    response = client.batch_get_collection(names=['rag-assistant-collection'])
    print(json.dumps(response, indent=2, default=str))
except Exception as e:
    print(f"Connection error: {e}")
    
    # Check collection endpoint
    collections = client.list_collections()
    for collection in collections['collectionSummaries']:
        print(f"Collection: {collection['name']} - {collection['status']}")
```

---

### Lambda Function Issues

**Issue**: Cold start latency too high
```python
# Optimization techniques
import json
import boto3
from functools import lru_cache

# Pre-warm connections
@lru_cache(maxsize=1)
def get_clients():
    """Initialize and cache AWS clients"""
    return {
        'opensearch': boto3.client('opensearchserverless'),
        'bedrock': boto3.client('bedrock-runtime'),
        'dynamodb': boto3.resource('dynamodb')
    }

def lambda_handler(event, context):
    # Get pre-warmed clients
    clients = get_clients()
    
    # Your function logic here
    pass
```

**Issue**: Out of memory errors
```bash
# Check current memory allocation
aws lambda get-function-configuration \
  --function-name rag-assistant-student-query-processor \
  --query 'MemorySize'

# Increase memory (also increases CPU)
aws lambda update-function-configuration \
  --function-name rag-assistant-student-query-processor \
  --memory-size 2048
```

---

### S3 Bucket Issues

**Issue**: Bucket name already exists
```bash
# S3 bucket names must be globally unique
# Solution: Use account ID in bucket name
aws sts get-caller-identity --query Account --output text

# Create bucket with unique name
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 mb s3://rag-documents-${ACCOUNT_ID} --region us-east-1
```

**Issue**: CORS errors from web interface
```json
// Add CORS configuration to S3 bucket
{
  "CORSRules": [
    {
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "AllowedOrigins": ["*"],
      "ExposeHeaders": ["ETag"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

---

## 💸 Cost-Related Issues

### Issue: Unexpected High Bills

**Immediate Actions**:
```bash
# Check current month costs
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Check hourly costs for today
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-%d),End=$(date -d "+1 day" +%Y-%m-%d) \
  --granularity HOURLY \
  --metrics BlendedCost
```

**Cost Optimization Actions**:
```bash
# Stop expensive services immediately
aws opensearchserverless delete-collection --id collection-id

# Delete unused Lambda functions
aws lambda delete-function --function-name unused-function

# Empty and delete S3 buckets
aws s3 rm s3://bucket-name --recursive
aws s3 rb s3://bucket-name
```

### Issue: OpenSearch Serverless High Costs

**Problem**: OpenSearch Serverless charges for compute units even when idle

**Solutions**:
```bash
# Option 1: Use OpenSearch managed service with t3.small
# (Often cheaper for low-traffic applications)

# Option 2: Implement smart collection management
# Delete collection when not in use, recreate when needed

# Option 3: Use alternative vector stores
# Consider Pinecone free tier or local SQLite with embeddings
```

---

## 🔧 Performance Issues

### Issue: Slow Query Response Times

**Diagnosis**:
```bash
# Check Lambda execution times
aws logs filter-log-events \
  --log-group-name /aws/lambda/rag-assistant-student-query-processor \
  --filter-pattern "REPORT RequestId" \
  --start-time $(date -d "1 hour ago" +%s)000

# Check API Gateway latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Latency \
  --dimensions Name=ApiName,Value=rag-assistant-api \
  --start-time $(date -d "1 hour ago" --iso-8601) \
  --end-time $(date --iso-8601) \
  --period 300 \
  --statistics Average,Maximum
```

**Optimization**:
```python
# Implement response caching
import redis
import json

# Use ElastiCache Redis for fast caching
redis_client = redis.Redis(host='your-elasticache-endpoint')

def get_cached_response(query_hash):
    cached = redis_client.get(f"query:{query_hash}")
    return json.loads(cached) if cached else None

def cache_response(query_hash, response):
    redis_client.setex(f"query:{query_hash}", 3600, json.dumps(response))
```

---

## 🛡️ Security Issues

### Issue: API Gateway Open to Internet

**Problem**: No authentication on API endpoints

**Solution**:
```yaml
# Add API key authentication
ApiKey:
  Type: AWS::ApiGateway::ApiKey
  Properties:
    Name: rag-assistant-api-key
    Description: API key for RAG assistant
    Enabled: true

UsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    UsagePlanName: rag-assistant-usage-plan
    Throttle:
      RateLimit: 100
      BurstLimit: 200
    Quota:
      Limit: 1000
      Period: DAY
```

### Issue: S3 Buckets Too Permissive

**Problem**: Public read access to document bucket

**Solution**:
```bash
# Remove public access from document bucket
aws s3api put-public-access-block \
  --bucket rag-documents-bucket \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Use pre-signed URLs for document access
```

---

## 📱 Web Interface Issues

### Issue: Static Website Not Loading

**Diagnosis**:
```bash
# Check website endpoint
aws s3api get-bucket-website --bucket rag-web-bucket

# Test direct file access
curl -I https://rag-web-bucket.s3-website-us-east-1.amazonaws.com/index.html
```

**Solution**:
```bash
# Ensure bucket policy allows public read
aws s3api put-bucket-policy --bucket rag-web-bucket --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::rag-web-bucket/*"
    }
  ]
}'
```

---

## 🆘 Emergency Procedures

### Complete Cleanup (if costs get out of hand)
```bash
#!/bin/bash
# emergency-cleanup.sh - Use only if costs are spiraling

echo "🚨 EMERGENCY CLEANUP - This will delete EVERYTHING"
read -p "Are you sure? Type 'DELETE' to continue: " confirm

if [ "$confirm" != "DELETE" ]; then
    echo "Cleanup cancelled"
    exit 1
fi

# Delete CloudFormation stack (removes most resources)
aws cloudformation delete-stack --stack-name rag-assistant-student

# Wait for stack deletion
aws cloudformation wait stack-delete-complete --stack-name rag-assistant-student

# Manual cleanup of any remaining resources
aws s3 rm s3://rag-documents-* --recursive
aws s3 rb s3://rag-documents-*

echo "✅ Emergency cleanup complete"
```

### Rollback to Previous State
```bash
# If deployment fails, rollback CloudFormation
aws cloudformation cancel-update-stack --stack-name rag-assistant-student

# Or rollback to previous version
aws cloudformation continue-update-rollback --stack-name rag-assistant-student
```

---

## 📞 Getting Help

### AWS Support Channels
- **AWS Support**: Basic tier included (technical support for billing/account)
- **AWS Forums**: [https://forums.aws.amazon.com/](https://forums.aws.amazon.com/)
- **AWS Reddit**: [r/aws](https://reddit.com/r/aws)
- **Stack Overflow**: Tag your questions with `[amazon-web-services]`

### Student-Specific Resources
- **AWS Educate Support**: [https://aws.amazon.com/education/awseducate/](https://aws.amazon.com/education/awseducate/)
- **AWS Student Forums**: Access through AWS Educate portal
- **University AWS User Groups**: Check if your school has one

### Debug Information to Collect
When seeking help, include:
```bash
# AWS account info (remove sensitive data)
aws sts get-caller-identity

# CloudFormation events
aws cloudformation describe-stack-events --stack-name rag-assistant-student

# Lambda logs (last hour)
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/rag

# Service quotas
aws service-quotas list-service-quotas --service-code lambda
```

---

**Remember**: Every cloud engineer faces these issues when starting out. The key is systematic debugging and learning from each problem. You've got this! 🚀**