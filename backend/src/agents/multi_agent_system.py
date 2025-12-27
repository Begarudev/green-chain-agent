"""
Multi-Agent System for GreenChain using LangGraph.

This module implements a sophisticated multi-agent architecture where:
1. Field Scout Agent - Gathers satellite and weather data
2. Risk Analyst Agent - Analyzes data and calculates risk scores
3. Loan Officer Agent - Makes final lending decisions

The agents communicate through a shared state and work together
to provide comprehensive loan assessments.
"""

import os
from typing import TypedDict, Annotated, Literal, Dict, Any, Optional
from datetime import datetime
import operator

# Check if langgraph is available
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    print(f"[AGENTS] Warning: LangGraph not installed ({e}). Using fallback mode.")

# Import our services
from services.satellite_service import get_farm_ndvi
from services.weather_service import get_weather_analysis
from services.llm_service import analyze_loan_risk


# ---------------------------------------------------------------------------
# Agent State Definition
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    """Shared state between all agents in the workflow."""
    # Input
    latitude: float
    longitude: float
    loan_purpose: str
    loan_amount: Optional[float]
    
    # Field Scout Agent outputs
    satellite_data: Optional[Dict[str, Any]]
    weather_data: Optional[Dict[str, Any]]
    field_report: Optional[str]
    
    # Risk Analyst Agent outputs
    risk_scores: Optional[Dict[str, float]]
    risk_analysis: Optional[str]
    composite_score: Optional[float]
    
    # Loan Officer Agent outputs
    final_decision: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    recommendations: Optional[list]
    certificate_eligible: Optional[bool]
    
    # Workflow metadata
    agent_trace: Annotated[list, operator.add]  # Tracks which agents ran
    errors: Optional[list]
    timestamp: Optional[str]


# ---------------------------------------------------------------------------
# Agent Implementations
# ---------------------------------------------------------------------------

def field_scout_agent(state: AgentState) -> AgentState:
    """
    🛰️ Field Scout Agent
    
    Responsibilities:
    - Fetch satellite imagery and calculate NDVI
    - Gather historical weather data
    - Compile initial field report
    """
    print("\n" + "="*50)
    print("🛰️ FIELD SCOUT AGENT ACTIVATED")
    print("="*50)
    
    lat = state["latitude"]
    lon = state["longitude"]
    errors = []
    
    # Task 1: Fetch satellite data
    print(f"[Field Scout] Fetching satellite data for ({lat}, {lon})...")
    try:
        satellite_data = get_farm_ndvi(lat, lon)
        print(f"[Field Scout] ✓ Satellite data acquired. NDVI: {satellite_data.get('ndvi_score', 'N/A')}")
    except Exception as e:
        satellite_data = {"error": str(e), "ndvi_score": 0.0}
        errors.append(f"Satellite error: {str(e)}")
        print(f"[Field Scout] ✗ Satellite error: {e}")
    
    # Task 2: Fetch weather data
    print(f"[Field Scout] Fetching weather history...")
    try:
        weather_data = get_weather_analysis(lat, lon)
        print(f"[Field Scout] ✓ Weather data acquired. Risk: {weather_data.get('weather_risk_score', 'N/A')}")
    except Exception as e:
        weather_data = {"error": str(e), "weather_risk_score": 0.5}
        errors.append(f"Weather error: {str(e)}")
        print(f"[Field Scout] ✗ Weather error: {e}")
    
    # Compile field report
    field_report = f"""
📍 FIELD RECONNAISSANCE REPORT
Location: {lat}, {lon}
Survey Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

🌿 Vegetation Analysis:
- NDVI Score: {satellite_data.get('ndvi_score', 'N/A')}
- Status: {satellite_data.get('status', 'Unknown')}
- Cloud Cover: {satellite_data.get('cloud_cover', 'N/A')}%

🌤️ Climate Conditions (90-day history):
- Total Rainfall: {weather_data.get('rainfall_total_mm', 'N/A')} mm
- Temperature Range: {weather_data.get('temperature_min_c', 'N/A')}°C - {weather_data.get('temperature_max_c', 'N/A')}°C
- Drought Risk: {weather_data.get('drought_risk_score', 'N/A')}
- Frost Days: {weather_data.get('frost_days', 'N/A')}

Field Scout Assessment: {'Data collection successful' if not errors else f'Partial data - {len(errors)} errors'}
"""
    
    print("[Field Scout] Field report compiled. Handing off to Risk Analyst...")
    
    return {
        **state,
        "satellite_data": satellite_data,
        "weather_data": weather_data,
        "field_report": field_report,
        "agent_trace": ["field_scout"],
        "errors": errors if errors else None
    }


def risk_analyst_agent(state: AgentState) -> AgentState:
    """
    📊 Risk Analyst Agent
    
    Responsibilities:
    - Calculate composite risk scores
    - Analyze sustainability metrics
    - Provide risk-based recommendations
    """
    print("\n" + "="*50)
    print("📊 RISK ANALYST AGENT ACTIVATED")
    print("="*50)
    
    satellite_data = state.get("satellite_data", {})
    weather_data = state.get("weather_data", {})
    
    # Extract key metrics
    ndvi_score = satellite_data.get("ndvi_score", 0.0)
    weather_risk = weather_data.get("weather_risk_score", 0.5)
    drought_risk = weather_data.get("drought_risk_score", 0.5)
    
    print(f"[Risk Analyst] Analyzing metrics...")
    print(f"  - NDVI Score: {ndvi_score}")
    print(f"  - Weather Risk: {weather_risk}")
    print(f"  - Drought Risk: {drought_risk}")
    
    # Calculate component scores (0-1, higher is better)
    vegetation_score = min(1.0, ndvi_score / 0.8) if ndvi_score > 0 else 0
    climate_score = 1 - weather_risk
    sustainability_score = 1 - drought_risk
    
    # Weighted composite score
    weights = {
        "vegetation": 0.40,
        "climate": 0.30,
        "sustainability": 0.30
    }
    
    composite_score = (
        vegetation_score * weights["vegetation"] +
        climate_score * weights["climate"] +
        sustainability_score * weights["sustainability"]
    )
    
    risk_scores = {
        "vegetation_score": round(vegetation_score, 3),
        "climate_score": round(climate_score, 3),
        "sustainability_score": round(sustainability_score, 3),
        "composite_score": round(composite_score, 3),
        "risk_level": "LOW" if composite_score > 0.6 else "MEDIUM" if composite_score > 0.4 else "HIGH"
    }
    
    # Generate risk analysis
    risk_analysis = f"""
📊 RISK ANALYSIS REPORT

Component Scores (0-1 scale, higher is better):
├─ 🌿 Vegetation Health: {risk_scores['vegetation_score']:.2f} (weight: {weights['vegetation']:.0%})
├─ 🌤️ Climate Favorability: {risk_scores['climate_score']:.2f} (weight: {weights['climate']:.0%})
└─ 💧 Sustainability Index: {risk_scores['sustainability_score']:.2f} (weight: {weights['sustainability']:.0%})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPOSITE SCORE: {risk_scores['composite_score']:.2f}
RISK LEVEL: {risk_scores['risk_level']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Risk Factors Identified:
{f'⚠️ Low vegetation health (NDVI < 0.4)' if ndvi_score < 0.4 else '✓ Vegetation healthy'}
{f'⚠️ Elevated weather risk ({weather_risk:.0%})' if weather_risk > 0.4 else '✓ Weather conditions favorable'}
{f'⚠️ Drought concerns detected' if drought_risk > 0.5 else '✓ Water availability adequate'}
"""
    
    print(f"[Risk Analyst] Composite Score: {composite_score:.2f} ({risk_scores['risk_level']} risk)")
    print("[Risk Analyst] Analysis complete. Handing off to Loan Officer...")
    
    return {
        **state,
        "risk_scores": risk_scores,
        "risk_analysis": risk_analysis,
        "composite_score": composite_score,
        "agent_trace": ["risk_analyst"]
    }


def loan_officer_agent(state: AgentState) -> AgentState:
    """
    🏦 Loan Officer Agent
    
    Responsibilities:
    - Make final lending decision
    - Generate reasoning and recommendations
    - Determine certificate eligibility
    """
    print("\n" + "="*50)
    print("🏦 LOAN OFFICER AGENT ACTIVATED")
    print("="*50)
    
    composite_score = state.get("composite_score", 0.0)
    risk_scores = state.get("risk_scores", {})
    satellite_data = state.get("satellite_data", {})
    weather_data = state.get("weather_data", {})
    loan_purpose = state.get("loan_purpose", "")
    
    print(f"[Loan Officer] Reviewing application...")
    print(f"  - Composite Score: {composite_score:.2f}")
    print(f"  - Risk Level: {risk_scores.get('risk_level', 'Unknown')}")
    print(f"  - Loan Purpose: {loan_purpose[:50]}...")
    
    # Decision logic
    recommendations = []
    
    if composite_score >= 0.6:
        decision = "APPROVED"
        confidence = min(0.95, 0.75 + composite_score * 0.2)
        reasoning = f"""
Based on comprehensive analysis, this loan application is APPROVED.

Key Factors:
✓ Strong vegetation health indicates sustainable farming practices
✓ Favorable climate conditions support agricultural productivity
✓ Low overall risk profile (Composite Score: {composite_score:.2f})

The applicant demonstrates commitment to sustainable agriculture through:
- Healthy crop indicators (NDVI: {satellite_data.get('ndvi_score', 'N/A')})
- Climate-resilient location
- Stated purpose: {loan_purpose}
"""
        certificate_eligible = True
        
    elif composite_score >= 0.4:
        decision = "CONDITIONAL"
        confidence = 0.65 + composite_score * 0.15
        reasoning = f"""
Based on analysis, this loan application receives CONDITIONAL approval.

Assessment Summary:
- Moderate vegetation health requires monitoring
- Some climate risk factors present
- Composite Score: {composite_score:.2f} (Moderate)

Conditions for Approval:
1. Implement recommended risk mitigation measures
2. Quarterly progress reporting required
3. Reduced initial loan amount recommended
"""
        recommendations = [
            "Implement drip irrigation to reduce water dependency",
            "Consider crop diversification for risk mitigation",
            "Install weather monitoring equipment",
            "Submit quarterly vegetation health reports"
        ]
        certificate_eligible = True
        
    else:
        decision = "REJECTED"
        confidence = 0.70 + (1 - composite_score) * 0.2
        reasoning = f"""
Based on analysis, this loan application is REJECTED at this time.

Risk Assessment:
✗ Vegetation health below acceptable threshold
✗ Climate/weather conditions pose significant risk
✗ Composite Score: {composite_score:.2f} (High Risk)

The application may be reconsidered after:
1. Improvement in vegetation health indicators
2. Implementation of climate adaptation measures
3. Minimum 6-month waiting period
"""
        recommendations = [
            "Improve soil health through composting",
            "Implement water conservation practices",
            "Consider drought-resistant crop varieties",
            "Apply for agricultural extension support",
            "Reapply after 6 months with improved metrics"
        ]
        certificate_eligible = False
    
    print(f"[Loan Officer] Decision: {decision} (Confidence: {confidence:.0%})")
    print("[Loan Officer] Multi-agent workflow complete.")
    
    return {
        **state,
        "final_decision": decision,
        "confidence": round(confidence, 2),
        "reasoning": reasoning.strip(),
        "recommendations": recommendations,
        "certificate_eligible": certificate_eligible,
        "timestamp": datetime.now().isoformat(),
        "agent_trace": ["loan_officer"]
    }


# ---------------------------------------------------------------------------
# Workflow Construction
# ---------------------------------------------------------------------------

def create_agent_workflow():
    """
    Creates the LangGraph workflow connecting all agents.
    
    Workflow:
    Field Scout → Risk Analyst → Loan Officer → END
    """
    if not LANGGRAPH_AVAILABLE:
        return None
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes (agents)
    workflow.add_node("field_scout", field_scout_agent)
    workflow.add_node("risk_analyst", risk_analyst_agent)
    workflow.add_node("loan_officer", loan_officer_agent)
    
    # Define edges (flow)
    workflow.set_entry_point("field_scout")
    workflow.add_edge("field_scout", "risk_analyst")
    workflow.add_edge("risk_analyst", "loan_officer")
    workflow.add_edge("loan_officer", END)
    
    # Compile
    return workflow.compile()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_multi_agent_analysis(
    latitude: float,
    longitude: float,
    loan_purpose: str = "",
    loan_amount: float = None
) -> Dict[str, Any]:
    """
    Run the complete multi-agent loan analysis workflow.
    
    Args:
        latitude: Farm latitude
        longitude: Farm longitude
        loan_purpose: Description of loan purpose
        loan_amount: Requested loan amount (optional)
    
    Returns:
        Complete analysis results including all agent outputs
    """
    print("\n" + "🌱"*25)
    print("GREENCHAIN MULTI-AGENT SYSTEM INITIATED")
    print("🌱"*25)
    
    # Initial state
    initial_state: AgentState = {
        "latitude": latitude,
        "longitude": longitude,
        "loan_purpose": loan_purpose,
        "loan_amount": loan_amount,
        "satellite_data": None,
        "weather_data": None,
        "field_report": None,
        "risk_scores": None,
        "risk_analysis": None,
        "composite_score": None,
        "final_decision": None,
        "confidence": None,
        "reasoning": None,
        "recommendations": None,
        "certificate_eligible": None,
        "agent_trace": [],
        "errors": None,
        "timestamp": None
    }
    
    if LANGGRAPH_AVAILABLE:
        # Use LangGraph workflow
        workflow = create_agent_workflow()
        if workflow:
            result = workflow.invoke(initial_state)
            return result
    
    # Fallback: Run agents sequentially without LangGraph
    print("[System] Running in fallback mode (LangGraph not available)")
    state = field_scout_agent(initial_state)
    state = risk_analyst_agent(state)
    state = loan_officer_agent(state)
    
    return state


# For backward compatibility with existing code
def process_loan_with_agents(lat: float, lon: float, context: str) -> Dict[str, Any]:
    """
    Wrapper function for compatibility with existing app.py structure.
    
    Returns data in format expected by the Streamlit frontend.
    """
    result = run_multi_agent_analysis(lat, lon, loan_purpose=context)
    
    # Transform to expected format
    return {
        "farm_data": result.get("satellite_data", {}),
        "weather_data": result.get("weather_data", {}),
        "llm_result": {
            "decision": result.get("final_decision", "PENDING"),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
            "recommendations": result.get("recommendations", []),
            "model_used": "multi-agent-system"
        },
        "agent_trace": result.get("agent_trace", []),
        "risk_scores": result.get("risk_scores", {}),
        "field_report": result.get("field_report", ""),
        "risk_analysis": result.get("risk_analysis", ""),
        "certificate_eligible": result.get("certificate_eligible", False)
    }
