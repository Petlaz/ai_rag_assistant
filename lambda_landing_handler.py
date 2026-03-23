"""
Lambda Handler for Landing Page
Bridges the FastAPI landing page to AWS Lambda Function URLs with health checks
"""
import json
from mangum import Mangum

# Global variables for lazy loading
_app = None
_handler = None

def get_landing_handler():
    """Lazy load the FastAPI handler."""
    global _handler
    if _handler is None:
        from landing.main import app
        _handler = Mangum(app, lifespan="off", api_gateway_base_path=None)
    return _handler

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Handles both health checks and FastAPI landing page
    """
    try:
        # Extract request info
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('requestContext', {}).get('http', {}).get('path', '/')
        
        # Handle health check requests - return simple JSON response
        if path == '/health' and http_method == 'GET':
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
        handler = get_landing_handler()
        return handler(event, context)
        
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