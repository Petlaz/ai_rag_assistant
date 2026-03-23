"""
Lambda Handler for Gradio App
Bridges the Gradio RAG Assistant to AWS Lambda Function URLs with health checks
"""
import json
import os
from pathlib import Path
from mangum import Mangum

# Set environment for Lambda execution
os.environ.setdefault("GRADIO_SHARE_LINK", "false")
os.environ.setdefault("GRADIO_SERVER_PORT", "7860")

# Path setup - use absolute path from working directory  
PROMPT_PATH = Path("/app/rag_pipeline/prompts/research_qa_prompt.yaml")

# Global variables for lazy loading
_app = None
_gradio_handler = None

def get_app():
    """Lazy load the Gradio app to avoid cold start timeouts."""
    global _app
    if _app is None:
        from deployment.app_gradio import build_interface, load_dependencies, load_prompt_templates, AssistantState
        
        # Initialize components with lazy loading
        dependencies = load_dependencies()
        prompts = load_prompt_templates(PROMPT_PATH) 
        state = AssistantState(deps=dependencies, prompt_template=prompts)
        _app = build_interface(state)
    return _app

def get_gradio_handler():
    """Lazy load the Mangum handler for Gradio."""
    global _gradio_handler
    if _gradio_handler is None:
        app = get_app()
        asgi_app = app.app  # Get the underlying ASGI app
        _gradio_handler = Mangum(asgi_app, lifespan="off", api_gateway_base_path=None)
    return _gradio_handler

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Handles both health checks and Gradio web interface
    """
    try:
        # Extract request info
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('requestContext', {}).get('http', {}).get('path', '/')
        
        # Handle health check requests - return simple JSON response
        if path in ['/', '/health'] and http_method == 'GET':
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "status": "healthy",
                    "message": "Quest Analytics RAG Assistant is running",
                    "timestamp": context.aws_request_id if context else "local",
                    "service": "lambda"
                })
            }
        
        # For all other requests (Gradio interface), use the full Gradio handler
        # This will only be loaded when actually accessing the Gradio interface
        gradio_handler = get_gradio_handler()
        return gradio_handler(event, context)
        
    except Exception as e:
        # Return proper error format for Lambda Function URLs
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e),
                "service": "lambda"
            })
        }