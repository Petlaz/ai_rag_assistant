# 💰 Cost Optimization Guide for Students

## Three-Tier Deployment Architecture

### 🎯 Ultra-Budget Mode ($8-18/month)
**Target**: Learning, demos, low-traffic personal projects

**Components**:
- **Vector Storage**: SQLite (bundled with Lambda)
- **API**: Lambda Function URLs (free tier)
- **LLM**: Amazon Bedrock Claude Haiku ($3/M tokens)
- **Storage**: S3 Standard ($0.023/GB)
- **Caching**: DynamoDB with 24-hour TTL (aggressive caching)

**Optimizations**:
- ✅ No API Gateway costs
- ✅ No OpenSearch Serverless costs
- ✅ SQLite for small-scale vector search
- ✅ Aggressive 24-hour response caching
- ✅ Lambda cold start optimization
- ✅ Automatic document cleanup after 7 days

**Usage Command**:
```bash
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=20
```

### ⚖️ Balanced Mode ($15-35/month)
**Target**: Small production apps, internship projects

**Components**:
- **Vector Storage**: Pinecone Starter ($70/month) or Chroma (self-hosted)
- **API**: API Gateway + Lambda
- **LLM**: Amazon Bedrock Claude Haiku/Sonnet mix
- **Storage**: S3 Intelligent Tiering
- **Caching**: DynamoDB with smart TTL

**Optimizations**:
- ✅ Smart caching (1-6 hour TTL based on query type)
- ✅ Intelligent tiering for storage
- ✅ Connection pooling
- ✅ Batch processing where possible

**Usage Command**:
```bash
./scripts/deploy-student-stack.sh --mode=balanced --budget=40
```

### 🚀 Full Mode ($25-68/month)
**Target**: Production apps, portfolio projects for employers

**Components**:
- **Vector Storage**: OpenSearch Serverless
- **API**: API Gateway with custom domain
- **LLM**: Amazon Bedrock Claude Sonnet
- **Storage**: S3 with CloudFront CDN
- **Caching**: ElastiCache + DynamoDB multi-layer

**Features**:
- ✅ Full hybrid search (keyword + semantic)
- ✅ Real-time analytics
- ✅ Custom domain and SSL
- ✅ Advanced monitoring and logging
- ✅ High availability

**Usage Command**:
```bash
./scripts/deploy-student-stack.sh --mode=full --budget=70
```

## Cost Monitoring & Alerts

### Setting Up Billing Alerts
```bash
# Create billing alert at 80% of budget
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget '{
    "BudgetName": "RAG-Assistant-Budget",
    "BudgetLimit": {
      "Amount": "'$BUDGET_LIMIT'",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "your-email@example.com"
    }]
  }'
```

### Daily Cost Monitoring
```bash
# Check yesterday's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d "yesterday" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

## Student-Specific Optimizations

### 1. AWS Free Tier Maximization
- **Lambda**: 1M free requests/month + 400,000 GB-seconds
- **S3**: 5GB free storage + 20,000 GET requests
- **DynamoDB**: 25GB free storage + 200M requests
- **API Gateway**: 1M free API calls

### 2. Academic Credits
- Apply for **AWS Educate** ($100-200 credits)
- Check if your school has **AWS Academy** access
- Look for **GitHub Student Pack** AWS credits

### 3. Time-Based Cost Control
```bash
# Automatically shutdown non-essential resources at night
aws events put-rule \
  --name "student-night-shutdown" \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED
```

### 4. Resource Cleanup Automation
```bash
# Clean up old documents automatically
aws lambda create-function \
  --function-name cleanup-old-docs \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --code file://cleanup.zip \
  --environment Variables='{DAYS_TO_KEEP=7}'
```

## Emergency Cost Control

### Immediate Shutdown
```bash
# Emergency shutdown script
./scripts/emergency-shutdown.sh
```

### Resource Deletion Order
1. **OpenSearch collections** (highest cost)
2. **API Gateway stages**
3. **Lambda functions** (keep cleanup function)
4. **S3 buckets** (after backup)
5. **DynamoDB tables** (export first)

## Upgrade Path

### From Ultra-Budget → Balanced
```bash
# Seamless upgrade with data migration
./scripts/deploy-student-stack.sh --mode=balanced --migrate-from=ultra-budget
```

### From Balanced → Full
```bash
# Full feature upgrade
./scripts/deploy-student-stack.sh --mode=full --migrate-from=balanced
```

## 📅 Deployment Day Cost Monitoring

### Pre-Deployment Cost Check
```bash
# Verify current month costs are $0 before starting
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost

# Should return very low costs (under $1)
```

### Real-Time Monitoring During Deployment
```bash
# Monitor costs every 5 minutes during deployment
watch -n 300 'aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-%d),End=$(date -d "1 day" +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost'

# Expected progression:
# 0 min: $0.00
# 10 min: $0.01-0.05 (Lambda invocations)
# 20 min: $0.05-0.15 (S3 operations)
# 30 min: $0.10-0.25 (Full stack running)
```

### First Hour Cost Validation
```bash
# Check costs 1 hour after deployment
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Expected first-hour costs:
# Lambda: $0.05-0.10
# S3: $0.01-0.05  
# DynamoDB: $0.00-0.01
# Total: $0.06-0.16
```

## Cost Estimation Calculator

| Component | Ultra-Budget | Balanced | Full |
|-----------|-------------|----------|------|
| Vector DB | $0 (SQLite) | $15 (Pinecone) | $35 (OpenSearch) |
| API | $0 (Function URLs) | $5 (API Gateway) | $10 (API Gateway + CDN) |
| Compute | $3 (Lambda) | $8 (Lambda) | $15 (Lambda + cache) |
| Storage | $2 (S3) | $4 (S3 Intelligent) | $8 (S3 + CloudFront) |
| LLM | $3 (Haiku) | $8 (Mix) | $15 (Sonnet) |
| **Total** | **$8-18/month** | **$15-35/month** | **$25-68/month** |

Remember: These are estimates. Actual costs depend on usage patterns!