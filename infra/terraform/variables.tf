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

# Service Configuration Variables
variable "ollama_base_url" {
  description = "Ollama server URL (e.g., http://ollama-service:11434 or https://ollama.example.com)"
  type        = string
  default     = ""  # Must be set for production deployment
  sensitive   = false
}

variable "opensearch_host" {
  description = "OpenSearch domain endpoint (e.g., my-domain.us-east-1.es.amazonaws.com:9200)"
  type        = string
  default     = ""  # Must be set for production deployment
  sensitive   = false
}

variable "opensearch_username" {
  description = "OpenSearch master username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "opensearch_password" {
  description = "OpenSearch master password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ollama_model" {
  description = "Primary Ollama model name"
  type        = string
  default     = "llama2"
}

variable "ollama_fallback_model" {
  description = "Fallback Ollama model name"
  type        = string
  default     = "mistral"
}

variable "embedding_model_name" {
  description = "Sentence transformer model for embeddings"
  type        = string
  default     = "all-MiniLM-L6-v2"
}

variable "opensearch_index_name" {
  description = "OpenSearch index name for RAG documents"
  type        = string
  default     = "quest-research"
}

variable "security_enabled" {
  description = "Enable security middleware (rate limiting, input validation)"
  type        = bool
  default     = true
}

variable "enable_analytics" {
  description = "Enable analytics tracking"
  type        = bool
  default     = false
}

# Resource sizing based on deployment mode
locals {
  deployment_config = {
    "ultra-budget" = {
      lambda_memory    = 512
      lambda_timeout   = 30
      lambda_reserved  = -1  # No concurrency limit to avoid AWS minimum requirements
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