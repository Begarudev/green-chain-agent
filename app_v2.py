"""
🌱 GreenChain Agent - AI-Powered Sustainable Finance
Version 2: Wizard-based UX with Progressive Disclosure
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
    st.error(f"Backend Import Error: {e}")
    MULTI_AGENT_AVAILABLE = False
    st.stop()


# ---------------------------------------------------------------------------
# Page Config & Styles
# ---------------------------------------------------------------------------
def setup_page():
    st.set_page_config(
        page_title="GreenChain",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        
        /* Clean slate */
        .block-container { 
            padding: 2rem 3rem; 
            max-width: 1100px; 
        }
        #MainMenu, footer, header { visibility: hidden; }
        
        /* Centered container */
        .main-container {
            max-width: 700px;
            margin: 0 auto;
        }
        
        /* Logo/Brand */
        .brand {
            text-align: center;
            padding: 1rem 0 2rem;
        }
        .brand-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        .brand-name {
            font-size: 1.5rem;
            font-weight: 700;
            color: #064e3b;
            letter-spacing: -0.5px;
        }
        .brand-tagline {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        /* Progress Steps */
        .progress-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 2rem 0;
            gap: 0.5rem;
        }
        .progress-step {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s;
        }
        .progress-step.completed {
            background: #059669;
            color: white;
        }
        .progress-step.active {
            background: #064e3b;
            color: white;
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(6, 78, 59, 0.4);
        }
        .progress-step.pending {
            background: #e5e7eb;
            color: #9ca3af;
        }
        .progress-line {
            width: 60px;
            height: 3px;
            background: #e5e7eb;
            border-radius: 2px;
        }
        .progress-line.completed {
            background: #059669;
        }
        
        /* Card Styles */
        .card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }
        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.5rem;
        }
        .card-subtitle {
            color: #6b7280;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }
        
        /* Location Cards */
        .location-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1.5rem 0;
        }
        .location-card {
            background: #f9fafb;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .location-card:hover {
            border-color: #059669;
            background: #ecfdf5;
        }
        .location-card.selected {
            border-color: #059669;
            background: #ecfdf5;
            box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.2);
        }
        .location-flag {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .location-name {
            font-weight: 600;
            color: #111827;
        }
        .location-region {
            font-size: 0.8rem;
            color: #6b7280;
        }
        
        /* Big Button */
        .big-button {
            width: 100%;
            padding: 1rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 1.5rem;
        }
        .big-button.primary {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
        }
        .big-button.primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(5, 150, 105, 0.4);
        }
        .big-button.secondary {
            background: #f3f4f6;
            color: #374151;
        }
        
        /* Processing Animation */
        .processing-container {
            text-align: center;
            padding: 3rem 2rem;
        }
        .processing-icon {
            font-size: 4rem;
            animation: bounce 1s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .processing-text {
            font-size: 1.25rem;
            font-weight: 600;
            color: #111827;
            margin: 1rem 0 0.5rem;
        }
        .processing-subtext {
            color: #6b7280;
        }
        
        /* Agent Steps */
        .agent-steps {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin: 2rem 0;
            text-align: left;
        }
        .agent-step {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            background: #f9fafb;
            border-radius: 8px;
            transition: all 0.3s;
        }
        .agent-step.active {
            background: #ecfdf5;
            border-left: 3px solid #059669;
        }
        .agent-step.done {
            background: #f0fdf4;
        }
        .agent-step-icon {
            font-size: 1.5rem;
        }
        .agent-step-text {
            flex: 1;
        }
        .agent-step-name {
            font-weight: 600;
            color: #111827;
        }
        .agent-step-status {
            font-size: 0.8rem;
            color: #6b7280;
        }
        .agent-step-check {
            color: #059669;
            font-size: 1.25rem;
        }
        
        /* Result Styles */
        .result-hero {
            text-align: center;
            padding: 2rem;
        }
        .result-icon {
            font-size: 5rem;
            margin-bottom: 1rem;
        }
        .result-title {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .result-title.approved { color: #059669; }
        .result-title.conditional { color: #d97706; }
        .result-title.rejected { color: #dc2626; }
        
        .result-confidence {
            display: inline-block;
            background: #f3f4f6;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            color: #374151;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin: 1.5rem 0;
        }
        .stat-box {
            background: #f9fafb;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #064e3b;
        }
        .stat-label {
            font-size: 0.75rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Expandable Section */
        .expand-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem;
            background: #f9fafb;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 1rem;
        }
        
        /* Certificate Box */
        .cert-box {
            background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
            border-radius: 12px;
            padding: 1.5rem;
            color: white;
            margin: 1rem 0;
        }
        .cert-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .cert-hash {
            font-family: monospace;
            font-size: 0.75rem;
            background: rgba(0,0,0,0.2);
            padding: 0.5rem;
            border-radius: 6px;
            word-break: break-all;
        }
        
        /* Hide streamlit elements */
        div[data-testid="stDecoration"] { display: none; }
        .stDeployButton { display: none; }
        
        /* Map container styling */
        iframe {
            border-radius: 12px !important;
            border: 2px solid #e5e7eb !important;
        }
        
        /* Leaflet customization */
        .leaflet-control-layers {
            border-radius: 8px !important;
            border: none !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
        }
        
        .leaflet-control-zoom a {
            background: white !important;
            color: #064e3b !important;
            border: none !important;
        }
        
        .leaflet-control-zoom a:hover {
            background: #ecfdf5 !important;
        }
        </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def render_brand():
    st.markdown("""
        <div class="brand">
            <div class="brand-icon">🌱</div>
            <div class="brand-name">GreenChain</div>
            <div class="brand-tagline">AI-Powered Sustainable Finance</div>
        </div>
    """, unsafe_allow_html=True)


def render_progress(current: int):
    steps_html = ""
    for i in range(1, 4):
        if i < current:
            step_class = "completed"
            content = "✓"
        elif i == current:
            step_class = "active"
            content = str(i)
        else:
            step_class = "pending"
            content = str(i)
        steps_html += f'<div class="progress-step {step_class}">{content}</div>'
        if i < 3:
            line_class = "completed" if i < current else ""
            steps_html += f'<div class="progress-line {line_class}"></div>'
    
    st.markdown(f'<div class="progress-container">{steps_html}</div>', unsafe_allow_html=True)


def run_analysis(lat: float, lon: float, purpose: str) -> Dict[str, Any]:
    """Run the multi-agent analysis."""
    satellite_service.MOCK_MODE = True
    weather_service.MOCK_MODE = True
    llm_service.MOCK_MODE = True
    
    if MULTI_AGENT_AVAILABLE:
        return process_loan_with_agents(lat, lon, purpose)
    
    farm_data = satellite_service.get_farm_ndvi(lat, lon)
    weather_data = weather_service.get_weather_analysis(lat, lon)
    combined_data = {**farm_data, "weather": weather_data}
    llm_result = llm_service.analyze_loan_risk(combined_data, user_request=purpose)
    return {"farm_data": farm_data, "weather_data": weather_data, "llm_result": llm_result}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_select_location():
    """Step 1: Location Selection"""
    render_progress(1)
    
    st.markdown("""
        <div class="card">
            <div class="card-title">Where is your farm located?</div>
            <div class="card-subtitle">Click on the map to select your farm location, or use quick presets</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Two column layout: Map on left, controls on right
    col_map, col_controls = st.columns([1.5, 1], gap="large")
    
    with col_map:
        st.markdown("**🗺️ Click on the map to select location:**")
        
        # Get current location or default
        current_lat = st.session_state.get("lat", 20.0)
        current_lon = st.session_state.get("lon", 0.0)
        
        # Create interactive map with custom green theme
        m = folium.Map(
            location=[current_lat, current_lon],
            zoom_start=3 if current_lat == 20.0 else 10,
            tiles=None  # We'll add custom tiles
        )
        
        # Add custom styled base layer (CartoDB Positron - clean minimal style)
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            name='Clean Map',
            overlay=False
        ).add_to(m)
        
        # Add satellite layer as option
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite View',
            overlay=False
        ).add_to(m)
        
        # Add terrain layer
        folium.TileLayer(
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='OpenTopoMap',
            name='Terrain',
            overlay=False
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        # Add marker if location is selected
        if "lat" in st.session_state and st.session_state.lat != 20.0:
            # Custom green icon matching app theme
            folium.Marker(
                [st.session_state.lat, st.session_state.lon],
                popup=f"<div style='font-family: Inter, sans-serif;'><b>🌱 Selected Farm</b><br>{st.session_state.lat:.4f}, {st.session_state.lon:.4f}</div>",
                icon=folium.DivIcon(
                    html='''
                        <div style="
                            background: linear-gradient(135deg, #059669 0%, #047857 100%);
                            width: 36px;
                            height: 36px;
                            border-radius: 50% 50% 50% 0;
                            transform: rotate(-45deg);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            box-shadow: 0 4px 12px rgba(5, 150, 105, 0.4);
                            border: 3px solid white;
                        ">
                            <span style="transform: rotate(45deg); font-size: 16px;">🌱</span>
                        </div>
                    ''',
                    icon_size=(36, 36),
                    icon_anchor=(18, 36)
                )
            ).add_to(m)
            
            # Analysis area circle with theme color
            folium.Circle(
                [st.session_state.lat, st.session_state.lon],
                radius=1000,
                color='#059669',
                fill=True,
                fill_color='#059669',
                fillOpacity=0.15,
                weight=2,
                dash_array='5, 5',
                tooltip="Analysis area (~1km radius)"
            ).add_to(m)
        
        # Render map and capture clicks
        map_data = st_folium(
            m, 
            height=400, 
            width=None, 
            key="location_map",
            returned_objects=["last_clicked"]
        )
        
        # Handle map clicks
        if map_data and map_data.get("last_clicked"):
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lon = map_data["last_clicked"]["lng"]
            if clicked_lat != st.session_state.get("lat") or clicked_lon != st.session_state.get("lon"):
                st.session_state.lat = clicked_lat
                st.session_state.lon = clicked_lon
                st.rerun()
    
    with col_controls:
        # Quick presets
        st.markdown("**⚡ Quick Presets:**")
        
        locations = [
            ("🇺🇸 Kansas, USA", 37.669, -100.749),
            ("🇮🇳 Punjab, India", 29.605, 76.273),
            ("🇧🇷 Goiás, Brazil", -15.826, -47.921),
            ("🇰🇪 Nairobi, Kenya", -1.286, 36.817),
            ("🇦🇺 Queensland, AU", -20.917, 142.702),
        ]
        
        for name, lat, lon in locations:
            is_selected = (st.session_state.get("lat") == lat and st.session_state.get("lon") == lon)
            if st.button(
                name,
                key=f"loc_{name}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.rerun()
        
        st.markdown("---")
        
        # Manual coordinate input
        st.markdown("**📍 Or enter coordinates:**")
        col1, col2 = st.columns(2)
        with col1:
            manual_lat = st.number_input(
                "Latitude", 
                value=st.session_state.get("lat", 37.669), 
                format="%.4f",
                min_value=-90.0,
                max_value=90.0
            )
        with col2:
            manual_lon = st.number_input(
                "Longitude", 
                value=st.session_state.get("lon", -100.749), 
                format="%.4f",
                min_value=-180.0,
                max_value=180.0
            )
        
        if manual_lat != st.session_state.get("lat") or manual_lon != st.session_state.get("lon"):
            if st.button("📍 Go to coordinates", use_container_width=True):
                st.session_state.lat = manual_lat
                st.session_state.lon = manual_lon
                st.rerun()
        
        # Show selected coordinates
        if "lat" in st.session_state and st.session_state.lat != 20.0:
            st.markdown("---")
            st.success(f"**Selected:** {st.session_state.lat:.4f}, {st.session_state.lon:.4f}")
            
            # Next button
            if st.button("Continue →", type="primary", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        else:
            st.info("👆 Click on the map or select a preset to choose your farm location")


def page_loan_details():
    """Step 2: Loan Purpose"""
    render_progress(2)
    
    st.markdown("""
        <div class="card">
            <div class="card-title">Tell us about your loan</div>
            <div class="card-subtitle">This helps our AI make a better assessment</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick purpose selection
    purposes = [
        ("🌾", "Crop Expansion", "Expand cultivation area or try new crops"),
        ("💧", "Irrigation System", "Install drip or sprinkler irrigation"),
        ("🚜", "Equipment", "Purchase farming equipment or machinery"),
        ("🌿", "Organic Transition", "Convert to organic farming practices"),
    ]
    
    cols = st.columns(2)
    for i, (icon, title, desc) in enumerate(purposes):
        with cols[i % 2]:
            if st.button(f"{icon} **{title}**\n\n{desc}", key=f"purpose_{i}", use_container_width=True):
                st.session_state.loan_purpose = f"{title}: {desc}"
    
    st.markdown("---")
    
    # Custom input
    purpose = st.text_area(
        "Or describe your purpose:",
        value=st.session_state.get("loan_purpose", ""),
        placeholder="e.g., Installing solar-powered drip irrigation for my wheat farm...",
        height=100
    )
    st.session_state.loan_purpose = purpose
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Analyze My Farm →", type="primary", use_container_width=True, disabled=not purpose):
            st.session_state.step = 3
            st.rerun()


def page_processing():
    """Step 3: Processing with animation"""
    render_progress(3)
    
    st.markdown("""
        <div class="card">
            <div class="processing-container">
                <div class="processing-icon">🛰️</div>
                <div class="processing-text">Analyzing Your Farm</div>
                <div class="processing-subtext">Our AI agents are working...</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Agent progress
    agents = [
        ("🛰️", "Field Scout", "Fetching satellite & weather data"),
        ("📊", "Risk Analyst", "Calculating sustainability scores"),
        ("🏦", "Loan Officer", "Making final decision"),
    ]
    
    progress_placeholder = st.empty()
    
    for step, (icon, name, desc) in enumerate(agents):
        # Build agent steps HTML
        html = '<div class="agent-steps">'
        for i, (ic, nm, ds) in enumerate(agents):
            if i < step:
                html += f'''
                    <div class="agent-step done">
                        <div class="agent-step-icon">{ic}</div>
                        <div class="agent-step-text">
                            <div class="agent-step-name">{nm}</div>
                            <div class="agent-step-status">{ds}</div>
                        </div>
                        <div class="agent-step-check">✓</div>
                    </div>
                '''
            elif i == step:
                html += f'''
                    <div class="agent-step active">
                        <div class="agent-step-icon">{ic}</div>
                        <div class="agent-step-text">
                            <div class="agent-step-name">{nm}</div>
                            <div class="agent-step-status">Processing...</div>
                        </div>
                    </div>
                '''
            else:
                html += f'''
                    <div class="agent-step">
                        <div class="agent-step-icon">{ic}</div>
                        <div class="agent-step-text">
                            <div class="agent-step-name">{nm}</div>
                            <div class="agent-step-status">Waiting</div>
                        </div>
                    </div>
                '''
        html += '</div>'
        progress_placeholder.markdown(html, unsafe_allow_html=True)
        time.sleep(0.8)
    
    # Run actual analysis
    result = run_analysis(
        st.session_state.lat,
        st.session_state.lon,
        st.session_state.loan_purpose
    )
    st.session_state.result = result
    
    # Show completion
    html = '<div class="agent-steps">'
    for ic, nm, ds in agents:
        html += f'''
            <div class="agent-step done">
                <div class="agent-step-icon">{ic}</div>
                <div class="agent-step-text">
                    <div class="agent-step-name">{nm}</div>
                    <div class="agent-step-status">Complete</div>
                </div>
                <div class="agent-step-check">✓</div>
            </div>
        '''
    html += '</div>'
    progress_placeholder.markdown(html, unsafe_allow_html=True)
    
    time.sleep(0.5)
    st.session_state.step = 4
    st.rerun()


def page_results():
    """Step 4: Results"""
    result = st.session_state.result
    farm = result.get("farm_data", {})
    weather = result.get("weather_data", {})
    llm = result.get("llm_result", {})
    risk_scores = result.get("risk_scores", {})
    
    decision = llm.get("decision", "PENDING")
    confidence = llm.get("confidence", 0)
    
    # Decision Hero
    if "APPROVED" in decision:
        icon, title, css_class = "🎉", "Approved!", "approved"
        st.balloons()
    elif "CONDITIONAL" in decision:
        icon, title, css_class = "⚡", "Conditionally Approved", "conditional"
    else:
        icon, title, css_class = "😔", "Not Approved", "rejected"
    
    st.markdown(f"""
        <div class="result-hero">
            <div class="result-icon">{icon}</div>
            <div class="result-title {css_class}">{title}</div>
            <div class="result-confidence">Confidence: {confidence:.0%}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Key Stats
    st.markdown("""
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value">{:.2f}</div>
                <div class="stat-label">NDVI Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{}</div>
                <div class="stat-label">Vegetation</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{:.0%}</div>
                <div class="stat-label">Weather Risk</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{:.0%}</div>
                <div class="stat-label">Overall Score</div>
            </div>
        </div>
    """.format(
        farm.get("ndvi_score", 0),
        farm.get("status", "N/A"),
        weather.get("weather_risk_score", 0) if weather else 0,
        risk_scores.get("composite_score", confidence)
    ), unsafe_allow_html=True)
    
    # Reasoning
    with st.expander("📝 View Detailed Analysis", expanded=False):
        st.markdown(llm.get("reasoning", "No analysis available."))
        
        if llm.get("recommendations"):
            st.markdown("**Recommendations:**")
            for rec in llm["recommendations"]:
                st.markdown(f"• {rec}")
    
    # Weather Details
    if weather:
        with st.expander("🌤️ Climate Data", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Rainfall", f"{weather.get('rainfall_total_mm', 'N/A')} mm")
            with col2:
                st.metric("Temperature", f"{weather.get('temperature_avg_c', 'N/A')}°C")
            with col3:
                st.metric("Drought Risk", f"{weather.get('drought_risk_score', 0):.0%}")
    
    # Certificate (if approved)
    if "APPROVED" in decision or "CONDITIONAL" in decision:
        tx_hash = generate_blockchain_hash(farm, llm)
        
        st.markdown(f"""
            <div class="cert-box">
                <div class="cert-title">🔐 Blockchain Verification</div>
                <div class="cert-hash">{tx_hash}</div>
            </div>
        """, unsafe_allow_html=True)
        
        try:
            pdf_path, _ = create_green_certificate(farm, llm)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📄 Download Certificate",
                    data=f,
                    file_name="GreenChain_Certificate.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Could not generate certificate: {e}")
    
    st.markdown("---")
    
    # Start over
    if st.button("🔄 Start New Application", use_container_width=True):
        for key in ["step", "lat", "lon", "loan_purpose", "result"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------
def main():
    setup_page()
    
    # Initialize
    if "step" not in st.session_state:
        st.session_state.step = 1
    
    # Brand header
    render_brand()
    
    # Route to correct page
    step = st.session_state.step
    
    if step == 1:
        page_select_location()
    elif step == 2:
        page_loan_details()
    elif step == 3:
        page_processing()
    elif step == 4:
        page_results()


if __name__ == "__main__":
    main()
