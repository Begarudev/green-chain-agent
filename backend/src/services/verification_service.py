"""
Verification Service for generating blockchain-verified Green Certificates.
Generates PDF certificates with simulated blockchain hashes for approved farms.
"""

import hashlib
import os
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import green, black, grey

def generate_blockchain_hash(farm_data: dict, llm_result: dict = None) -> str:
    """
    Simulates a blockchain transaction hash using SHA-256.
    In a real app, this would call the Caffeine AI / ICP Ledger.
    
    Args:
        farm_data: Dictionary containing NDVI score and farm details
        llm_result: Optional dictionary containing LLM analysis results
    
    Returns:
        Hex string representing the simulated blockchain transaction hash
    """
    # Create a unique string based on the data
    ndvi_score = farm_data.get('ndvi_score', 'unknown')
    status = farm_data.get('status', 'unknown')
    decision = llm_result.get('decision', 'unknown') if llm_result else 'unknown'
    timestamp = time.time()
    
    raw_data = f"{ndvi_score}{status}{decision}{timestamp}"
    # Hash it
    tx_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    return f"0x{tx_hash}"

def create_green_certificate(farm_data: dict, decision_data: dict, ledger_hash: str = None, latitude: float = None, longitude: float = None):
    """
    Generates a PDF certificate for approved farms.
    
    Args:
        farm_data: Dictionary containing NDVI score and farm details
        decision_data: Dictionary containing LLM analysis and decision
        ledger_hash: Optional pre-generated blockchain hash
        latitude: Optional farm latitude
        longitude: Optional farm longitude
    
    Returns:
        Tuple of (Path to PDF file, blockchain hash)
    """
    from pathlib import Path
    
    # Generate hash if not provided
    if ledger_hash is None:
        ledger_hash = generate_blockchain_hash(farm_data, decision_data)
    
    # Use placeholder coordinates if not provided
    if latitude is None:
        latitude = "N/A"
    if longitude is None:
        longitude = "N/A"
    
    # PDF Setup
    filename = f"GreenChain_Certificate_{int(time.time())}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)

    # --- DESIGN ---
    # Header
    c.setStrokeColor(green)
    c.setLineWidth(3)
    c.rect(30, 30, 550, 730) # Border

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(green)
    c.drawCentredString(300, 700, "GreenChain Verified")

    c.setFont("Helvetica", 12)
    c.setFillColor(black)
    c.drawCentredString(300, 670, "Sustainable Agriculture Certification")

    # Farm Details
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 600, "Farm Credential:")

    c.setFont("Helvetica", 14)
    c.drawString(120, 570, f"Location: {latitude}, {longitude}")
    c.drawString(120, 550, f"Vegetation Score (NDVI): {farm_data.get('ndvi_score', 'N/A')}")
    c.drawString(120, 530, f"Status: {farm_data.get('status', 'Unknown')}")
    c.drawString(120, 510, f"Date: {time.strftime('%Y-%m-%d')}")

    # AI Decision
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 450, "AI Risk Assessment:")
    c.setFont("Helvetica", 14)
    c.drawString(120, 420, f"Outcome: {decision_data['decision']}")
    c.drawString(120, 400, f"Confidence: {decision_data['confidence']}")

    # Blockchain Proof
    c.setStrokeColor(grey)
    c.line(100, 300, 500, 300)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 280, "Blockchain Verification Ledger (Simulated Caffeine AI):")
    c.setFont("Courier", 10)
    c.drawString(100, 260, ledger_hash)

    c.save()
    return Path(filename), ledger_hash