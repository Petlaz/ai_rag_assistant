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
        
        # Normalize path and ensure it's not empty
        if not path or path == '':
            path = '/'
            
        logger.info(f"Request: {http_method} {path} (raw_path: {raw_path})")
        logger.info(f"Full event structure: {json.dumps(event, default=str)[:1000]}")
        
        # Handle health check requests ONLY for EXACT /health path - return simple JSON response
        if path == '/health' and http_method == 'GET':
            logger.info("✅ LANDING HEALTH: Returning health response for EXACT /health path")
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
        
        # Log when we are NOT returning health check
        logger.info(f"🚀 FASTAPI ROUTE: Path '{path}' is NOT '/health' - proceeding to FastAPI interface")
        
        # For all other requests (FastAPI interface), use the FastAPI handler
        logger.info(f"Loading FastAPI handler for path: {path}")
        try:
            handler = get_landing_handler()
            logger.info("FastAPI handler loaded successfully, calling with event")
            result = handler(event, context)
            logger.info(f"FastAPI handler returned result type: {type(result)}")
            return result
        except Exception as fastapi_error:
            logger.error(f"🚨 FASTAPI HANDLER FAILED: {str(fastapi_error)}", exc_info=True)
            logger.error(f"🚨 FASTAPI FAILED FOR PATH: {path}")
            # If FastAPI fails, return a helpful error message
            return {
                "statusCode": 500,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "error": "FastAPI landing page failed to load",
                    "message": str(fastapi_error),
                    "path": path,
                    "service": "lambda-fastapi-failure"
                })
            }
        
    except Exception as e:
        logger.error(f"🚨 MAIN LANDING ERROR: {str(e)}", exc_info=True)
        logger.error(f"🚨 LANDING ERROR FOR PATH: {event.get('rawPath', 'unknown')}")
        # Return proper error format for Lambda Function URLs
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Main landing handler error",
                "message": str(e),
                "path": event.get('rawPath', 'unknown'),
                "service": "lambda-landing-error"
            })
        }