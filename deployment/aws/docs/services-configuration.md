# 🛠️ AWS Services Configuration Guide
*Detailed configuration for each AWS service used in the RAG Assistant*

---

## 🗂️ Service Overview

The RAG Assistant uses a **serverless-first architecture** to minimize costs:

| Service | Purpose | Estimated Monthly Cost |
|---------|---------|----------------------|
| **Lambda** | Query processing, document ingestion | $5-15 |
| **S3** | Document storage + web hosting | $1-5 |
| **OpenSearch Serverless** | Vector search and retrieval | $10-25 |
| **DynamoDB** | Response caching | $1-3 |
| **API Gateway** | REST API endpoints | $3-5 |
| **Bedrock** | LLM inference (Claude 3 Haiku) | $2-8 |
| **CloudFront** | Global CDN (optional) | $1-2 |

**Total**: $15-50/month (with student credits)

---

## 🔍 OpenSearch Serverless Configuration

### Collection Setup
```json
{
  "name": "rag-assistant-collection",
  "type": "search",
  "description": "Vector search for RAG Assistant documents"
}
```

### Index Configuration
```bash
# Create vector index for embeddings
curl -X PUT "https://your-collection-endpoint.us-east-1.aoss.amazonaws.com/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "mappings": {
      "properties": {
        "content": {"type": "text"},
        "embedding": {
          "type": "dense_vector",
          "dims": 384,
          "index": true,
          "similarity": "cosine"
        },
        "metadata": {
          "properties": {
            "source": {"type": "keyword"},
            "chunk_id": {"type": "keyword"},
            "timestamp": {"type": "date"}
          }
        }
      }
    },
    "settings": {
      "index": {
        "number_of_shards": 1,
        "number_of_replicas": 0
      }
    }
  }'
```

### Access Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:role/RAGLambdaExecutionRole"
      },
      "Action": "aoss:*",
      "Resource": "collection/rag-assistant-collection"
    }
  ]
}
```

---

## ⚡ AWS Lambda Configuration

### Function Settings

**Query Processor Function**:
```yaml
Runtime: python3.11
Memory: 1024 MB (optimized for embeddings)
Timeout: 5 minutes
Architecture: x86_64 (cheapest)

Environment Variables:
  OPENSEARCH_ENDPOINT: your-collection-endpoint.us-east-1.aoss.amazonaws.com
  CACHE_TABLE_NAME: rag-cache-table
  BEDROCK_MODEL_ID: anthropic.claude-3-haiku-20240307-v1:0
  EMBEDDING_MODEL: sentence-transformers/all-MiniLM-L6-v2
```

**Document Processor Function**:
```yaml
Runtime: python3.11
Memory: 2048 MB (for PDF processing)
Timeout: 15 minutes
Architecture: x86_64

Environment Variables:
  DOCUMENT_BUCKET: rag-documents-bucket
  OPENSEARCH_ENDPOINT: your-collection-endpoint.us-east-1.aoss.amazonaws.com
```

### Performance Optimization
```python
# Lambda optimization techniques
import json
import boto3
from functools import lru_cache

# Connection reuse (crucial for cost)
@lru_cache(maxsize=1)
def get_opensearch_client():
    """Reuse OpenSearch client across Lambda invocations"""
    return boto3.client('opensearchserverless')

@lru_cache(maxsize=1)
def get_bedrock_client():
    """Reuse Bedrock client across Lambda invocations"""
    return boto3.client('bedrock-runtime', region_name='us-east-1')

# Warm-up keep connections alive
def lambda_handler(event, context):
    # Pre-warm clients
    opensearch = get_opensearch_client()
    bedrock = get_bedrock_client()
    
    # Your function logic here
    pass
```

---

## 🎯 Amazon Bedrock Configuration

### Model Selection Strategy
```python
# Cost-optimized model routing
def select_bedrock_model(query_complexity: str) -> str:
    """Select most cost-effective model based on query complexity"""
    
    models = {
        'simple': 'anthropic.claude-3-haiku-20240307-v1:0',     # $0.25/1M tokens
        'complex': 'anthropic.claude-3-sonnet-20240229-v1:0',   # $3.00/1M tokens
        'bulk': 'amazon.titan-text-express-v1'                  # $0.13/1M tokens
    }
    
    # Simple heuristics for model selection
    if len(query_complexity.split()) < 10:
        return models['simple']  # Use cheapest for simple queries
    elif 'analysis' in query_complexity.lower():
        return models['complex']  # Use advanced for analysis
    else:
        return models['simple']   # Default to cheapest
```

### Request Optimization
```python
# Optimize token usage for cost control
def optimize_bedrock_request(prompt: str) -> dict:
    """Optimize Bedrock request for minimal cost"""
    
    return {
        'modelId': 'anthropic.claude-3-haiku-20240307-v1:0',
        'body': json.dumps({
            'max_tokens': 500,        # Limit response length
            'temperature': 0.1,       # Reduce randomness for consistency
            'top_p': 0.9,
            'stop_sequences': ['\n\n'], # Stop at natural breaks
            'messages': [{
                'role': 'user',
                'content': prompt[:4000]  # Truncate input if too long
            }]
        })
    }
```

---

## 🗄️ DynamoDB Caching Strategy

### Table Configuration
```yaml
Table Name: rag-response-cache
Partition Key: query_hash (String)
Billing Mode: On-Demand (pay-per-request)
TTL Attribute: ttl (expires after 1 hour)

Global Secondary Indexes:
  - timestamp-index:
      Partition Key: timestamp (String)
      Sort Key: query_hash (String)
```

### Caching Logic
```python
import hashlib
import time
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('rag-response-cache')

def get_cache_key(query: str, context_hash: str = '') -> str:
    """Generate consistent cache key"""
    content = f"{query.lower().strip()}:{context_hash}"
    return hashlib.md5(content.encode()).hexdigest()

def cache_response(query: str, response: str, ttl_hours: int = 1):
    """Cache response with TTL"""
    cache_key = get_cache_key(query)
    
    table.put_item(
        Item={
            'query_hash': cache_key,
            'response': response,
            'timestamp': str(int(time.time())),
            'ttl': int(time.time()) + (ttl_hours * 3600)
        }
    )

def get_cached_response(query: str) -> str:
    """Retrieve cached response if available"""
    cache_key = get_cache_key(query)
    
    try:
        response = table.get_item(Key={'query_hash': cache_key})
        return response.get('Item', {}).get('response')
    except:
        return None
```

---

## 🌐 API Gateway Configuration

### REST API Setup
```yaml
API Name: rag-assistant-api
Protocol: REST
Endpoint Type: Regional (cheapest)

Resources:
  /query:
    POST: Query processing endpoint
  /upload:
    POST: Document upload endpoint
  /health:
    GET: Health check endpoint

CORS Configuration:
  Allow-Origin: "*"
  Allow-Methods: "GET,POST,OPTIONS"
  Allow-Headers: "Content-Type,Authorization"
```

### Request/Response Models
```json
{
  "QueryRequest": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "maxLength": 1000},
      "context": {"type": "string", "maxLength": 5000},
      "max_results": {"type": "integer", "minimum": 1, "maximum": 10}
    },
    "required": ["query"]
  },
  
  "QueryResponse": {
    "type": "object",
    "properties": {
      "response": {"type": "string"},
      "sources": {"type": "array"},
      "cached": {"type": "boolean"},
      "processing_time": {"type": "number"}
    }
  }
}
```

---

## 📦 S3 Storage Configuration

### Bucket Setup
```yaml
Document Storage Bucket:
  Name: rag-documents-{account-id}
  Region: us-east-1
  Versioning: Enabled
  
  Lifecycle Rules:
    - Move to IA after 30 days
    - Move to Glacier after 90 days
    - Delete after 2 years

Web Hosting Bucket:
  Name: rag-web-{account-id}
  Region: us-east-1
  Static Website: Enabled
  Public Read: Enabled (for web assets only)
```

### Cost Optimization
```python
# S3 intelligent tiering for cost optimization
def setup_s3_lifecycle():
    """Configure S3 lifecycle for automatic cost optimization"""
    
    lifecycle_config = {
        'Rules': [
            {
                'ID': 'DocumentArchiving',
                'Status': 'Enabled',
                'Transitions': [
                    {
                        'Days': 30,
                        'StorageClass': 'STANDARD_IA'
                    },
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    }
                ],
                'Expiration': {
                    'Days': 730  # Delete after 2 years
                }
            }
        ]
    }
    
    s3_client.put_bucket_lifecycle_configuration(
        Bucket='rag-documents-bucket',
        LifecycleConfiguration=lifecycle_config
    )
```

---

## 📊 CloudWatch Monitoring

### Essential Metrics
```yaml
Lambda Metrics:
  - Duration (average, max)
  - Invocations (count)
  - Errors (count)
  - Throttles (count)
  - Concurrent Executions

API Gateway Metrics:
  - Count (requests)
  - Latency (p50, p95)
  - 4XXError, 5XXError
  - CacheHitCount, CacheMissCount

Bedrock Metrics:
  - InvocationCount
  - InvocationLatency
  - TokenUsage (for cost tracking)
```

### Custom Dashboard
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", "FunctionName", "rag-query-processor"],
          ["AWS/Lambda", "Invocations", "FunctionName", "rag-query-processor"],
          ["AWS/ApiGateway", "Count", "ApiName", "rag-assistant-api"],
          ["AWS/Bedrock", "InvocationCount", "ModelId", "anthropic.claude-3-haiku-20240307-v1:0"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "RAG Assistant Performance"
      }
    }
  ]
}
```

---

## 🔧 Environment-Specific Configurations

### Development Environment
```yaml
Resource Naming: rag-{service}-dev
Lambda Memory: 512 MB (minimal for testing)
OpenSearch: Single node
S3: No lifecycle rules
Monitoring: Basic CloudWatch only
```

### Production Environment
```yaml
Resource Naming: rag-{service}-prod
Lambda Memory: 1024+ MB (optimized)
OpenSearch: Multi-AZ if needed
S3: Full lifecycle management
Monitoring: Comprehensive dashboards + alarms
```

---

## ⚠️ Service-Specific Gotchas

### OpenSearch Serverless
- **Cold Start**: First query may take 10-30 seconds
- **Billing**: Charged for compute units even when idle
- **Limits**: 5 collections per account initially

### Lambda
- **Cold Start**: 1-5 second delay for new containers
- **Memory**: More memory = faster execution + higher cost
- **Timeout**: Set appropriate timeouts to avoid charges

### Bedrock
- **Model Access**: Must request access to each model
- **Token Limits**: 200K tokens per minute per model
- **Regional**: Model availability varies by region

---

## 📈 Scaling Considerations

### Traffic Growth Thresholds
```yaml
Light Traffic (< 1K requests/day):
  - Current serverless setup sufficient
  - Monitor costs weekly

Medium Traffic (1K-10K requests/day):
  - Add CloudFront for global distribution
  - Implement API rate limiting
  - Consider provisioned Lambda concurrency

High Traffic (> 10K requests/day):
  - Evaluate ECS Fargate for processing
  - Multi-region deployment
  - Advanced caching strategies
```

This configuration guide covers all the AWS services in detail. Ready to configure your first cloud deployment! 🚀