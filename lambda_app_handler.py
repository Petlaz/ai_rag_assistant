"""
Lambda Handler for Gradio App
Bridges the Gradio RAG Assistant to AWS Lambda Function URLs with lazy loading
"""
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
_handler = None

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

def get_handler():
    """Lazy load the Mangum handler."""
    global _handler
    if _handler is None:
        app = get_app()
        asgi_app = app.app  # Get the underlying ASGI app
        _handler = Mangum(asgi_app, lifespan="off", api_gateway_base_path=None)
    return _handler

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Converts Function URL events to ASGI calls for Gradio
    """
    handler = get_handler()
    return handler(event, context)