"""
AWS Lambda entry point for GreenChain Agent.
Handles incoming requests and orchestrates the loan validation process.
"""

import json
import os
from typing import Dict, Any
from agents.credit_agent import process_loan_request


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Expected event structure:
    {
        "latitude": float,
        "longitude": float,
        "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} (optional),
        "user_request": str (optional)
    }
    
    Returns:
    {
        "statusCode": int,
        "body": str (JSON),
        "headers": dict
    }
    """
    # Set CORS headers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # In production, restrict this to your domain
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST, OPTIONS"
    }
    
    # Handle OPTIONS request for CORS preflight
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": headers,
            "body": ""
        }
    
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        # Extract required parameters
        latitude = body.get("latitude")
        longitude = body.get("longitude")
        
        if latitude is None or longitude is None:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "error": "Missing required parameters: latitude and longitude are required"
                })
            }
        
        # Extract optional parameters
        date_range = None
        if "date_range" in body:
            date_range_obj = body["date_range"]
            if isinstance(date_range_obj, dict):
                start = date_range_obj.get("start")
                end = date_range_obj.get("end")
                if start and end:
                    date_range = (start, end)
        
        user_request = body.get("user_request")
        
        # Process the loan request
        result = process_loan_request(
            latitude=float(latitude),
            longitude=float(longitude),
            date_range=date_range,
            user_request=user_request
        )
        
        # Check if there was an error in processing
        if "error" in result:
            status_code = 500
        else:
            status_code = 200
        
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(result)
        }
        
    except ValueError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "error": f"Invalid input: {str(e)}"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "error": f"Internal server error: {str(e)}"
            })
        }

