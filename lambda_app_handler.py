"""
Lambda Handler for Gradio App
Bridges the Gradio RAG Assistant to AWS Lambda Function URLs with health checks
"""
import json
import os
import logging
from pathlib import Path

# Import Lambda dependencies with fallback handling
try:
    from mangum import Mangum
    MANGUM_AVAILABLE = True
except ImportError:
    logging.warning("Mangum not available - falling back to direct Lambda responses")
    MANGUM_AVAILABLE = False
    Mangum = None

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
            logger.info("🚀 Loading Gradio app dependencies (no timeout - Lambda handles this)...")
            
            from deployment.app_gradio import build_interface, load_dependencies, load_prompt_templates, AssistantState
            
            # Initialize components with lazy loading
            logger.info("📦 Loading dependencies...")
            dependencies = load_dependencies()
            
            logger.info("📝 Loading prompt templates...")
            prompts = load_prompt_templates(PROMPT_PATH) 
            
            logger.info("🔧 Building interface...")
            state = AssistantState(deps=dependencies, prompt_template=prompts)
            _app = build_interface(state)
            
            logger.info("✅ Gradio app loaded successfully!")
        except (ImportError, Exception) as e:
            logger.error(f"❌ Error loading Gradio app: {str(e)}, falling back to loading page", exc_info=True)
            # Return a simple fallback app that shows a loading interface
            _app = create_fallback_app()
    return _app

def create_fallback_app():
    """Create a simple fallback interface when Gradio can't be loaded."""
    class FallbackApp:
        def __init__(self):
            self.app = self  # For Mangum compatibility
            
        def __call__(self, event, context):
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/html",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": """
<!DOCTYPE html>
<html>
<head>
    <title>Quest Analytics RAG Assistant - Loading</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .loading { text-align: center; padding: 40px; }
        .status { background: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .retry { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="loading">
        <h1>🚀 Quest Analytics RAG Assistant</h1>
        <div class="status">
            <h3>⏳ System Initializing...</h3>
            <p>The RAG assistant is loading core dependencies. On first start this may take a moment.</p>
            <p><strong>Status:</strong> Loading Gradio and ML models...</p>
            <br>
            <button class="retry" onclick="window.location.reload()">🔄 Try Again</button>
        </div>
        <div style="text-align: left; margin-top: 30px;">
            <h3>📋 System Features:</h3>
            <ul>
                <li>✅ Interactive document Q&A interface</li>
                <li>✅ PDF upload and processing</li>
                <li>✅ Hybrid search (semantic + keyword)</li>
                <li>✅ Real-time health monitoring</li>
                <li>✅ Session management</li>
            </ul>
            <p><small>💡 <em>If this page continues to show, dependencies may be installing. Please wait and refresh.</em></small></p>
        </div>
    </div>
    <script>
        // Auto-retry every 45 seconds
        setTimeout(() => window.location.reload(), 45000);
    </script>
</body>
</html>"""
            }
    
    return FallbackApp()

def get_gradio_handler():
    """Lazy load the Mangum handler for Gradio."""
    global _gradio_handler
    if _gradio_handler is None:
        try:
            logger.info("Creating Mangum handler...")
            app = get_app()
            
            # Check if this is the fallback app
            if hasattr(app, '__class__') and app.__class__.__name__ == 'FallbackApp':
                logger.info("Using fallback app directly (no Mangum needed)")
                _gradio_handler = app
            else:
                if not MANGUM_AVAILABLE:
                    logger.error("Mangum not available but needed for ASGI app")
                    raise ImportError("Mangum is required for full Gradio app but not available")
                    
                logger.info("Creating Mangum wrapper for Gradio ASGI app")
                asgi_app = app.app  # Get the underlying ASGI app
                _gradio_handler = Mangum(asgi_app, lifespan="off", api_gateway_base_path=None)
                
            logger.info("Gradio handler created successfully")
        except Exception as e:
            logger.error(f"Error creating Gradio handler: {str(e)}", exc_info=True)
            # Create a simple error fallback
            _gradio_handler = create_error_fallback(str(e))
    return _gradio_handler

def create_error_fallback(error_msg):
    """Create an error fallback handler."""
    def error_handler(event, context):
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "RAG Assistant failed to load",
                "message": f"Initialization error: {error_msg}",
                "timestamp": context.aws_request_id if context else "local",
                "service": "lambda-initialization-error",
                "retry_suggestion": "Please wait a few moments and try again. The system may be starting up."
            })
        }
    return error_handler

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
        
        # Normalize path and ensure it's not empty
        if not path or path == '':
            path = '/'
        
        logger.info(f"Request: {http_method} {path} (raw_path: {raw_path})")
        logger.info(f"Full event structure: {json.dumps(event, default=str)[:1000]}")
        
        # Handle health check requests ONLY for EXACT /health path - return simple JSON response  
        if path == '/health' and http_method == 'GET':
            logger.info("✅ HEALTH CHECK: Returning health response for EXACT /health path")
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
        
        # Log when we are NOT returning health check to confirm routing
        logger.info(f"🚀 GRADIO ROUTE: Path '{path}' is NOT '/health' - proceeding to Gradio interface")
        
        # For all other requests (Gradio interface), use the full Gradio handler
        # This will only be loaded when actually accessing the Gradio interface
        logger.info(f"Loading Gradio handler for path: {path}")
        try:
            gradio_handler = get_gradio_handler()
            logger.info("Gradio handler loaded successfully, calling with event")
            result = gradio_handler(event, context)
            logger.info(f"Gradio handler returned result type: {type(result)}")
            return result
        except Exception as gradio_error:
            logger.error(f"🚨 GRADIO HANDLER FAILED: {str(gradio_error)}", exc_info=True)
            logger.error(f"🚨 GRADIO FAILED FOR PATH: {path}")
            # If Gradio fails, return a helpful error message but DO NOT return health check
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "Gradio interface failed to load",
                    "message": str(gradio_error),
                    "path": path,
                    "service": "lambda-gradio-failure"
                })
            }
        
    except Exception as e:
        logger.error(f"🚨 MAIN LAMBDA ERROR: {str(e)}", exc_info=True)
        logger.error(f"🚨 ERROR OCCURRED FOR PATH: {event.get('rawPath', 'unknown')}")
        # Return proper error format for Lambda Function URLs - NEVER health check
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Main Lambda handler error", 
                "message": str(e),
                "path": event.get('rawPath', 'unknown'),
                "service": "lambda-main-error"
            })
        }