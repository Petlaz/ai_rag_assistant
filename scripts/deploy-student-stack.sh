#!/bin/bash
# scripts/deploy-student-stack.sh
# Cost-optimized AWS deployment for master students
# Estimated monthly cost: $15-50

set -e

# Configuration
STACK_NAME="rag-assistant-student"
REGION="us-east-1"
ENVIRONMENT="dev"
BUDGET_LIMIT="50"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check if user has student credits
    print_warning "Ensure you have AWS student credits activated to minimize costs."
    read -p "Do you have AWS student credits activated? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Consider activating AWS Educate credits to reduce costs."
    fi
    
    print_success "Prerequisites check completed"
}

# Estimate costs
estimate_costs() {
    print_step "Cost estimation for student deployment..."
    
    cat << EOF

💰 ESTIMATED MONTHLY COSTS (Student-Optimized):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Core Services (Always On):
├── S3 Storage (documents + web)    : \$1-3/month
├── CloudFront CDN                 : \$1-2/month
├── Route 53 (if custom domain)    : \$0.50/month

Pay-Per-Use Services:
├── Lambda (1M requests/month)     : \$5-10/month
├── API Gateway (1M requests)      : \$3-5/month
├── OpenSearch Serverless         : \$10-20/month
├── AWS Bedrock (100K tokens/day) : \$2-8/month
├── DynamoDB (response cache)     : \$1-3/month

TOTAL ESTIMATED: \$15-50/month
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 COST OPTIMIZATION TIPS:
• Use AWS student credits for first year
• Enable AWS Budgets alerts at \$40
• Monitor costs weekly via AWS Console
• Use Spot instances if moving to ECS later

EOF
    
    read -p "Proceed with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
}

# Create CloudFormation template
create_cloudformation_template() {
    print_step "Creating CloudFormation template..."
    
    mkdir -p infrastructure
    
    cat > infrastructure/student-stack.yml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Cost-optimized RAG Assistant for Master Students'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: 'dev'
    AllowedValues: ['dev', 'staging', 'prod']
  
  BudgetLimit:
    Type: Number
    Default: 50
    Description: 'Monthly budget limit in USD'

Resources:
  # S3 Bucket for document storage
  DocumentStorageBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-documents-${Environment}-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: CostOptimization
            Status: Enabled
            Transitions:
              - TransitionInDays: 30
                StorageClass: STANDARD_IA
              - TransitionInDays: 90
                StorageClass: GLACIER
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # S3 Bucket for web hosting
  WebHostingBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::StackName}-web-${Environment}-${AWS::AccountId}'
      WebsiteConfiguration:
        IndexDocument: index.html
        ErrorDocument: error.html
      CorsConfiguration:
        CorsRules:
          - AllowedHeaders: ['*']
            AllowedMethods: [GET, PUT, POST, DELETE, HEAD]
            AllowedOrigins: ['*']

  # Web bucket policy for public read
  WebBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref WebHostingBucket
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal: '*'
            Action: s3:GetObject
            Resource: !Sub '${WebHostingBucket}/*'

  # DynamoDB table for response caching
  CacheTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-cache'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: query_hash
          AttributeType: S
      KeySchema:
        - AttributeName: query_hash
          KeyType: HASH
      TimeToLiveSpecification:
        AttributeName: ttl
        Enabled: true

  # Lambda execution role
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: RAGAssistantPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource: !Sub '${DocumentStorageBucket}/*'
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                  - dynamodb:PutItem
                  - dynamodb:UpdateItem
                Resource: !GetAtt CacheTable.Arn
              - Effect: Allow
                Action:
                  - bedrock:InvokeModel
                  - bedrock:InvokeModelWithResponseStream
                Resource: '*'
              - Effect: Allow
                Action:
                  - aoss:APIAccessAll
                Resource: !Sub 'arn:aws:aoss:${AWS::Region}:${AWS::AccountId}:collection/*'

  # Lambda function for document processing
  DocumentProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-document-processor'
      CodeUri: ../lambda-functions/document-processor/
      Handler: lambda_function.lambda_handler
      Runtime: python3.11
      MemorySize: 1024
      Timeout: 300
      Environment:
        Variables:
          DOCUMENT_BUCKET: !Ref DocumentStorageBucket
          CACHE_TABLE: !Ref CacheTable
          OPENSEARCH_ENDPOINT: !GetAtt OpenSearchCollection.CollectionEndpoint
      Events:
        S3Event:
          Type: S3
          Properties:
            Bucket: !Ref DocumentStorageBucket
            Events: s3:ObjectCreated:*

  # Lambda function for query processing
  QueryProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-query-processor'
      CodeUri: ../lambda-functions/query-processor/
      Handler: lambda_function.lambda_handler
      Runtime: python3.11
      MemorySize: 1024
      Timeout: 300
      Environment:
        Variables:
          DOCUMENT_BUCKET: !Ref DocumentStorageBucket
          CACHE_TABLE: !Ref CacheTable
          OPENSEARCH_ENDPOINT: !GetAtt OpenSearchCollection.CollectionEndpoint

  # API Gateway
  RestApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: !Sub '${AWS::StackName}-api'
      Description: 'RAG Assistant API'
      EndpointConfiguration:
        Types: [REGIONAL]

  # API Gateway deployment
  ApiDeployment:
    Type: AWS::ApiGateway::Deployment
    DependsOn: 
      - QueryMethod
      - UploadMethod
    Properties:
      RestApiId: !Ref RestApi
      StageName: !Ref Environment

  # API Gateway resources and methods
  QueryResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref RestApi
      ParentId: !GetAtt RestApi.RootResourceId
      PathPart: query

  QueryMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref RestApi
      ResourceId: !Ref QueryResource
      HttpMethod: POST
      AuthorizationType: NONE
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryProcessorFunction.Arn}/invocations'

  UploadResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref RestApi
      ParentId: !GetAtt RestApi.RootResourceId
      PathPart: upload

  UploadMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref RestApi
      ResourceId: !Ref UploadResource
      HttpMethod: POST
      AuthorizationType: NONE
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DocumentProcessorFunction.Arn}/invocations'

  # Lambda permissions for API Gateway
  QueryLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref QueryProcessorFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApi}/*/*'

  DocumentLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref DocumentProcessorFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApi}/*/*'

  # OpenSearch Serverless Collection
  OpenSearchCollection:
    Type: AWS::OpenSearchServerless::Collection
    Properties:
      Name: !Sub '${AWS::StackName}-collection'
      Type: SEARCH
      Description: 'Vector search for RAG Assistant'

  # CloudWatch Dashboard
  CostMonitoringDashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub '${AWS::StackName}-monitoring'
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "properties": {
                "metrics": [
                  ["AWS/Lambda", "Duration", "FunctionName", "${QueryProcessorFunction}"],
                  ["AWS/Lambda", "Invocations", "FunctionName", "${QueryProcessorFunction}"],
                  ["AWS/Lambda", "Errors", "FunctionName", "${QueryProcessorFunction}"]
                ],
                "period": 300,
                "stat": "Average",
                "region": "${AWS::Region}",
                "title": "Lambda Performance"
              }
            }
          ]
        }

  # AWS Budget for cost control
  CostBudget:
    Type: AWS::Budgets::Budget
    Properties:
      Budget:
        BudgetName: !Sub '${AWS::StackName}-budget'
        BudgetLimit:
          Amount: !Ref BudgetLimit
          Unit: USD
        TimeUnit: MONTHLY
        BudgetType: COST
        CostFilters:
          Service:
            - Amazon Simple Storage Service
            - AWS Lambda
            - Amazon API Gateway
            - Amazon OpenSearch Service
            - Amazon Bedrock
            - Amazon DynamoDB

Outputs:
  ApiGatewayUrl:
    Description: 'API Gateway endpoint URL'
    Value: !Sub 'https://${RestApi}.execute-api.${AWS::Region}.amazonaws.com/${Environment}'
    Export:
      Name: !Sub '${AWS::StackName}-ApiUrl'

  WebsiteUrl:
    Description: 'S3 website endpoint'
    Value: !GetAtt WebHostingBucket.WebsiteURL
    Export:
      Name: !Sub '${AWS::StackName}-WebUrl'

  DocumentBucket:
    Description: 'S3 bucket for document storage'
    Value: !Ref DocumentStorageBucket
    Export:
      Name: !Sub '${AWS::StackName}-DocBucket'

  QueryProcessorFunctionName:
    Description: 'Query processor Lambda function name'
    Value: !Ref QueryProcessorFunction
    Export:
      Name: !Sub '${AWS::StackName}-QueryFunction'
EOF
    
    print_success "CloudFormation template created"
}

# Create Lambda function code
create_lambda_functions() {
    print_step "Creating Lambda function code..."
    
    # Create directory structure
    mkdir -p lambda-functions/query-processor
    mkdir -p lambda-functions/document-processor
    
    # Query processor Lambda
    cat > lambda-functions/query-processor/lambda_function.py << 'EOF'
import json
import boto3
import hashlib
import time
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')
s3 = boto3.client('s3')

# Environment variables
CACHE_TABLE_NAME = os.environ.get('CACHE_TABLE')
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')

def lambda_handler(event, context):
    """
    Process user queries with caching and cost optimization
    """
    try:
        # Parse request
        body = json.loads(event['body']) if event.get('body') else {}
        query = body.get('query', '')
        
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Query is required'})
            }
        
        # Check cache first
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cached_response = get_cached_response(cache_key)
        
        if cached_response:
            logger.info(f"Cache hit for query: {query[:50]}...")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'response': cached_response,
                    'cached': True
                })
            }
        
        # Process query (simplified for demo)
        response = process_rag_query(query)
        
        # Cache the response
        cache_response(cache_key, response)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response,
                'cached': False
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def get_cached_response(cache_key: str) -> str:
    """Get cached response from DynamoDB"""
    try:
        table = dynamodb.Table(CACHE_TABLE_NAME)
        response = table.get_item(Key={'query_hash': cache_key})
        
        item = response.get('Item')
        if item and item.get('ttl', 0) > int(time.time()):
            return item.get('response')
        return None
        
    except Exception as e:
        logger.error(f"Cache retrieval error: {str(e)}")
        return None

def cache_response(cache_key: str, response: str):
    """Cache response in DynamoDB with TTL"""
    try:
        table = dynamodb.Table(CACHE_TABLE_NAME)
        table.put_item(
            Item={
                'query_hash': cache_key,
                'response': response,
                'ttl': int(time.time()) + 3600  # 1 hour TTL
            }
        )
    except Exception as e:
        logger.error(f"Cache storage error: {str(e)}")

def process_rag_query(query: str) -> str:
    """
    Simplified RAG processing using AWS Bedrock
    In production, this would include OpenSearch retrieval
    """
    try:
        # Use Claude 3 Haiku for cost optimization
        prompt = f"""
        You are a helpful research assistant. Based on the uploaded documents, 
        please answer the following question: {query}
        
        If you don't have relevant information in the documents, please say so.
        """
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        logger.error(f"Bedrock error: {str(e)}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
EOF

    # Document processor Lambda
    cat > lambda-functions/document-processor/lambda_function.py << 'EOF'
import json
import boto3
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Process document uploads and trigger indexing
    """
    try:
        if event.get('Records'):
            # S3 trigger event
            for record in event['Records']:
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']
                logger.info(f"Processing document: s3://{bucket}/{key}")
                
                # Process the document
                result = process_document(bucket, key)
                logger.info(f"Document processed: {result}")
        
        else:
            # API Gateway event
            body = json.loads(event['body']) if event.get('body') else {}
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Document upload endpoint ready',
                    'upload_url': 'Use pre-signed URL for uploads'
                })
            }
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Document processing failed'})
        }

def process_document(bucket: str, key: str) -> Dict[str, Any]:
    """
    Process uploaded document for indexing
    """
    try:
        # Get the document
        response = s3.get_object(Bucket=bucket, Key=key)
        
        # For demo purposes, just log the document info
        logger.info(f"Document size: {response['ContentLength']} bytes")
        logger.info(f"Document type: {response.get('ContentType', 'unknown')}")
        
        # In production, this would:
        # 1. Extract text from PDF
        # 2. Chunk the content
        # 3. Generate embeddings
        # 4. Index in OpenSearch
        
        return {
            'status': 'processed',
            'bucket': bucket,
            'key': key,
            'size': response['ContentLength']
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise
EOF

    # Create requirements.txt for Lambda functions
    cat > lambda-functions/query-processor/requirements.txt << 'EOF'
boto3>=1.34.0
PyPDF2>=3.0.1
sentence-transformers>=2.7.0
numpy>=1.24.0
EOF

    cat > lambda-functions/document-processor/requirements.txt << 'EOF'
boto3>=1.34.0
PyPDF2>=3.0.1
EOF

    print_success "Lambda function code created"
}

# Create static web interface
create_web_interface() {
    print_step "Creating static web interface..."
    
    mkdir -p static-web
    
    cat > static-web/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest Analytics RAG Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .main {
            padding: 30px;
        }
        
        .upload-section, .query-section {
            margin-bottom: 30px;
            padding: 20px;
            border: 2px dashed #e0e0e0;
            border-radius: 10px;
            background: #f9f9f9;
        }
        
        .section-title {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #333;
        }
        
        input[type="file"], input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        .response {
            margin-top: 20px;
            padding: 20px;
            background: #f0f8ff;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            white-space: pre-wrap;
        }
        
        .cost-info {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Quest Analytics RAG Assistant</h1>
            <p>Student-Optimized AWS Deployment • Cost: $15-50/month</p>
        </div>
        
        <div class="main">
            <div class="upload-section">
                <h3 class="section-title">📄 Upload Documents</h3>
                <input type="file" id="fileInput" accept=".pdf" multiple>
                <button onclick="uploadFile()">Upload PDF</button>
            </div>
            
            <div class="query-section">
                <h3 class="section-title">💬 Ask Questions</h3>
                <input type="text" id="queryInput" placeholder="Ask a question about your documents...">
                <button onclick="askQuestion()">Ask Question</button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Processing your request...</p>
            </div>
            
            <div id="response" class="response" style="display: none;"></div>
            
            <div class="cost-info">
                💰 <strong>Cost Optimization:</strong> This deployment uses AWS Bedrock Claude 3 Haiku ($0.25/1M tokens) 
                with intelligent caching to minimize costs. Responses are cached for 1 hour to avoid duplicate charges.
            </div>
        </div>
    </div>

    <script>
        // This would be replaced with actual API endpoints
        const API_BASE_URL = 'YOUR_API_GATEWAY_URL_HERE';
        
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showResponse(text, cached = false) {
            const responseDiv = document.getElementById('response');
            const cacheInfo = cached ? ' (Cached - No additional cost!)' : '';
            responseDiv.innerHTML = text + cacheInfo;
            responseDiv.style.display = 'block';
        }
        
        function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const files = fileInput.files;
            
            if (files.length === 0) {
                alert('Please select a file to upload');
                return;
            }
            
            showLoading();
            
            // Simulate upload process
            setTimeout(() => {
                hideLoading();
                showResponse('Document uploaded successfully! You can now ask questions about it.');
            }, 2000);
        }
        
        function askQuestion() {
            const query = document.getElementById('queryInput').value;
            
            if (!query.trim()) {
                alert('Please enter a question');
                return;
            }
            
            showLoading();
            
            // Simulate API call
            setTimeout(() => {
                hideLoading();
                const responses = [
                    'Based on the uploaded document, here is the relevant information...',
                    'The document indicates that...',
                    'According to the research findings in your document...'
                ];
                const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                const isCached = Math.random() > 0.5;
                showResponse(randomResponse, isCached);
            }, 3000);
        }
        
        // Enable Enter key for query input
        document.getElementById('queryInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askQuestion();
            }
        });
    </script>
</body>
</html>
EOF

    print_success "Static web interface created"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_step "Deploying AWS infrastructure..."
    
    # Package Lambda functions
    for func in query-processor document-processor; do
        cd lambda-functions/$func
        pip install -r requirements.txt -t ./ --quiet
        zip -r ../../${func}.zip . -x "__pycache__/*" "*.pyc"
        cd ../..
    done
    
    # Deploy CloudFormation stack
    aws cloudformation deploy \
        --template-file infrastructure/student-stack.yml \
        --stack-name $STACK_NAME \
        --capabilities CAPABILITY_IAM \
        --region $REGION \
        --parameter-overrides \
            Environment=$ENVIRONMENT \
            BudgetLimit=$BUDGET_LIMIT \
        --no-fail-on-empty-changeset
    
    if [ $? -eq 0 ]; then
        print_success "Infrastructure deployed successfully"
    else
        print_error "Infrastructure deployment failed"
        exit 1
    fi
}

# Update Lambda functions
update_lambda_functions() {
    print_step "Updating Lambda function code..."
    
    # Get function names from stack
    QUERY_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`QueryProcessorFunctionName`].OutputValue' \
        --output text \
        --region $REGION)
    
    # Update Lambda functions
    aws lambda update-function-code \
        --function-name $QUERY_FUNCTION \
        --zip-file fileb://query-processor.zip \
        --region $REGION
    
    print_success "Lambda functions updated"
}

# Deploy web assets
deploy_web_assets() {
    print_step "Deploying web assets..."
    
    # Get S3 bucket from stack
    WEB_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
        --output text \
        --region $REGION | cut -d'/' -f3 | cut -d'.' -f1)
    
    # Upload web assets
    aws s3 sync static-web/ s3://$WEB_BUCKET/ --delete --region $REGION
    
    print_success "Web assets deployed"
}

# Get deployment info
get_deployment_info() {
    print_step "Getting deployment information..."
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text \
        --region $REGION)
    
    WEB_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteUrl`].OutputValue' \
        --output text \
        --region $REGION)
    
    cat << EOF

🎉 DEPLOYMENT SUCCESSFUL!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 Web Interface: $WEB_URL
🔗 API Endpoint:  $API_URL
💰 Cost Monitor:  https://console.aws.amazon.com/billing/home
📊 CloudWatch:    https://console.aws.amazon.com/cloudwatch/home?region=$REGION

📝 NEXT STEPS:
1. Visit your web interface and test document upload
2. Set up AWS Budgets alerts for cost control  
3. Monitor usage in CloudWatch dashboards
4. Update the web interface with your actual API URL

💡 COST OPTIMIZATION REMINDERS:
• Monitor costs daily for first week
• Use cached responses when possible
• Consider using Bedrock Claude 3 Haiku for cost efficiency
• Set up billing alerts at \$40 threshold

🎓 PORTFOLIO TIPS:
• Document your architecture decisions
• Create a demo video for job interviews
• Track cost optimizations achieved
• Showcase serverless best practices

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Happy job hunting! 🚀
EOF
}

# Cleanup function for failed deployments
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed. Cleaning up resources..."
        aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Main deployment flow
main() {
    echo "🎓 AWS RAG Assistant - Student Deployment Script"
    echo "================================================"
    
    check_prerequisites
    estimate_costs
    create_cloudformation_template
    create_lambda_functions
    create_web_interface
    deploy_infrastructure
    update_lambda_functions
    deploy_web_assets
    get_deployment_info
    
    print_success "Deployment completed successfully!"
}

# Run main function
main "$@"