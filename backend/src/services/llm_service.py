"""
LLM Service for analyzing loan risk using Google Gemini API.
"""

import os
import requests
import random
from typing import Dict, Any, Optional

# --- MOCK MODE ---
# Set to True to skip API calls and return mock responses (for testing)
MOCK_MODE = False


def analyze_loan_risk(
    farm_data: Dict[str, Any],
    user_request: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze loan risk based on farm NDVI data using Google Gemini API.

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

    # --- MOCK MODE (FAST PATH) ---
    if MOCK_MODE:
        print("[LLM] ⚡ MOCK MODE ACTIVE: Skipping API call for speed.")
        ndvi_score = farm_data.get("ndvi_score", 0.5)
        weather = farm_data.get("weather", {})
        weather_risk = weather.get("weather_risk_score", 0.3) if weather else 0.3

        # Generate mock decision based on NDVI score AND weather risk
        composite_score = (ndvi_score * 0.6) + ((1 - weather_risk) * 0.4)
        
        if composite_score > 0.6:
            decision = "APPROVED"
            reasoning = f"Excellent conditions detected. Vegetation health shows NDVI of {ndvi_score:.2f} indicating strong crop growth. Weather analysis shows favorable conditions with {weather.get('weather_status', 'moderate')} climate patterns. The farm demonstrates sustainable practices suitable for micro-loan approval."
            confidence = min(0.95, 0.75 + composite_score * 0.2)
        elif composite_score > 0.4:
            decision = "CONDITIONAL"
            reasoning = f"Moderate conditions observed. NDVI score of {ndvi_score:.2f} shows acceptable vegetation health. Weather risk is {weather_risk:.0%}. Conditional approval recommended with monitoring of climate factors and implementation of risk mitigation strategies."
            confidence = 0.70 + composite_score * 0.1
        else:
            decision = "REJECTED"
            reasoning = f"Risk factors detected. NDVI score of {ndvi_score:.2f} indicates vegetation stress. Weather conditions show {weather_risk:.0%} risk level. Recommend improving farming practices and reapplying after conditions stabilize."
            confidence = 0.60 + (1 - composite_score) * 0.2

        return {
            "decision": decision,
            "reasoning": reasoning,
            "confidence": round(confidence, 2),
            "raw_response": reasoning,
            "model_used": "mock-gemini-pro",
            "composite_score": round(composite_score, 3),
            "recommendations": [
                "Implement drought-resistant farming techniques",
                "Consider crop diversification",
                "Install weather monitoring systems"
            ] if decision != "APPROVED" else []
        }

    # --- REAL MODE (API CALL) ---
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    # Prepare the prompt for Gemini
    ndvi_score = farm_data.get("ndvi_score", 0.0)
    status = farm_data.get("status", "Unknown")
    cloud_cover = farm_data.get("cloud_cover", None)
    acquisition_date = farm_data.get("acquisition_date", None)
    
    # Extract weather data if available
    weather = farm_data.get("weather", {})
    weather_section = ""
    if weather and not weather.get("error"):
        weather_section = f"""
Weather & Climate Data (Last {weather.get('data_period', {}).get('days', 90)} days):
- Total Rainfall: {weather.get('rainfall_total_mm', 'N/A')} mm
- Average Daily Rainfall: {weather.get('rainfall_avg_daily_mm', 'N/A')} mm
- Temperature Range: {weather.get('temperature_min_c', 'N/A')}°C to {weather.get('temperature_max_c', 'N/A')}°C
- Average Temperature: {weather.get('temperature_avg_c', 'N/A')}°C
- Drought Risk Score: {weather.get('drought_risk_score', 'N/A')} (0-1 scale)
- Frost Days: {weather.get('frost_days', 'N/A')}
- Growing Degree Days: {weather.get('growing_degree_days', 'N/A')}
- Weather Risk Score: {weather.get('weather_risk_score', 'N/A')} (0-1 scale, lower is better)
- Weather Status: {weather.get('weather_status', 'Unknown')}
"""

    prompt = f"""You are a Sustainable Credit Officer specializing in agricultural micro-loans.

Analyze the satellite vegetation data AND weather/climate data provided to make a comprehensive loan decision.

Farm Satellite Data:
- NDVI Score: {ndvi_score} (Normalized Difference Vegetation Index, 0-1 scale)
- Vegetation Status: {status}
{f'- Cloud Cover: {cloud_cover}%' if cloud_cover else ''}
{f'- Satellite Image Date: {acquisition_date}' if acquisition_date else ''}
{weather_section}
{f'Loan Purpose: {user_request}' if user_request else ''}

Decision Guidelines:
- Consider BOTH vegetation health (NDVI) AND weather conditions
- If NDVI > 0.5 AND weather_risk < 0.4, strongly consider APPROVAL
- If NDVI < 0.3 OR weather shows severe drought/frost risk, consider REJECTION
- For borderline cases, provide CONDITIONAL approval with specific recommendations
- Factor in drought risk, frost days, and rainfall adequacy

Provide your analysis in this exact format:
DECISION: [APPROVED/REJECTED/CONDITIONAL]
CONFIDENCE: [0-1 decimal]
REASONING: [Your detailed analysis covering both vegetation and climate factors]
RECOMMENDATIONS: [List any recommendations, or "None" if approved]"""

    # Make request to Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 500,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Extract the generated text from Gemini response
        if "candidates" in result and len(result["candidates"]) > 0:
            assistant_message = result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise RuntimeError("No content generated by Gemini API")

        # Parse the response to extract decision, confidence, reasoning, and recommendations
        lines = assistant_message.strip().split('\n')
        decision = "CONDITIONAL"
        confidence = 0.7
        reasoning = assistant_message
        recommendations = []

        for line in lines:
            line = line.strip()
            if line.upper().startswith('DECISION:'):
                decision_text = line.split(':', 1)[1].strip().upper()
                if 'APPROVED' in decision_text:
                    decision = 'APPROVED'
                elif 'REJECTED' in decision_text:
                    decision = 'REJECTED'
                elif 'CONDITIONAL' in decision_text:
                    decision = 'CONDITIONAL'
            elif line.upper().startswith('CONFIDENCE:'):
                try:
                    conf_value = float(line.split(':', 1)[1].strip())
                    if conf_value > 1.0:
                        conf_value = conf_value / 100.0
                    confidence = conf_value
                except (ValueError, IndexError):
                    pass
            elif line.upper().startswith('RECOMMENDATIONS:'):
                rec_text = line.split(':', 1)[1].strip()
                if rec_text.lower() != 'none' and rec_text:
                    # Split recommendations if they appear as a list
                    recommendations = [r.strip('- ').strip() for r in rec_text.split('\n') if r.strip()]

        return {
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "raw_response": assistant_message,
            "model_used": "gemini-pro",
            "recommendations": recommendations
        }

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to communicate with Gemini API: {str(e)}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response format from Gemini API: {str(e)}")

