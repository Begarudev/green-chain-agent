"""
Advanced Satellite Service for multi-temporal analysis and deforestation detection.
Implements defensible sustainability metrics with temporal NDVI trends.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# --- HACKATHON SETTINGS ---
MOCK_MODE = False
# --------------------------

try:
    import pystac_client
    import stackstac
    import xarray as xr
    SATELLITE_LIBS_AVAILABLE = True
except ImportError:
    SATELLITE_LIBS_AVAILABLE = False


def get_multi_temporal_ndvi(
    lat: float,
    lon: float,
    months_back: int = 6,
    polygon: Optional[List[List[float]]] = None
) -> Dict[str, Any]:
    """
    Fetch multi-temporal NDVI data over specified months.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        months_back: Number of months of historical data (default 6)
        polygon: Optional list of [lon, lat] coordinates defining farm boundary
    
    Returns:
        {
            "ndvi_trend": List of monthly NDVI values,
            "ndvi_current": Current NDVI score,
            "ndvi_average": Average over period,
            "ndvi_change": Change from first to last month,
            "trend_direction": "improving" | "stable" | "declining",
            "trend_score": 0-1 (higher = better/improving),
            "monthly_data": List of {month, ndvi, cloud_cover},
            "consistency_score": 0-1 (how consistent farming is),
            "process_time": str
        }
    """
    print(f"\n[ADV-SATELLITE] Multi-temporal analysis for ({lat}, {lon})")
    print(f"[ADV-SATELLITE] Analyzing {months_back} months of data...")
    
    if MOCK_MODE or not SATELLITE_LIBS_AVAILABLE:
        return _get_mock_temporal_data(months_back)
    
    start_time = time.time()
    monthly_data = []
    
    # Calculate bounding box (use polygon if provided, otherwise ~500m radius)
    if polygon and len(polygon) >= 3:
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        bbox = [min(lons), min(lats), max(lons), max(lats)]
        print(f"[ADV-SATELLITE] Using polygon boundary: {len(polygon)} points")
    else:
        bbox = [lon - 0.005, lat - 0.005, lon + 0.005, lat + 0.005]
    
    try:
        catalog = pystac_client.Client.open("https://earth-search.aws.element84.com/v1")
        
        end_date = datetime.now()
        
        # Fetch data for each month
        for month_offset in range(months_back - 1, -1, -1):
            month_end = end_date - timedelta(days=30 * month_offset)
            month_start = month_end - timedelta(days=30)
            
            month_label = month_start.strftime("%b %Y")
            print(f"[ADV-SATELLITE] Searching {month_label}...")
            
            try:
                search = catalog.search(
                    collections=["sentinel-2-l2a"],
                    bbox=bbox,
                    datetime=f"{month_start.strftime('%Y-%m-%d')}/{month_end.strftime('%Y-%m-%d')}",
                    query={"eo:cloud_cover": {"lt": 30}}
                )
                
                items = list(search.items())
                
                if items:
                    # Get best (lowest cloud cover) image
                    best_item = sorted(items, key=lambda x: x.properties.get("eo:cloud_cover", 100))[0]
                    
                    # Calculate NDVI for this image
                    stack = stackstac.stack(
                        [best_item],
                        assets=["red", "nir"],
                        resolution=0.0001,
                        bounds_latlon=bbox,
                        epsg=4326,
                        chunksize=256
                    )
                    
                    red = stack.sel(band="red")
                    nir = stack.sel(band="nir")
                    
                    numerator = nir - red
                    denominator = nir + red
                    ndvi = xr.where(denominator != 0, numerator / denominator, 0)
                    ndvi_mean = float(ndvi.mean(skipna=True).compute().values)
                    
                    if not np.isnan(ndvi_mean):
                        monthly_data.append({
                            "month": month_label,
                            "ndvi": round(ndvi_mean, 3),
                            "cloud_cover": best_item.properties.get("eo:cloud_cover", 0),
                            "date": best_item.datetime.isoformat()
                        })
                        print(f"[ADV-SATELLITE]   → NDVI: {ndvi_mean:.3f}")
                    else:
                        print(f"[ADV-SATELLITE]   → Skipped (NaN result)")
                else:
                    print(f"[ADV-SATELLITE]   → No clear images found")
                    
            except Exception as e:
                print(f"[ADV-SATELLITE]   → Error: {str(e)[:50]}")
                continue
        
        # If we got less than 3 months, use fallback
        if len(monthly_data) < 3:
            print("[ADV-SATELLITE] Insufficient data, using partial results with simulation")
            return _get_mock_temporal_data(months_back, partial_data=monthly_data)
        
        # Calculate trend metrics
        ndvi_values = [m["ndvi"] for m in monthly_data]
        ndvi_current = ndvi_values[-1] if ndvi_values else 0.5
        ndvi_average = np.mean(ndvi_values)
        ndvi_change = ndvi_values[-1] - ndvi_values[0] if len(ndvi_values) >= 2 else 0
        
        # Trend analysis
        if ndvi_change > 0.05:
            trend_direction = "improving"
            trend_score = min(1.0, 0.7 + ndvi_change)
        elif ndvi_change < -0.05:
            trend_direction = "declining"
            trend_score = max(0.2, 0.5 + ndvi_change)
        else:
            trend_direction = "stable"
            trend_score = 0.6
        
        # Consistency score (low variance = consistent farming)
        ndvi_std = np.std(ndvi_values)
        consistency_score = max(0, min(1.0, 1.0 - ndvi_std * 3))
        
        elapsed = round(time.time() - start_time, 2)
        print(f"[ADV-SATELLITE] Done! Trend: {trend_direction}, Change: {ndvi_change:.3f} ({elapsed}s)")
        
        return {
            "ndvi_trend": ndvi_values,
            "ndvi_current": round(ndvi_current, 3),
            "ndvi_average": round(ndvi_average, 3),
            "ndvi_change": round(ndvi_change, 3),
            "trend_direction": trend_direction,
            "trend_score": round(trend_score, 3),
            "monthly_data": monthly_data,
            "consistency_score": round(consistency_score, 3),
            "months_analyzed": len(monthly_data),
            "process_time": f"{elapsed}s"
        }
        
    except Exception as e:
        print(f"[ADV-SATELLITE] Error: {str(e)}")
        return _get_mock_temporal_data(months_back)


def check_deforestation(
    lat: float,
    lon: float,
    years_back: int = 2,
    polygon: Optional[List[List[float]]] = None
) -> Dict[str, Any]:
    """
    Check for recent deforestation activity using vegetation change detection.
    
    We compare current vegetation to historical baseline to detect sudden
    forest-to-agriculture conversion (a red flag for sustainability).
    
    Args:
        lat: Center latitude
        lon: Center longitude
        years_back: How many years to look back (default 2)
        polygon: Optional boundary polygon
    
    Returns:
        {
            "deforestation_detected": bool,
            "risk_level": "none" | "low" | "medium" | "high",
            "deforestation_score": 0-1 (0 = no deforestation, 1 = heavy clearing),
            "ndvi_historical": float (NDVI from years_back ago),
            "ndvi_recent": float (NDVI from recent),
            "change_detected": float (negative = vegetation loss),
            "analysis_period": str
        }
    """
    print(f"\n[DEFORESTATION] Checking for land clearing at ({lat}, {lon})")
    
    if MOCK_MODE or not SATELLITE_LIBS_AVAILABLE:
        return _get_mock_deforestation_data()
    
    start_time = time.time()
    
    # Bounding box
    if polygon and len(polygon) >= 3:
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        bbox = [min(lons), min(lats), max(lons), max(lats)]
    else:
        bbox = [lon - 0.005, lat - 0.005, lon + 0.005, lat + 0.005]
    
    try:
        catalog = pystac_client.Client.open("https://earth-search.aws.element84.com/v1")
        
        end_date = datetime.now()
        
        # Get historical NDVI (2 years ago)
        historical_start = end_date - timedelta(days=365 * years_back + 60)
        historical_end = end_date - timedelta(days=365 * years_back)
        
        print(f"[DEFORESTATION] Fetching historical data ({historical_start.strftime('%Y-%m')})...")
        
        ndvi_historical = _get_best_ndvi(catalog, bbox, historical_start, historical_end)
        
        # Get recent NDVI (last 2 months)
        recent_start = end_date - timedelta(days=60)
        recent_end = end_date
        
        print(f"[DEFORESTATION] Fetching recent data ({recent_start.strftime('%Y-%m')})...")
        
        ndvi_recent = _get_best_ndvi(catalog, bbox, recent_start, recent_end)
        
        if ndvi_historical is None or ndvi_recent is None:
            print("[DEFORESTATION] Insufficient data, using fallback")
            return _get_mock_deforestation_data()
        
        # Calculate change
        change = ndvi_recent - ndvi_historical
        
        # Interpret: Large negative change + historical was high = potential deforestation
        # (forest has NDVI > 0.6, cleared land has NDVI < 0.3)
        deforestation_detected = False
        if ndvi_historical > 0.5 and change < -0.2:
            deforestation_detected = True
            risk_level = "high"
            deforestation_score = min(1.0, abs(change) * 2)
        elif ndvi_historical > 0.4 and change < -0.15:
            risk_level = "medium"
            deforestation_score = min(0.7, abs(change) * 1.5)
        elif change < -0.1:
            risk_level = "low"
            deforestation_score = min(0.4, abs(change))
        else:
            risk_level = "none"
            deforestation_score = 0
        
        elapsed = round(time.time() - start_time, 2)
        print(f"[DEFORESTATION] Done! Risk: {risk_level}, Change: {change:.3f} ({elapsed}s)")
        
        return {
            "deforestation_detected": deforestation_detected,
            "risk_level": risk_level,
            "deforestation_score": round(deforestation_score, 3),
            "ndvi_historical": round(ndvi_historical, 3),
            "ndvi_recent": round(ndvi_recent, 3),
            "change_detected": round(change, 3),
            "analysis_period": f"{historical_start.strftime('%Y-%m')} to {recent_end.strftime('%Y-%m')}",
            "years_analyzed": years_back,
            "process_time": f"{elapsed}s"
        }
        
    except Exception as e:
        print(f"[DEFORESTATION] Error: {str(e)}")
        return _get_mock_deforestation_data()


def _get_best_ndvi(catalog, bbox, start_date, end_date) -> Optional[float]:
    """Helper to get best NDVI for a date range."""
    try:
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}",
            query={"eo:cloud_cover": {"lt": 30}}
        )
        
        items = list(search.items())
        if not items:
            return None
        
        best_item = sorted(items, key=lambda x: x.properties.get("eo:cloud_cover", 100))[0]
        
        stack = stackstac.stack(
            [best_item],
            assets=["red", "nir"],
            resolution=0.0001,
            bounds_latlon=bbox,
            epsg=4326,
            chunksize=256
        )
        
        red = stack.sel(band="red")
        nir = stack.sel(band="nir")
        
        numerator = nir - red
        denominator = nir + red
        ndvi = xr.where(denominator != 0, numerator / denominator, 0)
        ndvi_mean = float(ndvi.mean(skipna=True).compute().values)
        
        return ndvi_mean if not np.isnan(ndvi_mean) else None
        
    except Exception:
        return None


def calculate_sustainability_score(
    temporal_data: Dict[str, Any],
    deforestation_data: Dict[str, Any],
    weather_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate a comprehensive, defensible sustainability score.
    
    Uses transparent weighted scoring that can be explained:
    - 30% NDVI trend (improving farming practices)
    - 20% NDVI consistency (stable farming patterns)
    - 25% Deforestation (no recent clearing)
    - 25% Climate resilience (weather adaptation)
    
    Returns:
        {
            "overall_score": 0-100,
            "grade": "A" | "B" | "C" | "D" | "F",
            "component_scores": {
                "trend_score": 0-100,
                "consistency_score": 0-100,
                "deforestation_score": 0-100,
                "climate_score": 0-100
            },
            "weights": {...},
            "interpretation": str,
            "risk_factors": List[str],
            "positive_factors": List[str]
        }
    """
    # Extract component values
    trend_raw = temporal_data.get("trend_score", 0.5)
    consistency_raw = temporal_data.get("consistency_score", 0.5)
    deforestation_raw = 1 - deforestation_data.get("deforestation_score", 0)  # Invert: 0 deforestation = good
    climate_raw = 1 - weather_data.get("weather_risk_score", 0.5)  # Invert: low risk = good
    
    # Convert to 0-100 scale
    trend_score = int(trend_raw * 100)
    consistency_score = int(consistency_raw * 100)
    deforestation_score = int(deforestation_raw * 100)
    climate_score = int(climate_raw * 100)
    
    # Weighted calculation
    weights = {
        "trend": 0.30,
        "consistency": 0.20,
        "deforestation": 0.25,
        "climate": 0.25
    }
    
    overall_score = (
        trend_score * weights["trend"] +
        consistency_score * weights["consistency"] +
        deforestation_score * weights["deforestation"] +
        climate_score * weights["climate"]
    )
    
    # Assign grade
    if overall_score >= 80:
        grade = "A"
        interpretation = "Excellent sustainability practices"
    elif overall_score >= 65:
        grade = "B"
        interpretation = "Good sustainability with minor concerns"
    elif overall_score >= 50:
        grade = "C"
        interpretation = "Average sustainability, improvements possible"
    elif overall_score >= 35:
        grade = "D"
        interpretation = "Below average, significant concerns"
    else:
        grade = "F"
        interpretation = "Poor sustainability, high risk"
    
    # Identify risk and positive factors
    risk_factors = []
    positive_factors = []
    
    if trend_score < 40:
        risk_factors.append("Declining vegetation health over time")
    elif trend_score > 70:
        positive_factors.append("Improving vegetation health trend")
    
    if consistency_score < 40:
        risk_factors.append("Inconsistent farming patterns")
    elif consistency_score > 70:
        positive_factors.append("Consistent and stable land management")
    
    if deforestation_score < 50:
        risk_factors.append("Potential recent deforestation detected")
    elif deforestation_score > 80:
        positive_factors.append("No signs of recent deforestation")
    
    if climate_score < 40:
        risk_factors.append("High climate/weather risk exposure")
    elif climate_score > 70:
        positive_factors.append("Favorable climate conditions")
    
    return {
        "overall_score": round(overall_score),
        "grade": grade,
        "component_scores": {
            "trend_score": trend_score,
            "consistency_score": consistency_score,
            "deforestation_score": deforestation_score,
            "climate_score": climate_score
        },
        "weights": weights,
        "interpretation": interpretation,
        "risk_factors": risk_factors,
        "positive_factors": positive_factors
    }


def calculate_loan_risk_score(
    sustainability: Dict[str, Any],
    loan_amount: float = 500,
    purpose: str = ""
) -> Dict[str, Any]:
    """
    Calculate structured loan risk score with transparent methodology.
    
    Args:
        sustainability: Output from calculate_sustainability_score
        loan_amount: Requested loan amount in USD
        purpose: Loan purpose description
    
    Returns:
        {
            "risk_score": 0-100 (lower = less risky),
            "approval_likelihood": "high" | "medium" | "low",
            "suggested_interest_rate": float,
            "max_recommended_amount": float,
            "decision_factors": List[str]
        }
    """
    sustainability_score = sustainability.get("overall_score", 50)
    
    # Base risk (inverse of sustainability)
    base_risk = 100 - sustainability_score
    
    # Loan amount factor (higher amounts = more risk)
    if loan_amount <= 500:
        amount_risk = 0
    elif loan_amount <= 2000:
        amount_risk = 10
    elif loan_amount <= 5000:
        amount_risk = 20
    else:
        amount_risk = 30
    
    # Purpose factor (sustainable purposes reduce risk)
    sustainable_keywords = ["irrigation", "organic", "solar", "conservation", "drip", "sustainable", "renewable"]
    purpose_lower = purpose.lower()
    sustainable_purpose = any(kw in purpose_lower for kw in sustainable_keywords)
    purpose_adjustment = -10 if sustainable_purpose else 0
    
    # Final risk score
    risk_score = max(0, min(100, base_risk + amount_risk + purpose_adjustment))
    
    # Determine approval likelihood
    if risk_score <= 30:
        approval_likelihood = "high"
        suggested_rate = 0.08  # 8%
        max_amount = min(loan_amount * 2, 10000)
    elif risk_score <= 50:
        approval_likelihood = "medium"
        suggested_rate = 0.12  # 12%
        max_amount = loan_amount * 1.2
    elif risk_score <= 70:
        approval_likelihood = "low"
        suggested_rate = 0.18  # 18%
        max_amount = loan_amount * 0.7
    else:
        approval_likelihood = "very_low"
        suggested_rate = 0.25  # 25% or rejection
        max_amount = loan_amount * 0.3
    
    # Decision factors
    decision_factors = []
    decision_factors.append(f"Sustainability score: {sustainability_score}/100 ({sustainability.get('grade', 'N/A')})")
    
    if sustainability.get("risk_factors"):
        for factor in sustainability["risk_factors"]:
            decision_factors.append(f"⚠️ {factor}")
    
    if sustainability.get("positive_factors"):
        for factor in sustainability["positive_factors"]:
            decision_factors.append(f"✓ {factor}")
    
    if sustainable_purpose:
        decision_factors.append("✓ Sustainable loan purpose (rate reduction applied)")
    
    return {
        "risk_score": round(risk_score),
        "approval_likelihood": approval_likelihood,
        "suggested_interest_rate": suggested_rate,
        "suggested_interest_rate_pct": f"{suggested_rate * 100:.0f}%",
        "max_recommended_amount": round(max_amount, 2),
        "decision_factors": decision_factors
    }


# ============================================================================
# Mock Data Functions
# ============================================================================

def _get_mock_temporal_data(months: int, partial_data: List = None) -> Dict[str, Any]:
    """Generate realistic mock temporal data."""
    import random
    
    if partial_data and len(partial_data) > 0:
        # Extend partial data
        monthly_data = partial_data
    else:
        # Generate full mock data
        monthly_data = []
        base_ndvi = random.uniform(0.4, 0.7)
        trend = random.choice([-0.02, 0, 0.01, 0.02, 0.03])  # Slight trend
        
        end_date = datetime.now()
        for i in range(months - 1, -1, -1):
            month_date = end_date - timedelta(days=30 * i)
            ndvi = base_ndvi + trend * (months - i - 1) + random.uniform(-0.05, 0.05)
            ndvi = max(0.1, min(0.9, ndvi))  # Clamp
            monthly_data.append({
                "month": month_date.strftime("%b %Y"),
                "ndvi": round(ndvi, 3),
                "cloud_cover": random.uniform(5, 25),
                "date": month_date.isoformat()
            })
    
    ndvi_values = [m["ndvi"] for m in monthly_data]
    ndvi_change = ndvi_values[-1] - ndvi_values[0] if len(ndvi_values) >= 2 else 0
    
    if ndvi_change > 0.03:
        trend_direction = "improving"
        trend_score = min(1.0, 0.7 + ndvi_change)
    elif ndvi_change < -0.03:
        trend_direction = "declining"
        trend_score = max(0.2, 0.5 + ndvi_change)
    else:
        trend_direction = "stable"
        trend_score = 0.6
    
    consistency_score = max(0, min(1.0, 1.0 - np.std(ndvi_values) * 3))
    
    return {
        "ndvi_trend": ndvi_values,
        "ndvi_current": round(ndvi_values[-1], 3) if ndvi_values else 0.5,
        "ndvi_average": round(np.mean(ndvi_values), 3),
        "ndvi_change": round(ndvi_change, 3),
        "trend_direction": trend_direction,
        "trend_score": round(trend_score, 3),
        "monthly_data": monthly_data,
        "consistency_score": round(consistency_score, 3),
        "months_analyzed": len(monthly_data),
        "process_time": "0.5s (simulated)",
        "is_mock": True
    }


def _get_mock_deforestation_data() -> Dict[str, Any]:
    """Generate mock deforestation data (usually no deforestation)."""
    import random
    
    # Most farms should NOT have deforestation
    has_deforestation = random.random() < 0.15  # 15% chance
    
    if has_deforestation:
        return {
            "deforestation_detected": True,
            "risk_level": random.choice(["medium", "high"]),
            "deforestation_score": round(random.uniform(0.4, 0.8), 3),
            "ndvi_historical": round(random.uniform(0.6, 0.8), 3),
            "ndvi_recent": round(random.uniform(0.2, 0.4), 3),
            "change_detected": round(random.uniform(-0.4, -0.2), 3),
            "analysis_period": "2023-01 to 2024-12",
            "years_analyzed": 2,
            "process_time": "0.3s (simulated)",
            "is_mock": True
        }
    else:
        return {
            "deforestation_detected": False,
            "risk_level": "none",
            "deforestation_score": round(random.uniform(0, 0.15), 3),
            "ndvi_historical": round(random.uniform(0.4, 0.6), 3),
            "ndvi_recent": round(random.uniform(0.45, 0.65), 3),
            "change_detected": round(random.uniform(-0.05, 0.1), 3),
            "analysis_period": "2023-01 to 2024-12",
            "years_analyzed": 2,
            "process_time": "0.3s (simulated)",
            "is_mock": True
        }
