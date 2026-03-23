"""
Lambda Handler for Landing Page
Bridges the FastAPI landing page to AWS Lambda Function URLs with health checks
"""
import json
import logging
from mangum import Mangum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for lazy loading
_app = None
_handler = None

def get_landing_handler():
    """Lazy load the FastAPI handler."""
    global _handler
    if _handler is None:
        try:
            logger.info("Loading FastAPI landing page...")
            from landing.main import app
            _handler = Mangum(app, lifespan="off", api_gateway_base_path=None)
            logger.info("FastAPI handler loaded successfully")
        except Exception as e:
            logger.error(f"Error loading FastAPI handler: {str(e)}", exc_info=True)
            raise
    return _handler

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Handles both health checks and FastAPI landing page
    """
    try:
        logger.info(f"Landing handler called with event: {json.dumps(event, default=str)[:500]}...")
        
        # Extract request info - Lambda Function URL format
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        raw_path = event.get('rawPath', '/')
        path = event.get('requestContext', {}).get('http', {}).get('path', raw_path)
        
        # Normalize path
        if not path:
            path = '/'
            
        logger.info(f"Request: {http_method} {path}")
        
        # Handle health check requests - return simple JSON response
        if path == '/health' and http_method == 'GET':
            logger.info("Returning landing health check response")
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "status": "healthy",
                    "message": "Quest Analytics Landing Page is running", 
                    "timestamp": context.aws_request_id if context else "local",
                    "service": "lambda"
                })
            }
        
        # For all other requests (FastAPI interface), use the FastAPI handler
        logger.info("Loading FastAPI handler...")
        handler = get_landing_handler()
        return handler(event, context)
        
    except Exception as e:
        logger.error(f"Landing handler error: {str(e)}", exc_info=True)
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