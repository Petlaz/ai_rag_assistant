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

# Main AI RAG Assistant Lambda Function
resource "aws_lambda_function" "app" {
  function_name = "${local.name_prefix}-app"
  role         = aws_iam_role.lambda_role.arn
  
  # Using a dummy source for now - would be replaced by actual container image
  filename         = data.archive_file.dummy_zip.output_path
  source_code_hash = data.archive_file.dummy_zip.output_base64sha256
  
  handler = "app.handler"
  runtime = "python3.11"
  
  memory_size = local.config.lambda_memory
  timeout     = local.config.lambda_timeout
  
  reserved_concurrent_executions = local.config.lambda_reserved

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = local.common_tags
}

# Landing Page Lambda Function
resource "aws_lambda_function" "landing" {
  function_name = "${local.name_prefix}-landing"
  role         = aws_iam_role.lambda_role.arn
  
  filename         = data.archive_file.dummy_zip.output_path
  source_code_hash = data.archive_file.dummy_zip.output_base64sha256
  
  handler = "main.handler"
  runtime = "python3.11"
  
  memory_size = 256
  timeout     = 10

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = local.common_tags
}

# Worker Lambda Function for background processing
resource "aws_lambda_function" "worker" {
  function_name = "${local.name_prefix}-worker"
  role         = aws_iam_role.lambda_role.arn
  
  filename         = data.archive_file.dummy_zip.output_path
  source_code_hash = data.archive_file.dummy_zip.output_base64sha256
  
  handler = "worker.handler"
  runtime = "python3.11"
  
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

# Dummy zip file for initial deployment
data "archive_file" "dummy_zip" {
  type        = "zip"
  output_path = "/tmp/dummy.zip"
  
  source {
    content  = "def handler(event, context): return {'statusCode': 200, 'body': 'Hello World'}"
    filename = "index.py"
  }
}