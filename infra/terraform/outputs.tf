output "app_url" {
  description = "URL for the main AI RAG Assistant application"
  value       = aws_lambda_function_url.app.function_url
}

output "landing_url" {
  description = "URL for the landing page"
  value       = aws_lambda_function_url.landing.function_url
}

output "app_function_url" {
  description = "URL for the main AI RAG Assistant application (legacy)"
  value       = aws_lambda_function_url.app.function_url
}

output "landing_function_url" {
  description = "URL for the landing page (legacy)" 
  value       = aws_lambda_function_url.landing.function_url
}

output "function_names" {
  description = "Names of deployed Lambda functions"
  value = {
    app     = aws_lambda_function.app.function_name
    landing = aws_lambda_function.landing.function_name
    worker  = aws_lambda_function.worker.function_name
  }
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    environment      = var.environment
    deployment_mode  = var.deployment_mode
    image_tag       = var.image_tag
    region          = data.aws_region.current.name
    account_id      = data.aws_caller_identity.current.account_id
  }
}