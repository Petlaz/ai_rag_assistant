"""
Lambda Handler for Landing Page
Bridges the FastAPI landing page to AWS Lambda Function URLs with health checks
"""
import json
import logging
import sys
from mangum import Mangum

# Configure logging with immediate flush
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

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
    print(f"\n{'='*60}")
    print(f"LAMBDA HANDLER INVOKED")
    print(f"Event: {json.dumps(event, default=str)[:200]}")
    print(f"Context: function_name={context.function_name}, aws_request_id={context.aws_request_id}")
    print(f"{'='*60}\n")
    sys.stdout.flush()
    
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
        sys.stdout.flush()
        
        # Handle health check requests ONLY for EXACT /health path - return simple JSON response
        if path == '/health' and http_method == 'GET':
            logger.info("✅ LANDING HEALTH: Returning health response")
            response = {
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
            logger.info(f"Health response: {response}")
            sys.stdout.flush()
            return response
        
        # For all other requests, use the FastAPI handler
        try:
            logger.info(f"Loading FastAPI handler for {http_method} {path}")
            sys.stdout.flush()
            handler = get_landing_handler()
            logger.info("FastAPI handler loaded, invoking with event")
            sys.stdout.flush()
            result = handler(event, context)
            logger.info(f"FastAPI handler succeeded, returning result: {type(result)}")
            sys.stdout.flush()
            return result
        except RuntimeError as mangum_error:
            # Handle Mangum inference errors gracefully
            logger.error(f"RuntimeError in handler: {str(mangum_error)}", exc_info=True)
            sys.stdout.flush()
            if "adapter was unable to infer" in str(mangum_error):
                logger.error(f"Mangum inference error")
                logger.error(f"Event structure: method={http_method}, path={path}")
                logger.error(f"Raw event: {json.dumps(event, default=str)[:500]}")
                # Return a helpful error for debugging
                response = {
                    "statusCode": 502,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Handler inference failed",
                        "method": http_method,
                        "path": path,
                        "debug": "Check Lambda logs for details"
                    })
                }
                sys.stdout.flush()
                return response
            else:
                raise
        except Exception as fastapi_error:
            logger.error(f"FastAPI error: {str(fastapi_error)}", exc_info=True)
            sys.stdout.flush()
            response = {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "FastAPI landing page failed",
                    "message": str(fastapi_error)[:200],
                    "path": path
                })
            }
            sys.stdout.flush()
            return response
        
    except Exception as e:
        logger.error(f"Main handler error: {str(e)}", exc_info=True)
        sys.stdout.flush()
        response = {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Landing handler failed",
                "message": str(e)[:200]
            })
        }
        sys.stdout.flush()
        return response