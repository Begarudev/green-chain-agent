"""
Satellite Service for fetching and processing Sentinel-2 data.
INCLUDES: Mock Mode for fast testing & Error Handling for 'NaN' values.
"""
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
import pystac_client
import stackstac
import xarray as xr
import numpy as np

# --- HACKATHON SETTINGS ---
# Set to True to skip downloading and return fake data (for testing Agent logic)
# Set to False when you want to record your demo video with real data.
MOCK_MODE = False 
# --------------------------

def get_farm_ndvi(
    lat: float,
    lon: float,
    date_range: Optional[Tuple[str, str]] = None
) -> Dict[str, Any]:
    
    print(f"\n[SATELLITE] 1. Request received for Lat: {lat}, Lon: {lon}")
    
    # --- 1. MOCK MODE (FAST PATH) ---
    if MOCK_MODE:
        print("[SATELLITE] ⚡ MOCK MODE ACTIVE: Skipping download for speed.")
        time.sleep(1) # Fake delay
        return {
            "ndvi_score": 0.72,
            "status": "Excellent (Mock Data)",
            "cloud_cover": 5.0,
            "acquisition_date": datetime.now().isoformat(),
            "process_time": "0.01s (Mock)"
        }

    # --- 2. REAL MODE (AWS S3) ---
    start_time = time.time()
    
    # Default to last 30 days
    if date_range is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60) # Extended to 60 days to find clear images
        date_range = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    start_str, end_str = date_range

    try:
        # Connect to Element84 Catalog
        catalog = pystac_client.Client.open("https://earth-search.aws.element84.com/v1")
        
        # Reduced Bounding Box (Only 200m radius) for speed
        bbox = [lon - 0.002, lat - 0.002, lon + 0.002, lat + 0.002]
        
        print("[SATELLITE] 2. Searching catalog...")
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=f"{start_str}/{end_str}",
            query={"eo:cloud_cover": {"lt": 20}}
        )
        
        items = list(search.items())
        print(f"[SATELLITE]    Found {len(items)} images.")
        
        if not items:
            print("[SATELLITE]    No images found. Returning Fallback.")
            return _get_fallback_data("No images found")
        
        # Sort by cloud cover
        best_item = sorted(items, key=lambda x: x.properties.get("eo:cloud_cover", 100))[0]
        
        print(f"[SATELLITE] 3. downloading {best_item.id}...")
        
        # RESOLUTION FIX: Must be tiny decimal for EPSG:4326 (degrees)
        # resolution=60 means 60 degrees per pixel (huge!), causing NaN
        # resolution=0.0001 ≈ 10 meters per pixel
        stack = stackstac.stack(
            [best_item],
            assets=["red", "nir"],
            resolution=0.0001,
            bounds_latlon=bbox,
            epsg=4326,
            chunksize=256 # Helps prevent memory locks
        )

        red = stack.sel(band="red")
        nir = stack.sel(band="nir")

        # Compute NDVI
        numerator = nir - red
        denominator = nir + red
        ndvi = xr.where(denominator != 0, numerator / denominator, 0)
        
        # .compute() triggers the actual download
        print("[SATELLITE] 4. Processing pixels...")
        ndvi_mean = float(ndvi.mean(skipna=True).compute().values)
        
        # --- NAN CHECK ---
        if np.isnan(ndvi_mean):
            print("[SATELLITE] ⚠️ Result was NaN. Using fallback simulation.")
            # This happens if the image was purely 'nodata' (black borders)
            # We return a 'simulated' score so the demo doesn't crash
            return _get_fallback_data("Computed NaN value")

        elapsed = round(time.time() - start_time, 2)
        print(f"[SATELLITE] 5. Done! NDVI: {ndvi_mean} ({elapsed}s)")

        # Status Logic
        if ndvi_mean > 0.5: status = "Healthy"
        elif ndvi_mean > 0.3: status = "Moderate"
        else: status = "Poor"

        return {
            "ndvi_score": round(ndvi_mean, 3),
            "status": status,
            "cloud_cover": best_item.properties.get("eo:cloud_cover", 0),
            "acquisition_date": best_item.datetime.isoformat(),
            "process_time": f"{elapsed}s"
        }

    except Exception as e:
        print(f"[SATELLITE] ERROR: {str(e)}")
        return _get_fallback_data(str(e))

def _get_fallback_data(reason: str):
    """Returns safe dummy data so the Agent doesn't crash during a demo."""
    return {
        "ndvi_score": 0.45, # A safe 'average' score
        "status": "Simulated (Data Error)",
        "error": reason,
        "note": "Real satellite data failed to load; using simulation for hackathon demo."
    }