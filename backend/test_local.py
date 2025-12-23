"""
Local testing script for GreenChain Agent Lambda function.
Simulates Lambda events for local development and testing.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env.local in parent directory
env_path = Path(__file__).parent.parent / '.env.local'
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")
else:
    print(f"Warning: .env.local not found at {env_path}")
    # Try loading from current directory as fallback
    load_dotenv()

# Add src directory to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lambda_function import lambda_handler


class MockContext:
    """Mock AWS Lambda context object."""
    def __init__(self):
        self.function_name = "greenchain-agent-test"
        self.function_version = "$LATEST"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:greenchain-agent-test"
        self.memory_limit_in_mb = 512
        self.aws_request_id = "test-request-id"
        self.log_group_name = "/aws/lambda/greenchain-agent-test"
        self.log_stream_name = "2024/01/01/[$LATEST]test-stream"


def create_lambda_event(
    latitude: float,
    longitude: float,
    date_range: Dict[str, str] = None,
    user_request: str = None,
    http_method: str = "POST"
) -> Dict[str, Any]:
    """
    Create a simulated Lambda event (API Gateway format).
    
    Args:
        latitude: Farm latitude
        longitude: Farm longitude
        date_range: Optional dict with "start" and "end" keys (YYYY-MM-DD format)
        user_request: Optional user-provided context
        http_method: HTTP method (default: POST)
    
    Returns:
        Simulated Lambda event dictionary
    """
    body = {
        "latitude": latitude,
        "longitude": longitude
    }
    
    if date_range:
        body["date_range"] = date_range
    
    if user_request:
        body["user_request"] = user_request
    
    event = {
        "httpMethod": http_method,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body),
        "pathParameters": None,
        "queryStringParameters": None,
        "requestContext": {
            "requestId": "test-request-id",
            "stage": "test"
        }
    }
    
    return event


def print_response(response: Dict[str, Any]):
    """Pretty print the Lambda response."""
    print("\n" + "="*80)
    print("LAMBDA RESPONSE")
    print("="*80)
    print(f"Status Code: {response.get('statusCode')}")
    print(f"Headers: {json.dumps(response.get('headers', {}), indent=2)}")
    
    body = response.get('body', '{}')
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            pass
    
    print("\nResponse Body:")
    print(json.dumps(body, indent=2))
    print("="*80 + "\n")


def test_basic_request():
    """Test a basic loan request with coordinates."""
    print("TEST 1: Basic Loan Request")
    print("-" * 80)
    
    # Example: A farm in Iowa, USA (agricultural region)
    event = create_lambda_event(
        # 27.259672470173367, 79.84445028295187
        # 29.60582075720407, 76.27318739521897
        # latitude=41.8781,
        # longitude=-93.0977,
        latitude=29.60582075720407,
        longitude=76.27318739521897,
        user_request="Requesting micro-loan for sustainable farming practices"
    )
    
    context = MockContext()
    response = lambda_handler(event, context)
    print_response(response)
    
    return response


def test_with_date_range():
    """Test a loan request with a specific date range."""
    print("TEST 2: Loan Request with Date Range")
    print("-" * 80)
    
    event = create_lambda_event(
        latitude=40.7128,
        longitude=-74.0060,
        date_range={
            "start": "2024-01-01",
            "end": "2024-01-31"
        },
        user_request="Need loan for organic crop expansion"
    )
    
    context = MockContext()
    response = lambda_handler(event, context)
    print_response(response)
    
    return response


def test_missing_parameters():
    """Test error handling for missing parameters."""
    print("TEST 3: Missing Parameters (Error Handling)")
    print("-" * 80)
    
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"latitude": 40.7128}),  # Missing longitude
        "pathParameters": None,
        "queryStringParameters": None
    }
    
    context = MockContext()
    response = lambda_handler(event, context)
    print_response(response)
    
    return response


def test_invalid_coordinates():
    """Test error handling for invalid coordinates."""
    print("TEST 4: Invalid Coordinates (Error Handling)")
    print("-" * 80)
    
    event = create_lambda_event(
        latitude=100.0,  # Invalid latitude (> 90)
        longitude=-74.0060
    )
    
    context = MockContext()
    response = lambda_handler(event, context)
    print_response(response)
    
    return response


def test_cors_preflight():
    """Test CORS preflight OPTIONS request."""
    print("TEST 5: CORS Preflight (OPTIONS)")
    print("-" * 80)
    
    event = {
        "httpMethod": "OPTIONS",
        "headers": {"Content-Type": "application/json"},
        "body": None
    }
    
    context = MockContext()
    response = lambda_handler(event, context)
    print_response(response)
    
    return response


def main():
    """Run all test cases."""
    print("\n" + "="*80)
    print("GREENCHAIN AGENT - LOCAL TESTING")
    print("="*80)
    print("\nMake sure you have:")
    print("1. OPENROUTER_API_KEY in .env.local file (or as environment variable)")
    print("2. Installed all dependencies (uv pip install -r requirements.txt)")
    print("3. Have internet connection for satellite data and API calls")
    print("\n" + "="*80 + "\n")
    
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("WARNING: OPENROUTER_API_KEY environment variable is not set!")
        print("The LLM service will fail. Make sure it's in .env.local file:")
        print("  OPENROUTER_API_KEY=your-api-key-here")
        print("\nContinuing anyway to test satellite service...\n")
    else:
        print(f"✓ OPENROUTER_API_KEY loaded (length: {len(api_key)} characters)\n")
    
    try:
        # Run test cases
        test_basic_request()
        test_with_date_range()
        test_missing_parameters()
        test_invalid_coordinates()
        test_cors_preflight()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

