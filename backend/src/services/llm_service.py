"""
LLM Service for analyzing loan risk using OpenRouter API (Claude 3.5 Sonnet).
"""

import os
import requests
from typing import Dict, Any, Optional


def analyze_loan_risk(
    farm_data: Dict[str, Any],
    user_request: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze loan risk based on farm NDVI data using OpenRouter API.
    
    Args:
        farm_data: Dictionary containing NDVI score and status from satellite_service
        user_request: Optional user-provided context or request details
    
    Returns:
        Dictionary containing loan decision and analysis:
        {
            "decision": str,  # "APPROVED" or "REJECTED"
            "reasoning": str,
            "confidence": float,
            "recommendations": list[str]
        }
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is not set")
    
    # Prepare the system prompt
    system_prompt = (
        "You are a Sustainable Credit Officer specializing in agricultural micro-loans. "
        "Analyze the NDVI (Normalized Difference Vegetation Index) data provided. "
        "If NDVI > 0.5, approve the loan as the farm shows healthy vegetation. "
        "If NDVI < 0.3, reject the loan as the farm shows poor vegetation health. "
        "For values between 0.3 and 0.5, provide a conditional approval with recommendations. "
        "Be concise and professional in your analysis. "
        "Always provide: decision (APPROVED/REJECTED/CONDITIONAL), reasoning, confidence (0-1), and recommendations."
    )
    
    # Prepare user message with farm data
    ndvi_score = farm_data.get("ndvi_score", 0.0)
    status = farm_data.get("status", "Unknown")
    cloud_cover = farm_data.get("cloud_cover", None)
    acquisition_date = farm_data.get("acquisition_date", None)
    
    user_message = f"""Farm Sustainability Analysis Request:

NDVI Score: {ndvi_score}
Vegetation Status: {status}
Cloud Cover: {cloud_cover}% (if available)
Acquisition Date: {acquisition_date} (if available)

{f'Additional Context: {user_request}' if user_request else ''}

Please analyze this farm's sustainability and provide a loan decision."""
    
    # Make request to OpenRouter API
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://greenchain-agent.com",  # Optional: for tracking
        "X-Title": "GreenChain Agent"  # Optional: for tracking
    }
    
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3,  # Lower temperature for more consistent, factual responses
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the assistant's message
        assistant_message = result["choices"][0]["message"]["content"]
        
        # Parse the response (simple extraction - in production, you might want more robust parsing)
        # For now, we'll return the raw response and extract decision keywords
        decision = "CONDITIONAL"
        if "APPROVED" in assistant_message.upper() or "APPROVE" in assistant_message.upper():
            decision = "APPROVED"
        elif "REJECTED" in assistant_message.upper() or "REJECT" in assistant_message.upper():
            decision = "REJECTED"
        
        # Try to extract confidence if mentioned
        confidence = 0.7  # Default confidence
        if "confidence" in assistant_message.lower():
            # Simple extraction - could be improved
            import re
            conf_match = re.search(r'confidence[:\s]+([0-9.]+)', assistant_message.lower())
            if conf_match:
                confidence = float(conf_match.group(1))
                if confidence > 1.0:
                    confidence = confidence / 100.0
        
        return {
            "decision": decision,
            "reasoning": assistant_message,
            "confidence": confidence,
            "raw_response": assistant_message,
            "model_used": result.get("model", "anthropic/claude-3.5-sonnet")
        }
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to communicate with OpenRouter API: {str(e)}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response format from OpenRouter API: {str(e)}")

