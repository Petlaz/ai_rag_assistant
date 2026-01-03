# 🛠️ AWS Services Configuration Guide
*Detailed configuration for each AWS service across all deployment modes*

---

## 🎯 Service Overview by Deployment Mode

### 💰 Ultra-Budget Mode ($8-18/month)
| Service | Purpose | Monthly Cost |
|---------|---------|-------------|
| **Lambda** | Query processing + vector search | $2-5 |
| **S3** | Document storage | $1-3 |
| **SQLite** | Vector storage (bundled with Lambda) | $0 |
| **DynamoDB** | Aggressive response caching | $1-2 |
| **Function URLs** | Direct HTTPS endpoints | $0 |
| **Bedrock Claude Haiku** | LLM inference | $3-8 |
| **Total** | | **$8-18** |

### ⚖️ Balanced Mode ($15-35/month)
| Service | Purpose | Monthly Cost |
|---------|---------|-------------|
| **Lambda** | Query processing | $5-10 |
| **S3** | Document storage + web hosting | $2-5 |
| **Pinecone Starter** | Vector search | $70 (but efficient usage) |
| **DynamoDB** | Smart response caching | $1-3 |
| **API Gateway** | REST API endpoints | $3-5 |
| **Bedrock Claude Mix** | LLM inference | $5-12 |
| **Total** | | **$15-35** |

### 🚀 Full Mode ($25-68/month)
| Service | Purpose | Monthly Cost |
|---------|---------|-------------|
| **Lambda** | Query processing | $8-15 |
| **S3** | Document storage + web hosting | $3-8 |
| **OpenSearch Serverless** | Hybrid vector search | $10-25 |
| **DynamoDB** | Multi-layer caching | $2-5 |
| **API Gateway** | REST API with custom domain | $5-8 |
| **Bedrock Claude Sonnet** | Advanced LLM inference | $8-15 |
| **CloudFront** | Global CDN | $1-2 |
| **Total** | | **$25-68** |

---

## 🔍 Service Configuration by Mode

### 💰 Ultra-Budget Mode Configuration

#### SQLite Vector Storage
```python
# Lambda function with SQLite vector search
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

def create_vector_index():
    conn = sqlite3.connect('/tmp/vectors.db')
    cursor = conn.cursor()
    
    # Create vector storage table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_vectors (
            id TEXT PRIMARY KEY,
            content TEXT,
            embedding BLOB,
            metadata TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for fast retrieval
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON document_vectors(timestamp)')
    conn.commit()
    return conn

def vector_search(query_embedding, limit=5):
    conn = sqlite3.connect('/tmp/vectors.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT content, embedding, metadata FROM document_vectors')
    results = []
    
    for content, embedding_blob, metadata in cursor.fetchall():
        doc_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
        similarity = np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
        )
        results.append((similarity, content, metadata))
    
    # Sort by similarity and return top results
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:limit]
```

#### Lambda Function URLs
```yaml
# CloudFormation template for Function URLs
Resources:
  QueryProcessorFunctionUrl:
    Type: AWS::Lambda::Url
    Properties:
      TargetFunctionArn: !Ref QueryProcessorFunction
      AuthType: NONE
      Cors:
        AllowOrigins: ['*']
        AllowMethods: [POST, GET, OPTIONS]
        AllowHeaders: [Content-Type, Authorization]
        MaxAge: 300

Outputs:
  ApiEndpoint:
    Description: Direct Lambda Function URL
    Value: !GetAtt QueryProcessorFunctionUrl.FunctionUrl
```

#### Aggressive Caching Strategy
```python
# 24-hour response caching for ultra-budget mode
import hashlib
import json
from datetime import datetime, timedelta

def cache_response(query, documents, response):
    cache_key = hashlib.md5(f"{query}:{documents}".encode()).hexdigest()
    
    dynamodb.put_item(
        TableName='ResponseCache',
        Item={
            'cache_key': {'S': cache_key},
            'response': {'S': response},
            'ttl': {'N': str(int((datetime.now() + timedelta(hours=24)).timestamp()))}
        }
    )

def get_cached_response(query, documents):
    cache_key = hashlib.md5(f"{query}:{documents}".encode()).hexdigest()
    
    try:
        response = dynamodb.get_item(
            TableName='ResponseCache',
            Key={'cache_key': {'S': cache_key}}
        )
        
        if 'Item' in response:
            return response['Item']['response']['S']
    except:
        pass
    
    return None
```

---

### ⚖️ Balanced Mode Configuration

#### Pinecone Vector Storage
```python
# Pinecone configuration for balanced mode
import pinecone

pinecone.init(
    api_key=os.environ['PINECONE_API_KEY'],
    environment='us-east-1-aws'
)

# Create index with cost optimization
index = pinecone.Index('rag-assistant')

def upsert_vectors(vectors, batch_size=100):
    # Batch uploads to minimize costs
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        time.sleep(0.1)  # Rate limiting

def query_vectors(query_embedding, top_k=5):
    results = index.query(
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )
    return results.matches
```

#### Smart Caching Strategy
```python
# Intelligent TTL based on query type
def get_cache_ttl(query):
    # Common questions: 6 hours
    # Specific questions: 1 hour  
    # Complex analysis: 30 minutes
    
    common_patterns = ['what is', 'how to', 'explain']
    if any(pattern in query.lower() for pattern in common_patterns):
        return 6 * 3600  # 6 hours
    elif len(query.split()) > 10:
        return 30 * 60   # 30 minutes
    else:
        return 3600      # 1 hour
```

---

### 🚀 Full Mode Configuration

#### OpenSearch Serverless
```json
{
  "name": "rag-assistant-collection",
  "type": "search",
  "description": "Production vector search with hybrid capabilities"
}
```

#### Advanced Vector Index
```bash
# Create production vector index
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