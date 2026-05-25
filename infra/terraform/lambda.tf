# IAM Role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "${local.name_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Lambda basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}

# Additional IAM policies for RAG functionality
resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "lambda_bedrock_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
  role       = aws_iam_role.lambda_role.name
}

# ECR permissions for Lambda container image access
resource "aws_iam_role_policy" "lambda_ecr_access" {
  name = "${local.name_prefix}-lambda-ecr-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      }
    ]
  })
}

# Main AI RAG Assistant Lambda Function
resource "aws_lambda_function" "app" {
  function_name = "${local.name_prefix}-app"
  role         = aws_iam_role.lambda_role.arn
  
  package_type = "Image"
  image_uri    = var.app_image_uri
  
  memory_size = max(local.config.lambda_memory, 1024)
  timeout     = 180  # Allow Gradio container cold starts to finish
  
  reserved_concurrent_executions = local.config.lambda_reserved

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      OLLAMA_BASE_URL          = var.ollama_base_url
      OLLAMA_MODEL             = var.ollama_model
      OLLAMA_FALLBACK_MODEL    = var.ollama_fallback_model
      OLLAMA_TIMEOUT           = "60"
      OPENSEARCH_HOST          = var.opensearch_host
      OPENSEARCH_USERNAME      = var.opensearch_username
      OPENSEARCH_PASSWORD      = var.opensearch_password
      OPENSEARCH_INDEX         = var.opensearch_index_name
      OPENSEARCH_TLS_VERIFY    = var.opensearch_host != "" && startswith(var.opensearch_host, "https") ? "true" : "false"
      EMBEDDING_MODEL_NAME     = var.embedding_model_name
      SECURITY_ENABLED         = var.security_enabled ? "true" : "false"
      ENABLE_ANALYTICS         = var.enable_analytics ? "true" : "false"
      GRADIO_SERVER_PORT       = "7860"
      GRADIO_SERVER_NAME       = "0.0.0.0"
      GRADIO_SHARE_LINK        = "false"
    }
  }

  tags = local.common_tags
}

# Landing Page Lambda Function
resource "aws_lambda_function" "landing" {
  function_name = "${local.name_prefix}-landing"
  role         = aws_iam_role.lambda_role.arn
  
  package_type = "Image"
  image_uri    = var.landing_image_uri
  
  memory_size = 512  # Increased from 256 to 512 for better cold start performance
  timeout     = 120  # Increased to 120 seconds for FastAPI initialization

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      APP_URL          = aws_lambda_function_url.app.function_url
      LANDING_PORT     = "3000"
      ENABLE_ANALYTICS = var.enable_analytics ? "true" : "false"
    }
  }

  # Explicit dependency: landing function needs app function URL to be created first
  depends_on = [aws_lambda_function_url.app]

  tags = local.common_tags
}

# Worker Lambda Function for background processing
resource "aws_lambda_function" "worker" {
  function_name = "${local.name_prefix}-worker"
  role         = aws_iam_role.lambda_role.arn
  
  package_type = "Image" 
  image_uri    = var.worker_image_uri
  
  memory_size = local.config.lambda_memory
  timeout     = 300  # 5 minutes for processing

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = local.common_tags
}

# Lambda Function URLs for direct HTTP access
resource "aws_lambda_function_url" "app" {
  function_name      = aws_lambda_function.app.function_name
  authorization_type = "NONE"
  
  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}

resource "aws_lambda_function_url" "landing" {
  function_name      = aws_lambda_function.landing.function_name
  authorization_type = "NONE"
  
  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["GET"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }
}

# Resource-based policies to allow public access to Lambda function URLs
resource "aws_lambda_permission" "app_url_public_access" {
  statement_id           = "FunctionURLPublicAccess"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.app.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "landing_url_public_access" {
  statement_id           = "FunctionURLPublicAccess"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.landing.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}

# Additional permissions for lambda:InvokeFunction (required for function URLs created after Oct 2025)
resource "aws_lambda_permission" "app_invoke_public_access" {
  statement_id  = "FunctionURLInvokeAllowPublicAccess"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "*"
}

resource "aws_lambda_permission" "landing_invoke_public_access" {
  statement_id  = "FunctionURLInvokeAllowPublicAccess"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.landing.function_name
  principal     = "*"
}
