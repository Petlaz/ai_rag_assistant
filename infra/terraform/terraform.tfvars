# Terraform Variables for Quest Analytics RAG Assistant
# Please update the values below before running terraform.

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

environment = "staging"

deployment_mode = "balanced"

aws_region = "us-east-1"

# ============================================================================
# CONTAINER IMAGE URIS
# ============================================================================
app_image_uri      = "ghcr.io/petlaz/rag-assistant:latest"
landing_image_uri  = "ghcr.io/petlaz/rag-landing:latest"
worker_image_uri   = "ghcr.io/petlaz/rag-worker:latest"

# ============================================================================
# CRITICAL: EXTERNAL SERVICE CONFIGURATION
# ============================================================================

ollama_base_url = "https://ollama.example.com"  # Set to a reachable Ollama service URL (not localhost)

opensearch_host = ""  # TODO: Set your OpenSearch endpoint

opensearch_username = "admin"
opensearch_password = ""  # TODO: Set your OpenSearch password

# ============================================================================
# OPTIONAL: SERVICE CONFIGURATION
# ============================================================================

ollama_model          = "gemma3:1b"
ollama_fallback_model = "mistral"

embedding_model_name = "all-MiniLM-L6-v2"

opensearch_index_name = "quest-research"

security_enabled = true

enable_analytics = false
