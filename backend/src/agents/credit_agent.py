"""
Credit Agent - Main logic controller for the GreenChain Agent system.
Orchestrates satellite data fetching and LLM-based loan risk analysis.
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from services.satellite_service import get_farm_ndvi
from services.llm_service import analyze_loan_risk


def process_loan_request(
    latitude: float,
    longitude: float,
    date_range: Optional[Tuple[str, str]] = None,
    user_request: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to process a loan request for a farm.
    
    This function:
    1. Fetches satellite data and calculates NDVI
    2. Analyzes loan risk using LLM
    3. Returns comprehensive loan decision
    
    Args:
        latitude: Farm latitude
        longitude: Farm longitude
        date_range: Optional tuple of (start_date, end_date) in 'YYYY-MM-DD' format
        user_request: Optional user-provided context or request details
    
    Returns:
        Dictionary containing complete loan analysis:
        {
            "farm_location": {"lat": float, "lon": float},
            "satellite_data": {...},
            "loan_analysis": {...},
            "timestamp": str,
            "request_id": str (optional)
        }
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Invalid longitude: {longitude}. Must be between -180 and 180.")
    
    # Step 1: Fetch satellite data and calculate NDVI
    try:
        satellite_data = get_farm_ndvi(latitude, longitude, date_range)
    except Exception as e:
        return {
            "error": f"Failed to fetch satellite data: {str(e)}",
            "farm_location": {"lat": latitude, "lon": longitude},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Step 2: Analyze loan risk using LLM
    try:
        loan_analysis = analyze_loan_risk(satellite_data, user_request)
    except Exception as e:
        return {
            "error": f"Failed to analyze loan risk: {str(e)}",
            "farm_location": {"lat": latitude, "lon": longitude},
            "satellite_data": satellite_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Step 3: Compile comprehensive response
    response = {
        "farm_location": {
            "latitude": latitude,
            "longitude": longitude
        },
        "satellite_data": satellite_data,
        "loan_analysis": loan_analysis,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return response

