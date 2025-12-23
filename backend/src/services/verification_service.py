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

def generate_blockchain_hash(verification_payload):
    """
    Simulates a blockchain transaction hash using SHA-256.
    In a real app, this would call the Caffeine AI / ICP Ledger.
    """
    # Create a unique string based on the data
    farm_data = verification_payload["farm_data"]
    latitude = verification_payload.get("latitude", "unknown")
    longitude = verification_payload.get("longitude", "unknown")
    raw_data = f"{latitude}{longitude}{farm_data.get('ndvi_score', 'unknown')}{verification_payload.get('issued_at', time.time())}"
    # Hash it
    tx_hash = hashlib.sha256(raw_data.encode()).hexdigest()
    return f"0x{tx_hash}"

def create_green_certificate(farm_data, decision_data, ledger_hash, latitude, longitude):
    """
    Generates a PDF certificate for approved farms.
    """
    # PDF Setup
    from pathlib import Path
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
    return Path(filename)