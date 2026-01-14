"""
Analytics Service for portfolio analysis, regional trends, and reporting.

Provides analytics functions for the banker terminal command interface.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

# Data storage path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
APPLICATIONS_FILE = DATA_DIR / "applications.json"


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_applications() -> List[Dict[str, Any]]:
    """Load historical applications from JSON file."""
    ensure_data_dir()
    
    if not APPLICATIONS_FILE.exists():
        return []
    
    try:
        with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Analytics] Error loading applications: {str(e)}")
        return []


def save_application(application: Dict[str, Any]):
    """Save a new application to the JSON file."""
    ensure_data_dir()
    
    applications = load_applications()
    
    # Add timestamp if not present
    if "timestamp" not in application:
        application["timestamp"] = datetime.now().isoformat()
    
    # Add ID if not present
    if "id" not in application:
        application["id"] = f"GCH-{datetime.now().strftime('%Y')}-{len(applications) + 1:06d}"
    
    applications.append(application)
    
    try:
        with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(applications, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Analytics] Error saving application: {str(e)}")


def get_portfolio_stats() -> Dict[str, Any]:
    """Calculate portfolio-wide statistics."""
    applications = load_applications()
    
    if not applications:
        return {
            "total_applications": 0,
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "conditional": 0,
            "total_disbursed": 0,
            "avg_sustainability": 0,
            "avg_risk_score": 0,
            "green_compliance_rate": 0
        }
    
    total = len(applications)
    status_counts = defaultdict(int)
    total_disbursed = 0
    sustainability_scores = []
    risk_scores = []
    green_count = 0
    
    for app in applications:
        status = app.get("status", "PENDING").upper()
        status_counts[status] += 1
        
        if status == "APPROVED":
            total_disbursed += app.get("loan_amount", 0)
        
        sust_score = app.get("sustainability_score", 0)
        if sust_score > 0:
            sustainability_scores.append(sust_score)
        
        risk_score = app.get("risk_score", 0)
        if risk_score > 0:
            risk_scores.append(risk_score)
        
        if sust_score >= 70:
            green_count += 1
    
    return {
        "total_applications": total,
        "pending": status_counts.get("PENDING", 0),
        "approved": status_counts.get("APPROVED", 0),
        "rejected": status_counts.get("REJECTED", 0),
        "conditional": status_counts.get("CONDITIONAL", 0),
        "total_disbursed": total_disbursed,
        "avg_sustainability": sum(sustainability_scores) / len(sustainability_scores) if sustainability_scores else 0,
        "avg_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
        "green_compliance_rate": (green_count / total * 100) if total > 0 else 0
    }


def get_regional_analysis(region: Optional[str] = None) -> Dict[str, Any]:
    """Analyze applications by region."""
    applications = load_applications()
    
    if not applications:
        return {"regions": {}, "total": 0}
    
    region_stats = defaultdict(lambda: {
        "count": 0,
        "approved": 0,
        "total_amount": 0,
        "avg_sustainability": [],
        "avg_risk": []
    })
    
    for app in applications:
        app_region = app.get("region", "Unknown")
        
        if region and region.lower() not in app_region.lower():
            continue
        
        stats = region_stats[app_region]
        stats["count"] += 1
        
        if app.get("status") == "APPROVED":
            stats["approved"] += 1
            stats["total_amount"] += app.get("loan_amount", 0)
        
        sust = app.get("sustainability_score", 0)
        if sust > 0:
            stats["avg_sustainability"].append(sust)
        
        risk = app.get("risk_score", 0)
        if risk > 0:
            stats["avg_risk"].append(risk)
    
    # Calculate averages
    result = {}
    for reg, stats in region_stats.items():
        result[reg] = {
            "count": stats["count"],
            "approved": stats["approved"],
            "approval_rate": (stats["approved"] / stats["count"] * 100) if stats["count"] > 0 else 0,
            "total_amount": stats["total_amount"],
            "avg_sustainability": sum(stats["avg_sustainability"]) / len(stats["avg_sustainability"]) if stats["avg_sustainability"] else 0,
            "avg_risk": sum(stats["avg_risk"]) / len(stats["avg_risk"]) if stats["avg_risk"] else 0
        }
    
    return {
        "regions": result,
        "total": len(applications)
    }


def get_trend_analysis(metric: str = "sustainability") -> Dict[str, Any]:
    """Analyze trends over time for a specific metric."""
    applications = load_applications()
    
    if not applications:
        return {"trends": [], "periods": []}
    
    # Group by month
    monthly_data = defaultdict(lambda: {
        "count": 0,
        "values": []
    })
    
    for app in applications:
        timestamp = app.get("timestamp", "")
        if not timestamp:
            continue
        
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            month_key = dt.strftime("%Y-%m")
            
            value = None
            if metric == "sustainability":
                value = app.get("sustainability_score", 0)
            elif metric == "risk":
                value = app.get("risk_score", 0)
            elif metric == "ndvi":
                value = app.get("ndvi_current", 0)
            
            if value and value > 0:
                monthly_data[month_key]["count"] += 1
                monthly_data[month_key]["values"].append(value)
        
        except Exception:
            continue
    
    # Calculate averages
    trends = []
    periods = []
    
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        if data["values"]:
            avg_value = sum(data["values"]) / len(data["values"])
            trends.append(avg_value)
            periods.append(month_key)
    
    return {
        "trends": trends,
        "periods": periods,
        "metric": metric,
        "current": trends[-1] if trends else 0,
        "change": (trends[-1] - trends[0]) if len(trends) > 1 else 0
    }


def calculate_carbon_impact() -> Dict[str, Any]:
    """Calculate aggregate carbon impact of approved loans."""
    applications = load_applications()
    
    approved_loans = [app for app in applications if app.get("status") == "APPROVED"]
    
    if not approved_loans:
        return {
            "total_loans": 0,
            "total_carbon_offset_tons": 0,
            "avg_carbon_per_loan": 0
        }
    
    # Estimate: Each approved sustainable loan offsets ~2-5 tons CO2/year
    # Based on sustainability score
    total_carbon = 0
    
    for app in approved_loans:
        sust_score = app.get("sustainability_score", 0)
        # Higher sustainability = more carbon offset
        carbon_per_loan = 2 + (sust_score / 100 * 3)  # 2-5 tons range
        total_carbon += carbon_per_loan
    
    return {
        "total_loans": len(approved_loans),
        "total_carbon_offset_tons": round(total_carbon, 2),
        "avg_carbon_per_loan": round(total_carbon / len(approved_loans), 2) if approved_loans else 0,
        "equivalent_trees": round(total_carbon * 20, 0)  # ~20 trees per ton CO2
    }


def get_compliance_audit() -> Dict[str, Any]:
    """Perform compliance audit against standards."""
    applications = load_applications()
    
    if not applications:
        return {
            "total_audited": 0,
            "compliant": 0,
            "non_compliant": 0,
            "compliance_rate": 0
        }
    
    compliant = 0
    non_compliant = 0
    
    for app in applications:
        # Check compliance criteria
        sust_score = app.get("sustainability_score", 0)
        deforestation = app.get("deforestation_detected", False)
        risk_score = app.get("risk_score", 100)
        
        # Compliant if: sustainability >= 60, no deforestation, risk < 50
        is_compliant = (
            sust_score >= 60 and
            not deforestation and
            risk_score < 50
        )
        
        if is_compliant:
            compliant += 1
        else:
            non_compliant += 1
    
    total = len(applications)
    
    return {
        "total_audited": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "compliance_rate": (compliant / total * 100) if total > 0 else 0,
        "issues": [
            "Low sustainability scores",
            "Deforestation detected",
            "High risk scores"
        ] if non_compliant > 0 else []
    }


def export_to_csv(output_path: Optional[str] = None) -> str:
    """Export applications to CSV file."""
    applications = load_applications()
    
    if not applications:
        raise ValueError("No applications to export")
    
    # Flatten data for CSV
    df_data = []
    for app in applications:
        df_data.append({
            "ID": app.get("id", ""),
            "Status": app.get("status", ""),
            "Loan Amount": app.get("loan_amount", 0),
            "Sustainability Score": app.get("sustainability_score", 0),
            "Risk Score": app.get("risk_score", 0),
            "NDVI Current": app.get("ndvi_current", 0),
            "Region": app.get("region", ""),
            "Timestamp": app.get("timestamp", "")
        })
    
    df = pd.DataFrame(df_data)
    
    if not output_path:
        ensure_data_dir()
        output_path = str(DATA_DIR / f"applications_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    df.to_csv(output_path, index=False)
    return output_path


def export_to_pdf(output_path: Optional[str] = None) -> str:
    """Export portfolio summary to PDF."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
    except ImportError:
        raise ImportError("reportlab is required for PDF export")
    
    ensure_data_dir()
    
    if not output_path:
        output_path = str(DATA_DIR / f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    story.append(Paragraph("GreenChain Portfolio Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    
    # Portfolio Stats
    stats = get_portfolio_stats()
    story.append(Paragraph("Portfolio Statistics", styles["Heading2"]))
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Applications", str(stats["total_applications"])],
        ["Approved", str(stats["approved"])],
        ["Pending", str(stats["pending"])],
        ["Rejected", str(stats["rejected"])],
        ["Total Disbursed", f"${stats['total_disbursed']:,.0f}"],
        ["Avg Sustainability", f"{stats['avg_sustainability']:.1f}/100"],
        ["Green Compliance Rate", f"{stats['green_compliance_rate']:.1f}%"]
    ]
    
    table = Table(stats_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), "#4472C4"),
        ("TEXTCOLOR", (0, 0), (-1, 0), "white"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), "#F2F2F2"),
        ("GRID", (0, 0), (-1, -1), 1, "#CCCCCC")
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Carbon Impact
    carbon = calculate_carbon_impact()
    story.append(Paragraph("Carbon Impact", styles["Heading2"]))
    story.append(Paragraph(f"Total Carbon Offset: {carbon['total_carbon_offset_tons']:.2f} tons CO2", styles["Normal"]))
    story.append(Paragraph(f"Equivalent Trees Planted: {carbon['equivalent_trees']:.0f}", styles["Normal"]))
    
    # Footer
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    
    doc.build(story)
    return output_path
