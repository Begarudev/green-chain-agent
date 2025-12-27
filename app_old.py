"""
Streamlit frontend for the 🌱 GreenChain: AI Sustainable Finance Agent.
Refactored for Clean UX/UI and Robust State Management.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path Setup
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_SRC = ROOT_DIR / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

# Load Env
env_path = ROOT_DIR / ".env.local"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Service Imports
try:
    import services.satellite_service as satellite_service
    import services.weather_service as weather_service
    from services import llm_service
    from services.verification_service import (
        create_green_certificate,
        generate_blockchain_hash,
    )
    from agents.multi_agent_system import process_loan_with_agents
    MULTI_AGENT_AVAILABLE = True
except ImportError as e:
    st.error(f"Backend Import Error: {e}. Make sure you are running from the root directory.")
    MULTI_AGENT_AVAILABLE = False
    st.stop()


# ---------------------------------------------------------------------------
# UI Configuration & CSS
# ---------------------------------------------------------------------------
def setup_page():
    st.set_page_config(
        page_title="GreenChain | AI Finance",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Modern CSS Injection
    st.markdown("""
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Hides Streamlit's default top padding */
        .block-container {
            padding-top: 2rem;
        }

        /* Custom Header Styling */
        .hero-header {
            color: #064e3b;
            font-weight: 700;
            font-size: 2.5rem;
            margin-bottom: 0px;
        }
        .hero-subheader {
            color: #6b7280;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }

        /* Metric Styling */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #064e3b;
        }

        /* Success/Error Callouts */
        .stAlert {
            border-radius: 8px;
        }
        
        /* Remove anchor links next to headers */
        .css-15zrgzn {display: none}
        </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Logic Functions
# ---------------------------------------------------------------------------
def run_analysis(lat: float, lon: float, context: str, use_multi_agent: bool = False) -> Dict[str, Any]:
    """Orchestrates the backend services including satellite, weather, and LLM analysis."""
    
    # Multi-Agent Mode
    if use_multi_agent and MULTI_AGENT_AVAILABLE:
        return process_loan_with_agents(lat, lon, context)
    
    # Standard Mode
    # Step 1: Fetch satellite data
    farm_data = satellite_service.get_farm_ndvi(lat, lon)
    
    # If satellite fails, don't waste money on LLM
    if farm_data.get("error") and "Simulated" not in farm_data.get("status", ""):
        return {"farm_data": farm_data, "weather_data": None, "llm_result": None}
    
    # Step 2: Fetch weather data
    weather_data = weather_service.get_weather_analysis(lat, lon)
    
    # Step 3: Combine data for LLM analysis
    combined_data = {
        **farm_data,
        "weather": weather_data
    }
    
    llm_result = llm_service.analyze_loan_risk(combined_data, user_request=context)
    return {"farm_data": farm_data, "weather_data": weather_data, "llm_result": llm_result}


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
def main():
    setup_page()

    # --- Session State Initialization ---
    if "lat" not in st.session_state: st.session_state.lat = 37.669
    if "lon" not in st.session_state: st.session_state.lon = -100.749
    if "analysis_result" not in st.session_state: st.session_state.analysis_result = None

    # --- Header ---
    st.markdown('<div class="hero-header">🌱 GreenChain Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subheader">AI-Powered Verification for Sustainable Micro-Loans</div>', unsafe_allow_html=True)

    # --- Layout ---
    col_sidebar, col_main = st.columns([1, 2.5], gap="large")

    # --- SIDEBAR (Controls) ---
    with col_sidebar:
        with st.container(border=True):
            st.subheader("📍 Farm Location")
            
            # Map Interactions - One way flow usually works best in Streamlit
            new_lat = st.number_input("Latitude", value=st.session_state.lat, format="%.4f")
            new_lon = st.number_input("Longitude", value=st.session_state.lon, format="%.4f")
            
            # Update state if inputs change
            if new_lat != st.session_state.lat or new_lon != st.session_state.lon:
                st.session_state.lat = new_lat
                st.session_state.lon = new_lon
                # Clear previous result if location changes
                st.session_state.analysis_result = None 

            st.caption("Try: Kansas (37.669, -100.749) or India (29.605, 76.273)")
        
        with st.container(border=True):
            st.subheader("⚙️ Configuration")
            
            # Multi-Agent Mode Toggle
            use_multi_agent = st.toggle("🤖 Multi-Agent Mode", value=True, 
                help="Use advanced multi-agent system with Field Scout, Risk Analyst, and Loan Officer agents")
            
            mock_mode = st.toggle("Mock Mode (Fast)", value=False)
            satellite_service.MOCK_MODE = mock_mode
            weather_service.MOCK_MODE = mock_mode
            llm_mock_mode = st.toggle("Mock LLM (No API Key)", value=False)
            llm_service.MOCK_MODE = llm_mock_mode
            
            loan_context = st.text_area("Loan Purpose", "Expansion of organic wheat farming using drip irrigation.")
            
            run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

    # --- MAIN CONTENT ---
    with col_main:
        
        # 1. THE MAP
        # We put the map in an expander or top section
        m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=14, tiles="OpenStreetMap")
        folium.Marker(
            [st.session_state.lat, st.session_state.lon], 
            popup="Target Farm", 
            icon=folium.Icon(color="green", icon="leaf")
        ).add_to(m)
        
        # Display map
        st_folium(m, height=300, width="100%", key="main_map")

        # 2. RUN LOGIC
        if run_btn:
            with st.status("🔍 Agent Active...", expanded=True) as status:
                if use_multi_agent:
                    st.write("🤖 **Multi-Agent System Activated**")
                    st.write("🛰️ Field Scout Agent: Gathering satellite & weather data...")
                    st.write("📊 Risk Analyst Agent: Computing risk scores...")
                    st.write("🏦 Loan Officer Agent: Making decision...")
                else:
                    st.write("🛰️ Contacting Sentinel-2 Satellite Interface...")
                    st.write("📸 Downloading Multispectral Imagery...")
                    st.write("🌤️ Fetching Historical Weather Data...")
                
                time.sleep(0.5) # UI pacing
                result = run_analysis(st.session_state.lat, st.session_state.lon, loan_context, use_multi_agent)
                
                if result["farm_data"].get("error") and "Simulated" not in result["farm_data"].get("status", ""):
                    status.update(label="❌ Data Retrieval Failed", state="error")
                    st.error(result["farm_data"]["error"])
                else:
                    if not use_multi_agent:
                        st.write("🧠 Processing Risk Models (Gemini Pro)...")
                    st.session_state.analysis_result = result
                    st.session_state.used_multi_agent = use_multi_agent
                    status.update(label="✅ Analysis Complete", state="complete")

        # 3. DISPLAY RESULTS
        if st.session_state.analysis_result:
            res = st.session_state.analysis_result
            farm = res["farm_data"]
            weather = res.get("weather_data", {})
            llm = res["llm_result"]
            
            st.divider()
            
            # --- TOP METRICS ROW ---
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Vegetation Index (NDVI)", f"{farm.get('ndvi_score', 0):.2f}", delta="Target > 0.4")
            with m2:
                # Colorize Status
                status_color = ":green" if "Healthy" in farm.get('status', '') else ":red"
                st.metric("Vegetation Status", farm.get('status', 'Unknown'))
            with m3:
                # Weather risk
                weather_risk = weather.get('weather_risk_score', 0) if weather else 0
                st.metric("Weather Risk", f"{weather_risk:.0%}", delta=weather.get('weather_status', 'Unknown'))
            with m4:
                # Decision
                decision = llm.get('decision', 'PENDING')
                icon = "✅" if "APPROVED" in decision else "⚠️" if "CONDITIONAL" in decision else "❌"
                st.metric("AI Recommendation", f"{icon} {decision}")
            
            # --- WEATHER DATA SECTION ---
            if weather and not weather.get("error"):
                st.subheader("🌤️ Climate Analysis")
                w1, w2, w3, w4 = st.columns(4)
                with w1:
                    st.metric("Total Rainfall", f"{weather.get('rainfall_total_mm', 'N/A')} mm")
                with w2:
                    st.metric("Avg Temperature", f"{weather.get('temperature_avg_c', 'N/A')}°C")
                with w3:
                    st.metric("Drought Risk", f"{weather.get('drought_risk_score', 0):.0%}")
                with w4:
                    st.metric("Frost Days", weather.get('frost_days', 'N/A'))
            
            # --- MULTI-AGENT TRACE (if used) ---
            if st.session_state.get("used_multi_agent") and res.get("agent_trace"):
                st.subheader("🤖 Multi-Agent Workflow")
                
                # Agent trace visualization
                agents_run = res.get("agent_trace", [])
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    agent_done = "field_scout" in agents_run
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: {'#d4edda' if agent_done else '#f8f9fa'}; border-radius: 8px;">
                        <div style="font-size: 2em;">🛰️</div>
                        <div style="font-weight: bold;">Field Scout</div>
                        <div style="color: {'green' if agent_done else 'gray'};">{'✓ Complete' if agent_done else '○ Pending'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    agent_done = "risk_analyst" in agents_run
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: {'#d4edda' if agent_done else '#f8f9fa'}; border-radius: 8px;">
                        <div style="font-size: 2em;">📊</div>
                        <div style="font-weight: bold;">Risk Analyst</div>
                        <div style="color: {'green' if agent_done else 'gray'};">{'✓ Complete' if agent_done else '○ Pending'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    agent_done = "loan_officer" in agents_run
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: {'#d4edda' if agent_done else '#f8f9fa'}; border-radius: 8px;">
                        <div style="font-size: 2em;">🏦</div>
                        <div style="font-weight: bold;">Loan Officer</div>
                        <div style="color: {'green' if agent_done else 'gray'};">{'✓ Complete' if agent_done else '○ Pending'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show risk scores if available
                risk_scores = res.get("risk_scores", {})
                if risk_scores:
                    st.markdown("**📊 Risk Score Breakdown:**")
                    score_cols = st.columns(4)
                    with score_cols[0]:
                        st.metric("Vegetation", f"{risk_scores.get('vegetation_score', 0):.0%}")
                    with score_cols[1]:
                        st.metric("Climate", f"{risk_scores.get('climate_score', 0):.0%}")
                    with score_cols[2]:
                        st.metric("Sustainability", f"{risk_scores.get('sustainability_score', 0):.0%}")
                    with score_cols[3]:
                        composite = risk_scores.get('composite_score', 0)
                        risk_level = risk_scores.get('risk_level', 'Unknown')
                        st.metric("Composite", f"{composite:.0%}", delta=risk_level)

            # --- DECISION DETAIL ---
            st.subheader("📝 Agent Reasoning")
            
            # Use a colored container for the decision
            container_color = "green" if "APPROVED" in decision else "orange" if "CONDITIONAL" in decision else "red"
            
            with st.container(border=True):
                st.markdown(f"**Confidence Score:** {llm.get('confidence', 0):.0%}")
                st.write(llm.get('reasoning', 'No reasoning provided.'))

            # --- CERTIFICATION (Only if Approved) ---
            if "APPROVED" in decision or "CONDITIONAL" in decision:
                st.markdown("### 🔐 Blockchain Verification")
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    tx_hash = generate_blockchain_hash(farm, llm)
                    st.info(f"**Ledger Proof ID:** `{tx_hash}`")
                
                with c2:
                    # Generate PDF on the fly
                    pdf_path, _ = create_green_certificate(farm, llm)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📜 Download Cert",
                            data=f,
                            file_name="GreenChain_Certificate.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
                # Only show balloons on fresh run
                if run_btn:
                    st.balloons()

if __name__ == "__main__":
    main()