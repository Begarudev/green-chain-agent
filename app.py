"""
🌱 GreenChain Agent - AI-Powered Sustainable Finance
Redesigned with modern UX principles for hackathon impact.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict

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

# Load Environment
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
# Page Configuration & Custom CSS
# ---------------------------------------------------------------------------
def setup_page():
    st.set_page_config(
        page_title="GreenChain | Sustainable Finance AI",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
        <style>
        /* Import Modern Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Remove default padding */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 1200px;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom Hero Header */
        .hero-container {
            background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 40px rgba(6, 78, 59, 0.3);
        }
        
        .hero-title {
            color: white;
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.5px;
        }
        
        .hero-subtitle {
            color: rgba(255,255,255,0.85);
            font-size: 1.1rem;
            font-weight: 400;
            margin-top: 0.5rem;
        }
        
        .hero-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 1rem;
            backdrop-filter: blur(10px);
        }
        
        /* Step Cards */
        .step-card {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.3s ease;
            height: 100%;
        }
        
        .step-card:hover {
            border-color: #059669;
            box-shadow: 0 4px 20px rgba(5, 150, 105, 0.15);
        }
        
        .step-card.active {
            border-color: #059669;
            background: linear-gradient(180deg, #ecfdf5 0%, white 100%);
        }
        
        .step-number {
            width: 32px;
            height: 32px;
            background: #059669;
            color: white;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .step-title {
            font-weight: 600;
            color: #1f2937;
            margin: 0.5rem 0 0.25rem;
        }
        
        .step-desc {
            color: #6b7280;
            font-size: 0.85rem;
        }
        
        /* Decision Cards */
        .decision-card {
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
        }
        
        .decision-approved {
            background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
            border: 2px solid #10b981;
        }
        
        .decision-conditional {
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            border: 2px solid #f59e0b;
        }
        
        .decision-rejected {
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
            border: 2px solid #ef4444;
        }
        
        .decision-icon {
            font-size: 4rem;
            margin-bottom: 0.5rem;
        }
        
        .decision-title {
            font-size: 1.75rem;
            font-weight: 800;
            margin: 0.5rem 0;
        }
        
        .decision-approved .decision-title { color: #059669; }
        .decision-conditional .decision-title { color: #d97706; }
        .decision-rejected .decision-title { color: #dc2626; }
        
        .decision-confidence {
            font-size: 0.9rem;
            color: #6b7280;
            margin-top: 0.5rem;
        }
        
        /* Metric Cards */
        .metric-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #064e3b;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Agent Pipeline */
        .agent-pipeline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 1.5rem 0;
        }
        
        .agent-node {
            flex: 1;
            text-align: center;
            padding: 1rem;
            background: #f9fafb;
            border-radius: 12px;
            margin: 0 0.5rem;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        
        .agent-node.complete {
            background: #ecfdf5;
            border-color: #10b981;
        }
        
        .agent-node.active {
            background: #eff6ff;
            border-color: #3b82f6;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
            50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
        }
        
        .agent-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .agent-name {
            font-weight: 600;
            font-size: 0.9rem;
            color: #374151;
        }
        
        .agent-status {
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
        
        .agent-connector {
            color: #d1d5db;
            font-size: 1.5rem;
        }
        
        /* Sample Locations */
        .location-chip {
            display: inline-block;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            margin: 0.25rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .location-chip:hover {
            background: #ecfdf5;
            border-color: #059669;
            color: #059669;
        }
        
        /* Progress Bar */
        .custom-progress {
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .custom-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #059669, #10b981);
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        
        /* Blockchain Hash */
        .blockchain-hash {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.85rem;
            background: #1f2937;
            color: #10b981;
            padding: 1rem;
            border-radius: 8px;
            word-break: break-all;
            margin: 0.5rem 0;
        }
        
        /* Info Box */
        .info-box {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin: 1rem 0;
        }
        
        /* Stacked Bar Chart */
        .score-bar-container {
            display: flex;
            height: 24px;
            border-radius: 12px;
            overflow: hidden;
            background: #e5e7eb;
            margin: 0.5rem 0;
        }
        
        .score-bar-segment {
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
            font-weight: 600;
            color: white;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .hero-title { font-size: 1.75rem; }
            .decision-icon { font-size: 3rem; }
        }
        </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper Components
# ---------------------------------------------------------------------------

def render_hero():
    """Render the hero header section."""
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">🌱 GreenChain Agent</div>
            <div class="hero-subtitle">AI-Powered Verification for Sustainable Agricultural Micro-Loans</div>
            <div class="hero-badge">🤖 Multi-Agent System • 🛰️ Satellite Verified • ⛓️ Blockchain Secured</div>
        </div>
    """, unsafe_allow_html=True)


def render_step_indicators(current_step: int):
    """Render the step indicator showing progress."""
    steps = [
        ("1", "Select Location", "Choose farm coordinates"),
        ("2", "Configure", "Set analysis parameters"),
        ("3", "Analyze", "Run AI verification"),
        ("4", "Results", "View decision & certificate")
    ]
    
    cols = st.columns(4)
    for i, (num, title, desc) in enumerate(steps):
        with cols[i]:
            active = "active" if i + 1 == current_step else ""
            completed = "✓" if i + 1 < current_step else num
            st.markdown(f"""
                <div class="step-card {active}">
                    <div class="step-number">{completed}</div>
                    <div class="step-title">{title}</div>
                    <div class="step-desc">{desc}</div>
                </div>
            """, unsafe_allow_html=True)


def render_agent_pipeline(agents_run: list, is_running: bool = False):
    """Render the multi-agent workflow visualization."""
    agents = [
        ("🛰️", "Field Scout", "Satellite & Weather"),
        ("📊", "Risk Analyst", "Score Calculation"),
        ("🏦", "Loan Officer", "Final Decision")
    ]
    
    html = '<div class="agent-pipeline">'
    for i, (icon, name, desc) in enumerate(agents):
        agent_key = ["field_scout", "risk_analyst", "loan_officer"][i]
        
        if agent_key in agents_run:
            status_class = "complete"
            status_text = "✓ Complete"
        elif is_running and len(agents_run) == i:
            status_class = "active"
            status_text = "⟳ Processing..."
        else:
            status_class = ""
            status_text = "○ Pending"
        
        html += f'''
            <div class="agent-node {status_class}">
                <div class="agent-icon">{icon}</div>
                <div class="agent-name">{name}</div>
                <div class="agent-status">{status_text}</div>
            </div>
        '''
        if i < 2:
            html += '<div class="agent-connector">→</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_decision_card(decision: str, confidence: float):
    """Render the prominent decision card."""
    if "APPROVED" in decision:
        card_class = "decision-approved"
        icon = "✅"
        title = "LOAN APPROVED"
    elif "CONDITIONAL" in decision:
        card_class = "decision-conditional"
        icon = "⚠️"
        title = "CONDITIONAL APPROVAL"
    else:
        card_class = "decision-rejected"
        icon = "❌"
        title = "NOT APPROVED"
    
    st.markdown(f"""
        <div class="decision-card {card_class}">
            <div class="decision-icon">{icon}</div>
            <div class="decision-title">{title}</div>
            <div class="decision-confidence">Confidence: {confidence:.0%}</div>
        </div>
    """, unsafe_allow_html=True)


def render_metric_row(metrics: list):
    """Render a row of metric cards."""
    cols = st.columns(len(metrics))
    for col, (label, value, icon) in zip(cols, metrics):
        with col:
            st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">{icon}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)


def render_score_breakdown(risk_scores: dict):
    """Render visual score breakdown."""
    veg = risk_scores.get('vegetation_score', 0) * 100
    climate = risk_scores.get('climate_score', 0) * 100
    sustain = risk_scores.get('sustainability_score', 0) * 100
    
    st.markdown(f"""
        <div style="margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: 600;">Risk Score Composition</span>
                <span style="color: #059669; font-weight: 700;">{risk_scores.get('composite_score', 0):.0%} Overall</span>
            </div>
            <div class="score-bar-container">
                <div class="score-bar-segment" style="width: 40%; background: #059669;">Veg {veg:.0f}%</div>
                <div class="score-bar-segment" style="width: 30%; background: #0891b2;">Climate {climate:.0f}%</div>
                <div class="score-bar-segment" style="width: 30%; background: #7c3aed;">Sustain {sustain:.0f}%</div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">
                <span>🌿 40% weight</span>
                <span>🌤️ 30% weight</span>
                <span>💧 30% weight</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Analysis Function
# ---------------------------------------------------------------------------
def run_analysis(lat: float, lon: float, context: str, use_multi_agent: bool = False) -> Dict[str, Any]:
    """Orchestrates the backend services."""
    if use_multi_agent and MULTI_AGENT_AVAILABLE:
        return process_loan_with_agents(lat, lon, context)
    
    farm_data = satellite_service.get_farm_ndvi(lat, lon)
    
    if farm_data.get("error") and "Simulated" not in farm_data.get("status", ""):
        return {"farm_data": farm_data, "weather_data": None, "llm_result": None}
    
    weather_data = weather_service.get_weather_analysis(lat, lon)
    combined_data = {**farm_data, "weather": weather_data}
    llm_result = llm_service.analyze_loan_risk(combined_data, user_request=context)
    
    return {"farm_data": farm_data, "weather_data": weather_data, "llm_result": llm_result}


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
def main():
    setup_page()

    # Session State
    if "lat" not in st.session_state: st.session_state.lat = 37.669
    if "lon" not in st.session_state: st.session_state.lon = -100.749
    if "analysis_result" not in st.session_state: st.session_state.analysis_result = None
    if "current_step" not in st.session_state: st.session_state.current_step = 1

    # Hero Header
    render_hero()
    
    # Determine current step
    current_step = 1
    if st.session_state.analysis_result:
        current_step = 4
    
    # Step Indicators
    render_step_indicators(current_step)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main Layout
    col_left, col_right = st.columns([1.2, 1.8], gap="large")
    
    # =========================================================================
    # LEFT COLUMN - Controls
    # =========================================================================
    with col_left:
        # Location Selection Card
        with st.container(border=True):
            st.markdown("#### 📍 Farm Location")
            
            # Quick location buttons
            st.markdown("**Quick Select:**")
            loc_cols = st.columns(3)
            
            sample_locations = [
                ("🇺🇸 Kansas", 37.669, -100.749),
                ("🇮🇳 Punjab", 29.605, 76.273),
                ("🇧🇷 Brazil", -15.826, -47.921),
            ]
            
            for col, (name, lat, lon) in zip(loc_cols, sample_locations):
                with col:
                    if st.button(name, use_container_width=True, key=f"loc_{name}"):
                        st.session_state.lat = lat
                        st.session_state.lon = lon
                        st.session_state.analysis_result = None
                        st.rerun()
            
            st.markdown("---")
            
            # Manual coordinate input
            col_lat, col_lon = st.columns(2)
            with col_lat:
                new_lat = st.number_input("Latitude", value=st.session_state.lat, 
                                          format="%.4f", min_value=-90.0, max_value=90.0)
            with col_lon:
                new_lon = st.number_input("Longitude", value=st.session_state.lon,
                                          format="%.4f", min_value=-180.0, max_value=180.0)
            
            if new_lat != st.session_state.lat or new_lon != st.session_state.lon:
                st.session_state.lat = new_lat
                st.session_state.lon = new_lon
                st.session_state.analysis_result = None
        
        # Configuration Card
        with st.container(border=True):
            st.markdown("#### ⚙️ Analysis Settings")
            
            # Multi-Agent Toggle (prominent)
            use_multi_agent = st.toggle(
                "🤖 **Multi-Agent System**",
                value=True,
                help="Uses 3 specialized AI agents: Field Scout, Risk Analyst, and Loan Officer"
            )
            
            col_mock1, col_mock2 = st.columns(2)
            with col_mock1:
                mock_mode = st.toggle("⚡ Fast Mode", value=True, help="Use simulated data for quick demo")
            with col_mock2:
                mock_llm = st.toggle("🧠 Mock AI", value=True, help="Skip API call (no key needed)")
            
            satellite_service.MOCK_MODE = mock_mode
            weather_service.MOCK_MODE = mock_mode
            llm_service.MOCK_MODE = mock_llm
            
            st.markdown("---")
            
            loan_purpose = st.text_area(
                "💰 Loan Purpose",
                value="Expansion of organic wheat farming with drip irrigation system installation.",
                height=80
            )
            
            # Big Run Button
            st.markdown("<br>", unsafe_allow_html=True)
            run_btn = st.button(
                "🚀 **Run Verification Analysis**",
                type="primary",
                use_container_width=True
            )
    
    # =========================================================================
    # RIGHT COLUMN - Map & Results
    # =========================================================================
    with col_right:
        # Interactive Map
        with st.container(border=True):
            st.markdown("#### 🗺️ Farm Location Preview")
            
            m = folium.Map(
                location=[st.session_state.lat, st.session_state.lon],
                zoom_start=12,
                tiles="OpenStreetMap"
            )
            
            # Add satellite tile layer option
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite',
                overlay=False
            ).add_to(m)
            
            folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
            folium.LayerControl().add_to(m)
            
            # Farm marker with popup
            popup_html = f"""
                <div style="font-family: Inter, sans-serif; min-width: 150px;">
                    <b>🌱 Target Farm</b><br>
                    <small>Lat: {st.session_state.lat:.4f}</small><br>
                    <small>Lon: {st.session_state.lon:.4f}</small>
                </div>
            """
            
            folium.Marker(
                [st.session_state.lat, st.session_state.lon],
                popup=folium.Popup(popup_html, max_width=200),
                icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
                tooltip="Click for details"
            ).add_to(m)
            
            # Add a circle to show analysis area
            folium.Circle(
                [st.session_state.lat, st.session_state.lon],
                radius=500,
                color='#059669',
                fill=True,
                fillOpacity=0.1,
                weight=2,
                tooltip="Analysis Area (500m radius)"
            ).add_to(m)
            
            map_data = st_folium(m, height=350, width=None, key="main_map", returned_objects=[])
    
    # =========================================================================
    # ANALYSIS EXECUTION
    # =========================================================================
    if run_btn:
        with st.container(border=True):
            st.markdown("### 🔄 Analysis in Progress")
            
            if use_multi_agent:
                render_agent_pipeline([], is_running=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Simulate staged progress for better UX
                stages = [
                    (0.33, "🛰️ Field Scout: Acquiring satellite imagery..."),
                    (0.66, "📊 Risk Analyst: Computing sustainability scores..."),
                    (1.0, "🏦 Loan Officer: Generating decision...")
                ]
                
                for progress, message in stages:
                    status_text.markdown(f"**{message}**")
                    time.sleep(0.3)
                    progress_bar.progress(progress)
            else:
                with st.spinner("Processing..."):
                    time.sleep(0.5)
            
            # Run the actual analysis
            result = run_analysis(
                st.session_state.lat,
                st.session_state.lon,
                loan_purpose,
                use_multi_agent
            )
            
            if result["farm_data"].get("error") and "Simulated" not in result["farm_data"].get("status", ""):
                st.error(f"❌ Analysis failed: {result['farm_data']['error']}")
            else:
                st.session_state.analysis_result = result
                st.session_state.used_multi_agent = use_multi_agent
                st.rerun()
    
    # =========================================================================
    # RESULTS DISPLAY
    # =========================================================================
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        farm = res["farm_data"]
        weather = res.get("weather_data", {})
        llm = res["llm_result"]
        decision = llm.get('decision', 'PENDING')
        confidence = llm.get('confidence', 0)
        
        st.markdown("---")
        st.markdown("## 📊 Verification Results")
        
        # Decision Card (Most Important - Top)
        render_decision_card(decision, confidence)
        
        # Celebration for approved
        if "APPROVED" in decision:
            st.balloons()
        
        # Key Metrics Row
        st.markdown("### 📈 Key Indicators")
        metrics = [
            ("NDVI Score", f"{farm.get('ndvi_score', 0):.2f}", "🌿"),
            ("Vegetation", farm.get('status', 'N/A'), "🌾"),
            ("Weather Risk", f"{weather.get('weather_risk_score', 0):.0%}" if weather else "N/A", "🌤️"),
            ("Confidence", f"{confidence:.0%}", "🎯")
        ]
        render_metric_row(metrics)
        
        # Multi-Agent Section
        if st.session_state.get("used_multi_agent") and res.get("agent_trace"):
            st.markdown("### 🤖 Agent Workflow")
            render_agent_pipeline(res.get("agent_trace", []))
            
            if res.get("risk_scores"):
                render_score_breakdown(res["risk_scores"])
        
        # Detailed Analysis Tabs
        st.markdown("### 📋 Detailed Analysis")
        tab1, tab2, tab3 = st.tabs(["🧠 AI Reasoning", "🌤️ Climate Data", "🔐 Certificate"])
        
        with tab1:
            with st.container(border=True):
                st.markdown(llm.get('reasoning', 'No reasoning available.'))
                
                if llm.get('recommendations'):
                    st.markdown("**📌 Recommendations:**")
                    for rec in llm['recommendations']:
                        st.markdown(f"- {rec}")
        
        with tab2:
            if weather and not weather.get("error"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🌧️ Total Rainfall", f"{weather.get('rainfall_total_mm', 'N/A')} mm")
                    st.metric("🌡️ Avg Temperature", f"{weather.get('temperature_avg_c', 'N/A')}°C")
                    st.metric("📅 Data Period", f"{weather.get('data_period', {}).get('days', 90)} days")
                with col2:
                    st.metric("☀️ Drought Risk", f"{weather.get('drought_risk_score', 0):.0%}")
                    st.metric("❄️ Frost Days", weather.get('frost_days', 'N/A'))
                    st.metric("🌱 Growing Degree Days", weather.get('growing_degree_days', 'N/A'))
            else:
                st.info("Weather data not available for this analysis.")
        
        with tab3:
            if "APPROVED" in decision or "CONDITIONAL" in decision:
                # Generate blockchain hash
                tx_hash = generate_blockchain_hash(farm, llm)
                
                st.markdown("**⛓️ Blockchain Verification**")
                st.markdown(f'<div class="blockchain-hash">{tx_hash}</div>', unsafe_allow_html=True)
                
                st.markdown("**📜 Green Certificate**")
                st.info("Your sustainable farming verification is ready for download.")
                
                # Generate and offer PDF
                try:
                    pdf_path, _ = create_green_certificate(farm, llm)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Certificate (PDF)",
                            data=f,
                            file_name="GreenChain_Verification_Certificate.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Certificate generation failed: {e}")
            else:
                st.warning("Certificate is only available for approved or conditionally approved applications.")
        
        # Reset Button
        st.markdown("---")
        if st.button("🔄 Start New Analysis", use_container_width=True):
            st.session_state.analysis_result = None
            st.rerun()


if __name__ == "__main__":
    main()
