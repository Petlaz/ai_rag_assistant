variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "deployment_mode" {
  description = "Deployment mode defining resource allocation"
  type        = string
  default     = "ultra-budget"
  
  validation {
    condition     = contains(["ultra-budget", "balanced", "full-scale"], var.deployment_mode)
    error_message = "Deployment mode must be 'ultra-budget', 'balanced', or 'full-scale'."
  }
}

variable "image_tag" {
  description = "Container image tag to deploy"
  type        = string
  default     = "latest"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-rag-assistant"
}

variable "app_image_uri" {
  description = "Container image URI for the main application"
  type        = string
  default     = "ghcr.io/petlaz/rag-assistant:latest"
}

variable "landing_image_uri" {
  description = "Container image URI for the landing page"
  type        = string
  default     = "ghcr.io/petlaz/rag-landing:latest"
}

variable "worker_image_uri" {
  description = "Container image URI for the worker"
  type        = string
  default     = "ghcr.io/petlaz/rag-worker:latest"
}

# Resource sizing based on deployment mode
locals {
  deployment_config = {
    "ultra-budget" = {
      lambda_memory    = 512
      lambda_timeout   = 30
      lambda_reserved  = 1
      opensearch_instance = "t3.micro"
      opensearch_nodes = 1
    }
    "balanced" = {
      lambda_memory    = 1024
      lambda_timeout   = 60
      lambda_reserved  = 5
      opensearch_instance = "t3.small"
      opensearch_nodes = 2
    }
    "full-scale" = {
      lambda_memory    = 2048
      lambda_timeout   = 120
      lambda_reserved  = 10
      opensearch_instance = "t3.medium"
      opensearch_nodes = 3
    }
  }
  
  config = local.deployment_config[var.deployment_mode]
}