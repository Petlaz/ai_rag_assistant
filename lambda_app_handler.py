"""
Lambda Handler for Gradio App
Bridges the Gradio RAG Assistant to AWS Lambda Function URLs with health checks
"""
import json
import os
import logging
from pathlib import Path
from mangum import Mangum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        try:
            logger.info("Loading Gradio app dependencies...")
            from deployment.app_gradio import build_interface, load_dependencies, load_prompt_templates, AssistantState
            
            # Initialize components with lazy loading
            dependencies = load_dependencies()
            prompts = load_prompt_templates(PROMPT_PATH) 
            state = AssistantState(deps=dependencies, prompt_template=prompts)
            _app = build_interface(state)
            logger.info("Gradio app loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Gradio app: {str(e)}", exc_info=True)
            raise
    return _app

def get_gradio_handler():
    """Lazy load the Mangum handler for Gradio."""
    global _gradio_handler
    if _gradio_handler is None:
        try:
            logger.info("Creating Mangum handler...")
            app = get_app()
            asgi_app = app.app  # Get the underlying ASGI app
            _gradio_handler = Mangum(asgi_app, lifespan="off", api_gateway_base_path=None)
            logger.info("Mangum handler created successfully")
        except Exception as e:
            logger.error(f"Error creating Mangum handler: {str(e)}", exc_info=True)
            raise
    return _gradio_handler

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Handles both health checks and Gradio web interface
    """
    try:
        logger.info(f"Lambda handler called with event: {json.dumps(event, default=str)[:500]}...")
        
        # Extract request info - Lambda Function URL format
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        raw_path = event.get('rawPath', '/')
        path = event.get('requestContext', {}).get('http', {}).get('path', raw_path)
        
        # Normalize path
        if not path:
            path = '/'
        
        logger.info(f"Request: {http_method} {path}")
        
        # Handle health check requests - return simple JSON response
        if path in ['/', '/health'] and http_method == 'GET':
            logger.info("Returning health check response")
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
        logger.info("Loading Gradio handler...")
        gradio_handler = get_gradio_handler()
        return gradio_handler(event, context)
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}", exc_info=True)
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