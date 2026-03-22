"""
Lambda Handler for Landing Page
Bridges the FastAPI landing page to AWS Lambda Function URLs
"""
from mangum import Mangum
from landing.main import app

# Create Lambda handler using Mangum (FastAPI -> Lambda adapter)
handler = Mangum(app, lifespan="off", api_gateway_base_path=None)

def lambda_handler(event, context):
    """
    AWS Lambda handler for Function URLs
    Converts Function URL events to ASGI calls
    """
    return handler(event, context)