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

# Main AI RAG Assistant Lambda Function
resource "aws_lambda_function" "app" {
  function_name = "${local.name_prefix}-app"
  role         = aws_iam_role.lambda_role.arn
  
  package_type = "Image"
  image_uri    = var.app_image_uri
  
  memory_size = local.config.lambda_memory
  timeout     = local.config.lambda_timeout
  
  reserved_concurrent_executions = local.config.lambda_reserved

  environment {
    variables = {
      ENVIRONMENT = var.environment
      AWS_REGION = var.aws_region
      AWS_DEFAULT_REGION = var.aws_region
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
  
  memory_size = 256
  timeout     = 10

  environment {
    variables = {
      ENVIRONMENT = var.environment
      AWS_REGION = var.aws_region
      AWS_DEFAULT_REGION = var.aws_region
    }
  }

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
  statement_id           = "AllowPublicAccess"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.app.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "landing_url_public_access" {
  statement_id           = "AllowPublicAccess"
  action                = "lambda:InvokeFunctionUrl"
  function_name         = aws_lambda_function.landing.function_name
  principal             = "*"
  function_url_auth_type = "NONE"
}