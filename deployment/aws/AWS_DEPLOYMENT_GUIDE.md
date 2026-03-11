# AWS Deployment Guide
**Complete Guide for Deploying AI RAG Assistant to AWS**

*Three cost-optimized deployment modes for students, portfolio projects, and production use*

---

## Table of Contents
1. [Deployment Modes Overview](#deployment-modes-overview)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Ultra-Budget Deployment ($8-18/month)](#ultra-budget-deployment-8-18month)
4. [Balanced Deployment ($15-35/month)](#balanced-deployment-15-35month)
5. [Full Production Deployment ($25-68/month)](#full-production-deployment-25-68month)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Cost Optimization Tips](#cost-optimization-tips)

---

## Deployment Modes Overview

### Ultra-Budget Mode ($8-18/month)
**Perfect for:** Students, learning, demos, portfolio projects

**Key Features:**
- SQLite vector storage (no external DB costs)
- Lambda Function URLs (no API Gateway costs)
- 24-hour aggressive caching (80% cost reduction)
- Automatic document cleanup after 7 days
- Deploy with: `./scripts/deploy-student-stack.sh --mode=ultra-budget`

**Services Used:**
- **Lambda**: Query processing + embedded vector search
- **S3**: Document storage with lifecycle policies
- **SQLite**: Vector storage (bundled with Lambda)
- **DynamoDB**: Response caching with TTL
- **Function URLs**: Direct HTTPS endpoints
- **Bedrock Claude Haiku**: Cost-effective LLM inference

### Balanced Mode ($15-35/month)
**Perfect for:** Small production apps, internship projects, portfolio showcases

**Key Features:**
- External vector database (Pinecone/Chroma)
- API Gateway + Lambda architecture
- Smart caching strategy
- Better performance and scalability

### Full Production Mode ($25-68/month)
**Perfect for:** Production applications, showcasing to employers

**Key Features:**
- OpenSearch Serverless for full hybrid search
- CloudFront CDN
- Advanced monitoring and analytics
- High availability and disaster recovery

---

## Prerequisites & Setup

### AWS Account Preparation

1. **Create AWS Account**
   ```bash
   # Sign up at aws.amazon.com
   # Verify email and phone number
   # Set up billing information
   ```

2. **AWS CLI Installation** (macOS)
   ```bash
   brew install awscli
   aws configure
   # Enter AWS Access Key ID and Secret Access Key
   # Default region: us-east-1 (lowest costs)
   # Default output format: json
   ```

3. **Student Credits** (Recommended)
   ```bash
   # Apply for AWS Educate or AWS Academy
   # $100+ free credits for students
   # Significantly extends free tier usage
   ```

4. **Billing Alerts Setup** (Critical)
   ```bash
   # Create billing alert at 80% of budget
   aws budgets create-budget \
     --account-id $(aws sts get-caller-identity --query Account --output text) \
     --budget '{
       "BudgetName": "RAG-Assistant-Budget",
       "BudgetLimit": {"Amount": "20", "Unit": "USD"},
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

### IAM Permissions Setup

Create IAM user with necessary permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "s3:*",
        "dynamodb:*",
        "cloudformation:*",
        "iam:*",
        "logs:*",
        "bedrock:*"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Ultra-Budget Deployment ($8-18/month)

### Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   Lambda    │───▶│  SQLite     │
│  Request    │    │  Function   │    │  Vector DB  │
└─────────────┘    │  (with URL) │    │ (in /tmp)   │
                   └─────────────┘    └─────────────┘
                          │                    
                          ▼                    
                   ┌─────────────┐    ┌─────────────┐
                   │  DynamoDB   │    │     S3      │
                   │   Cache     │    │ Documents   │
                   └─────────────┘    └─────────────┘
```

### Step 1: Deploy Infrastructure

```bash
# Navigate to project directory
cd /path/to/ai_rag_assistant

# Deploy ultra-budget stack
./scripts/deploy-student-stack.sh \
  --mode=ultra-budget \
  --budget=20 \
  --region=us-east-1

# Deployment typically takes 20-30 minutes
```

### Step 2: Lambda Function Configuration

**Memory and Timeout Settings:**
```bash
# Optimize for cost and performance
aws lambda update-function-configuration \
  --function-name rag-assistant-ultra-query \
  --memory-size 1024 \
  --timeout 30
```

**Environment Variables:**
```bash
# Set environment variables for Lambda
aws lambda update-function-configuration \
  --function-name rag-assistant-ultra-query \
  --environment Variables='{
    "CACHE_TTL": "86400",
    "VECTOR_DIMENSIONS": "384",
    "MAX_DOCUMENT_SIZE": "10MB",
    "SQLITE_PATH": "/tmp/vectors.db"
  }'
```

### Step 3: S3 Bucket Configuration

```bash
# Create S3 bucket with lifecycle policy
aws s3api create-bucket \
  --bucket rag-ultra-documents-$(date +%s) \
  --region us-east-1

# Set lifecycle policy (auto-delete after 7 days)
aws s3api put-bucket-lifecycle-configuration \
  --bucket your-bucket-name \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "DeleteOldDocuments",
      "Status": "Enabled",
      "Expiration": {"Days": 7}
    }]
  }'
```

### Step 4: DynamoDB Caching Setup

```bash
# Create DynamoDB table with TTL
aws dynamodb create-table \
  --table-name rag-response-cache \
  --attribute-definitions \
    AttributeName=query_hash,AttributeType=S \
  --key-schema \
    AttributeName=query_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Enable TTL for automatic cleanup
aws dynamodb update-time-to-live \
  --table-name rag-response-cache \
  --time-to-live-specification \
    AttributeName=expiry,Enabled=true
```

### Step 5: Function URL Configuration

```bash
# Create Function URL for direct access
aws lambda create-function-url-config \
  --function-name rag-assistant-ultra-query \
  --config AuthType=NONE,Cors='{
    "AllowCredentials": false,
    "AllowHeaders": ["content-type"],
    "AllowMethods": ["POST", "GET"],
    "AllowOrigins": ["*"],
    "MaxAge": 86400
  }'
```

---

## Balanced Deployment ($15-35/month)

### Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│ API Gateway │───▶│   Lambda    │
│  Request    │    │             │    │  Function   │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────┐           ▼
                   │  DynamoDB   │    ┌─────────────┐
                   │   Cache     │    │  Pinecone   │
                   └─────────────┘    │ Vector DB   │
                                      └─────────────┘
```

### Step 1: External Vector Database Setup

**Option A: Pinecone Setup**
```bash
# Sign up for Pinecone free tier (100k vectors free)
# Create index with 384 dimensions
curl -X POST "https://api.pinecone.io/indexes" \
  -H "Api-Key: $PINECONE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rag-assistant",
    "dimension": 384,
    "metric": "cosine",
    "pods": 1,
    "pod_type": "p1.x1"
  }'
```

**Option B: Chroma Setup**
```bash
# Deploy Chroma using Docker
docker run -p 8000:8000 chromadb/chroma:latest
```

### Step 2: Deploy Balanced Stack

```bash
./scripts/deploy-student-stack.sh \
  --mode=balanced \
  --budget=35 \
  --vector-db=pinecone \
  --pinecone-api-key=$PINECONE_API_KEY
```

---

## Full Production Deployment ($25-68/month)

### Architecture Overview

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  CloudFront │───▶│ API Gateway │───▶│   Lambda    │
│     CDN     │    │             │    │  Function   │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                   ┌─────────────┐           ▼
                   │ CloudWatch  │    ┌─────────────┐
                   │ Monitoring  │    │ OpenSearch  │
                   └─────────────┘    │ Serverless  │
                                      └─────────────┘
```

### Step 1: OpenSearch Serverless Setup

```bash
# Create OpenSearch Serverless collection
aws opensearchserverless create-collection \
  --name rag-assistant \
  --type search \
  --description "RAG Assistant vector search"
```

### Step 2: CloudFront CDN Setup

```bash
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "rag-assistant-cdn",
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "api-gateway",
        "DomainName": "your-api-gateway-domain.execute-api.us-east-1.amazonaws.com",
        "CustomOriginConfig": {
          "HTTPPort": 443,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only"
        }
      }]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "api-gateway",
      "ViewerProtocolPolicy": "redirect-to-https"
    }
  }'
```

---

## Post-Deployment Configuration

### SSL/TLS Certificate Setup

```bash
# Request SSL certificate (free with AWS)
aws acm request-certificate \
  --domain-name your-domain.com \
  --validation-method DNS \
  --region us-east-1
```

### Custom Domain Configuration

```bash
# Create custom domain for API Gateway
aws apigateway create-domain-name \
  --domain-name api.your-domain.com \
  --certificate-arn arn:aws:acm:us-east-1:account:certificate/cert-id
```

### Environment-Specific Configurations

**Development:**
```bash
./scripts/deploy-student-stack.sh --mode=ultra-budget --env=dev
```

**Production:**
```bash
./scripts/deploy-student-stack.sh --mode=full --env=prod
```

---

## Monitoring & Maintenance

### CloudWatch Dashboards

```bash
# Create monitoring dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "RAG-Assistant-Metrics" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Lambda", "Duration", "FunctionName", "rag-assistant-query"],
            ["AWS/Lambda", "Errors", "FunctionName", "rag-assistant-query"],
            ["AWS/Lambda", "Invocations", "FunctionName", "rag-assistant-query"]
          ],
          "period": 300,
          "stat": "Average",
          "region": "us-east-1",
          "title": "Lambda Performance"
        }
      }
    ]
  }'
```

### Cost Monitoring

```bash
# Check daily costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "7 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

### Health Checks

```bash
# Test deployment health
curl -X POST https://your-function-url.lambda-url.us-east-1.on.aws/health

# Expected response:
# {"status": "healthy", "version": "1.0", "timestamp": "2026-03-11T12:00:00Z"}
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Lambda Function Timeout

**Symptoms:**
- Queries timing out after 30 seconds
- 502 Bad Gateway errors

**Solutions:**
```bash
# Increase timeout (max 15 minutes)
aws lambda update-function-configuration \
  --function-name rag-assistant-query \
  --timeout 300

# Optimize embedding batch size
# In lambda code: reduce BATCH_SIZE from 10 to 5
```

#### 2. Out of Memory Errors

**Symptoms:**
- Lambda function fails with memory errors
- Large document processing fails

**Solutions:**
```bash
# Increase memory allocation
aws lambda update-function-configuration \
  --function-name rag-assistant-query \
  --memory-size 2048

# Optimize document chunking
# Reduce MAX_CHUNK_SIZE in configuration
```

#### 3. High Costs

**Symptoms:**
- Monthly costs exceeding budget
- Unexpected charges

**Solutions:**
```bash
# Check cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "1 month ago" +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Common culprits and fixes:
# 1. Bedrock usage: Implement aggressive caching
# 2. Lambda invocations: Optimize caching strategy  
# 3. S3 storage: Enable lifecycle policies
```

#### 4. Vector Search Performance Issues

**Symptoms:**
- Slow query responses (>5 seconds)
- Poor retrieval relevance

**Solutions:**
```bash
# SQLite optimization (Ultra-Budget mode)
# Reduce embedding dimensions
# Implement index optimization

# External DB optimization (Balanced/Full mode)
# Check vector database metrics
# Optimize index configuration
```

#### 5. Document Upload Failures

**Symptoms:**
- PDF processing errors
- S3 upload timeouts

**Solutions:**
```bash
# Check S3 permissions
aws s3api get-bucket-policy --bucket your-bucket-name

# Optimize file size limits
# Implement chunked upload for large files
# Add retry logic for network issues
```

### Debugging Commands

```bash
# View Lambda logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/rag-assistant-query \
  --start-time $(date -d "1 hour ago" +%s)000

# Check DynamoDB performance
aws dynamodb describe-table \
  --table-name rag-response-cache

# Monitor S3 costs
aws s3api get-bucket-metrics-configuration \
  --bucket your-bucket-name
```

---

## Cost Optimization Tips

### Ultra-Budget Mode Optimizations

1. **Aggressive Caching**
   ```bash
   # 24-hour cache TTL (vs 1-hour default)
   export CACHE_TTL=86400
   ```

2. **Document Lifecycle**
   ```bash
   # Auto-delete documents after 7 days
   aws s3api put-bucket-lifecycle-configuration \
     --bucket your-bucket \
     --lifecycle-configuration file://lifecycle.json
   ```

3. **Lambda Optimization**
   ```bash
   # Right-size memory for your workload
   # Monitor and adjust based on CloudWatch metrics
   ```

### General Cost Optimization

1. **Use AWS Free Tier**
   - Lambda: 1M requests/month free
   - S3: 5GB storage free
   - DynamoDB: 25GB storage free

2. **Regional Selection**
   - Use us-east-1 (cheapest region)
   - Keep all resources in same region

3. **Resource Cleanup**
   ```bash
   # Automated cleanup script
   ./scripts/cleanup-unused-resources.sh
   ```

4. **Monitoring and Alerts**
   - Set billing alerts at 50% and 80% of budget
   - Monitor daily costs
   - Use AWS Cost Explorer

### Emergency Cost Controls

```bash
# Emergency shutdown (if costs spike)
./scripts/emergency-shutdown.sh

# Temporarily disable services
aws lambda put-provisioned-concurrency-config \
  --function-name rag-assistant-query \
  --qualifier '$LATEST' \
  --provisioned-concurrency-config ProvisionedConcurrencyCount=0
```

---

## Security Best Practices

### IAM Policies

Use least-privilege access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:region:account:table/rag-response-cache"
    }
  ]
}
```

### API Security

```bash
# Add API throttling
aws apigateway create-usage-plan \
  --name "rag-assistant-throttling" \
  --throttle burstLimit=10,rateLimit=5
```

### Data Encryption

```bash
# Enable S3 encryption at rest
aws s3api put-bucket-encryption \
  --bucket your-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

---

## Next Steps

After successful deployment:

1. **Test Full Functionality**
   ```bash
   # Run comprehensive tests
   python scripts/smoke_test.py --deployment-url https://your-url
   ```

2. **Set Up Monitoring**
   - Configure CloudWatch alarms
   - Set up cost monitoring
   - Enable AWS Config for compliance

3. **Optimize Performance**
   - Monitor metrics for 1 week
   - Adjust memory/timeout based on usage
   - Fine-tune caching strategy

4. **Document for Portfolio**
   - Create architecture diagrams
   - Document cost optimization decisions
   - Prepare demo scripts for interviews

5. **Plan Scaling Strategy**
   - Define metrics for mode upgrades
   - Plan migration path (Ultra → Balanced → Full)
   - Document upgrade procedures

---

**Deployment Support:**
- For deployment issues: Check troubleshooting section above
- For cost concerns: Review cost optimization tips
- For performance optimization: Monitor CloudWatch metrics

**Remember:** Start with Ultra-Budget mode for learning and portfolio value, then scale up based on needs and budget availability.