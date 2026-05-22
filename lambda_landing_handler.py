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
            # Configure Mangum for Lambda Function URL events
            # - lifespan="off": Disables lifespan events (not supported in Lambda)
            # - api_gateway_base_path: Use None for Lambda Function URLs
            # - backend="aws_alb": Explicitly handle as ALB/Function URL format
            _handler = Mangum(
                app,
                lifespan="off",
                api_gateway_base_path=None
            )
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
        logger.info(f"Landing handler called with event keys: {list(event.keys())}")
        
        # Extract request info - Lambda Function URL format
        request_context = event.get('requestContext', {})
        http_info = request_context.get('http', {})
        
        http_method = http_info.get('method', 'GET')
        raw_path = event.get('rawPath', '/')
        path = http_info.get('path', raw_path)
        
        # Normalize path and ensure it's not empty
        if not path or path == '':
            path = '/'
            
        logger.info(f"Request: {http_method} {path}")
        
        # Handle health check requests ONLY for EXACT /health path - return simple JSON response
        if path == '/health' and http_method == 'GET':
            logger.info("✅ LANDING HEALTH: Returning health response")
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "status": "healthy",
                    "message": "Quest Analytics Landing Page is running",
                    "service": "lambda"
                })
            }
        
        # For all other requests, use the FastAPI handler
        try:
            logger.info(f"Loading FastAPI handler for {http_method} {path}")
            handler = get_landing_handler()
            logger.info("FastAPI handler loaded, invoking with event")
            result = handler(event, context)
            logger.info(f"FastAPI handler succeeded, returning result")
            return result
        except RuntimeError as mangum_error:
            # Handle Mangum inference errors gracefully
            if "adapter was unable to infer" in str(mangum_error):
                logger.error(f"Mangum inference error: {str(mangum_error)}")
                logger.error(f"Event structure: method={http_method}, path={path}")
                logger.error(f"Raw event: {json.dumps(event, default=str)[:500]}")
                # Return a helpful error for debugging
                return {
                    "statusCode": 502,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Handler inference failed",
                        "method": http_method,
                        "path": path,
                        "debug": "Check Lambda logs for details"
                    })
                }
            else:
                raise
        except Exception as fastapi_error:
            logger.error(f"FastAPI error: {str(fastapi_error)}", exc_info=True)
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "FastAPI landing page failed",
                    "message": str(fastapi_error),
                    "path": path
                })
            }
        
    except Exception as e:
        logger.error(f"Main handler error: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Landing handler failed",
                "message": str(e)
            })
        }
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