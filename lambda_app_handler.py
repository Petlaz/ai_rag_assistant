"""
Lambda Handler for Gradio App
Bridges the Gradio RAG Assistant to AWS Lambda Function URLs
"""
import os
from pathlib import Path
from mangum import Mangum
from deployment.app_gradio import build_interface, load_dependencies, load_prompt_templates, AssistantState

# Set environment for Lambda execution
os.environ.setdefault("GRADIO_SHARE_LINK", "false")
os.environ.setdefault("GRADIO_SERVER_PORT", "7860")

# Path setup - use absolute path from working directory
PROMPT_PATH = Path("/app/rag_pipeline/prompts")

# Initialize the app components
dependencies = load_dependencies()
prompts = load_prompt_templates(PROMPT_PATH) 
state = AssistantState(deps=dependencies, prompt_template=prompts)
app = build_interface(state)

# Create ASGI app from Gradio interface
asgi_app = app.app  # Get the underlying ASGI app

# Create Lambda handler using Mangum
handler = Mangum(asgi_app, lifespan="off", api_gateway_base_path=None)

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Converts Function URL events to ASGI calls for Gradio
    """
    return handler(event, context)