"""
Weather Service for fetching historical weather and climate data.
Uses Open-Meteo API (free, no API key required) for weather analysis.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import statistics

# --- MOCK MODE ---
MOCK_MODE = False


def get_weather_analysis(
    lat: float,
    lon: float,
    days_back: int = 90
) -> Dict[str, Any]:
    """
    Fetch historical weather data and calculate agricultural risk metrics.
    
    Args:
        lat: Latitude of the farm
        lon: Longitude of the farm
        days_back: Number of days of historical data to fetch (default 90)
    
    Returns:
        Dictionary containing:
        {
            "rainfall_total_mm": float,
            "rainfall_avg_daily_mm": float,
            "drought_risk_score": float (0-1, higher = more risk),
            "temperature_avg_c": float,
            "temperature_max_c": float,
            "temperature_min_c": float,
            "growing_degree_days": float,
            "frost_days": int,
            "weather_risk_score": float (0-1, lower = better),
            "weather_status": str,
            "data_period": dict
        }
    """
    print(f"\n[WEATHER] 1. Request received for Lat: {lat}, Lon: {lon}")
    
    # --- MOCK MODE (FAST PATH) ---
    if MOCK_MODE:
        print("[WEATHER] ⚡ MOCK MODE ACTIVE: Returning simulated data.")
        return _get_mock_weather_data()
    
    # --- REAL MODE (Open-Meteo API) ---
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Open-Meteo Historical Weather API (free, no key required)
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min", 
                "temperature_2m_mean",
                "precipitation_sum",
                "et0_fao_evapotranspiration"  # Reference evapotranspiration
            ],
            "timezone": "auto"
        }
        
        print("[WEATHER] 2. Calling Open-Meteo API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        
        # Extract data arrays
        temps_max = [t for t in daily.get("temperature_2m_max", []) if t is not None]
        temps_min = [t for t in daily.get("temperature_2m_min", []) if t is not None]
        temps_mean = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
        precipitation = [p for p in daily.get("precipitation_sum", []) if p is not None]
        evapotranspiration = [e for e in daily.get("et0_fao_evapotranspiration", []) if e is not None]
        
        if not temps_mean or not precipitation:
            print("[WEATHER] ⚠️ Insufficient data returned")
            return _get_fallback_weather_data("Insufficient historical data")
        
        print(f"[WEATHER] 3. Processing {len(temps_mean)} days of data...")
        
        # Calculate metrics
        rainfall_total = sum(precipitation)
        rainfall_avg = statistics.mean(precipitation) if precipitation else 0
        temp_avg = statistics.mean(temps_mean)
        temp_max = max(temps_max) if temps_max else temp_avg
        temp_min = min(temps_min) if temps_min else temp_avg
        
        # Count frost days (min temp below 0°C)
        frost_days = sum(1 for t in temps_min if t < 0)
        
        # Calculate Growing Degree Days (base 10°C for most crops)
        gdd = sum(max(0, t - 10) for t in temps_mean)
        
        # Calculate drought risk using precipitation vs evapotranspiration
        total_et = sum(evapotranspiration) if evapotranspiration else rainfall_total
        if total_et > 0:
            water_balance = rainfall_total / total_et
            # Drought risk: if rainfall < evapotranspiration, risk increases
            drought_risk = max(0, min(1, 1 - water_balance))
        else:
            drought_risk = 0.5  # Unknown
        
        # Calculate overall weather risk score (0-1, lower is better)
        weather_risk = _calculate_weather_risk(
            rainfall_total, days_back, temp_avg, frost_days, drought_risk
        )
        
        # Determine status
        if weather_risk < 0.3:
            weather_status = "Favorable"
        elif weather_risk < 0.5:
            weather_status = "Moderate"
        elif weather_risk < 0.7:
            weather_status = "Challenging"
        else:
            weather_status = "High Risk"
        
        print(f"[WEATHER] 4. Done! Weather Risk: {weather_risk:.2f} ({weather_status})")
        
        return {
            "rainfall_total_mm": round(rainfall_total, 1),
            "rainfall_avg_daily_mm": round(rainfall_avg, 2),
            "drought_risk_score": round(drought_risk, 3),
            "temperature_avg_c": round(temp_avg, 1),
            "temperature_max_c": round(temp_max, 1),
            "temperature_min_c": round(temp_min, 1),
            "growing_degree_days": round(gdd, 0),
            "frost_days": frost_days,
            "weather_risk_score": round(weather_risk, 3),
            "weather_status": weather_status,
            "data_period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "days": days_back
            }
        }
        
    except requests.exceptions.RequestException as e:
        print(f"[WEATHER] ERROR: {str(e)}")
        return _get_fallback_weather_data(str(e))
    except Exception as e:
        print(f"[WEATHER] ERROR: {str(e)}")
        return _get_fallback_weather_data(str(e))


def _calculate_weather_risk(
    rainfall_mm: float,
    days: int,
    avg_temp: float,
    frost_days: int,
    drought_risk: float
) -> float:
    """
    Calculate composite weather risk score.
    
    Components:
    - Rainfall adequacy (too little or too much is bad)
    - Temperature extremes
    - Frost damage risk
    - Drought conditions
    """
    risk_scores = []
    
    # 1. Rainfall adequacy (ideal: 2-6mm per day for most crops)
    daily_rainfall = rainfall_mm / days if days > 0 else 0
    if daily_rainfall < 1:
        rainfall_risk = 0.8  # Too dry
    elif daily_rainfall < 2:
        rainfall_risk = 0.4
    elif daily_rainfall <= 6:
        rainfall_risk = 0.1  # Ideal
    elif daily_rainfall <= 10:
        rainfall_risk = 0.4
    else:
        rainfall_risk = 0.7  # Too wet / flooding risk
    risk_scores.append(rainfall_risk * 0.25)
    
    # 2. Temperature risk (ideal: 15-30°C for most crops)
    if 15 <= avg_temp <= 30:
        temp_risk = 0.1
    elif 10 <= avg_temp < 15 or 30 < avg_temp <= 35:
        temp_risk = 0.3
    elif 5 <= avg_temp < 10 or 35 < avg_temp <= 40:
        temp_risk = 0.6
    else:
        temp_risk = 0.9
    risk_scores.append(temp_risk * 0.2)
    
    # 3. Frost risk
    frost_ratio = frost_days / days if days > 0 else 0
    frost_risk = min(1.0, frost_ratio * 5)  # More than 20% frost days = max risk
    risk_scores.append(frost_risk * 0.2)
    
    # 4. Drought risk (already 0-1)
    risk_scores.append(drought_risk * 0.35)
    
    return sum(risk_scores)


def _get_mock_weather_data() -> Dict[str, Any]:
    """Returns mock weather data for testing."""
    return {
        "rainfall_total_mm": 185.5,
        "rainfall_avg_daily_mm": 2.06,
        "drought_risk_score": 0.25,
        "temperature_avg_c": 22.5,
        "temperature_max_c": 35.2,
        "temperature_min_c": 12.1,
        "growing_degree_days": 1125,
        "frost_days": 0,
        "weather_risk_score": 0.22,
        "weather_status": "Favorable",
        "data_period": {
            "start": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
            "end": datetime.now().strftime("%Y-%m-%d"),
            "days": 90
        },
        "note": "Mock data for testing"
    }


def _get_fallback_weather_data(reason: str) -> Dict[str, Any]:
    """Returns fallback data when API fails."""
    return {
        "rainfall_total_mm": None,
        "drought_risk_score": 0.5,
        "temperature_avg_c": None,
        "weather_risk_score": 0.5,
        "weather_status": "Unknown (Data Error)",
        "error": reason,
        "note": "Weather data unavailable; using neutral risk score"
    }


def get_climate_summary(lat: float, lon: float) -> str:
    """
    Generate a human-readable climate summary for the AI agent.
    """
    weather = get_weather_analysis(lat, lon)
    
    if weather.get("error"):
        return f"Weather data unavailable: {weather['error']}"
    
    summary = f"""
Climate Analysis (Last {weather['data_period']['days']} days):
- Total Rainfall: {weather['rainfall_total_mm']}mm ({weather['rainfall_avg_daily_mm']}mm/day avg)
- Temperature Range: {weather['temperature_min_c']}°C to {weather['temperature_max_c']}°C (avg: {weather['temperature_avg_c']}°C)
- Drought Risk: {weather['drought_risk_score']:.0%}
- Frost Days: {weather['frost_days']}
- Growing Degree Days: {weather['growing_degree_days']}
- Overall Weather Risk: {weather['weather_risk_score']:.0%} ({weather['weather_status']})
"""
    return summary.strip()
