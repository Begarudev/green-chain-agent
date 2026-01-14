"""
🌱 GreenChain Agent - AI-Powered Sustainable Finance
Features:
- Multi-temporal NDVI analysis (6 months trend)
- Deforestation detection
- Polygon farm boundary selection
- Transparent structured scoring model
"""

import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px

# Import translations
from translations import LANGUAGES, t, get_text

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
    from services.advanced_satellite_service import (
        get_multi_temporal_ndvi,
        check_deforestation,
        calculate_sustainability_score,
        calculate_loan_risk_score,
    )
    from services.verification_service import (
        create_green_certificate,
        generate_blockchain_hash,
    )
    from services.rag_service import (
        get_compliance_context,
        get_index,
    )
    from services.analysis_service import (
        generate_metric_explanations,
    )
    SERVICES_AVAILABLE = True
except ImportError as e:
    st.error(f"Backend Import Error: {e}")
    SERVICES_AVAILABLE = False
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
        
        .block-container { 
            padding: 2rem 3rem; 
            max-width: 1200px; 
        }
        #MainMenu, footer, header { visibility: hidden; }
        
        /* Brand */
        .brand {
            text-align: center;
            padding: 1rem 0 2rem;
        }
        .brand-icon { font-size: 3rem; margin-bottom: 0.5rem; }
        .brand-name { font-size: 1.5rem; font-weight: 700; color: #064e3b; letter-spacing: -0.5px; }
        .brand-tagline { color: #6b7280; font-size: 0.9rem; }
        .version-badge {
            display: inline-block;
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: white;
            font-size: 0.65rem;
            padding: 0.2rem 0.5rem;
            border-radius: 10px;
            margin-left: 0.5rem;
            vertical-align: super;
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
        .progress-step.completed { background: #059669; color: white; }
        .progress-step.active {
            background: #064e3b;
            color: white;
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(6, 78, 59, 0.4);
        }
        .progress-step.pending { background: #e5e7eb; color: #9ca3af; }
        .progress-line { width: 60px; height: 3px; background: #e5e7eb; border-radius: 2px; }
        .progress-line.completed { background: #059669; }

        /* Override Streamlit blue halo */
        .stApp {
            background: #ffffff;
        }
        div[data-testid="stAppViewBlockContainer"] {
            box-shadow: 0 10px 40px rgba(5, 150, 105, 0.08) !important;
            border-radius: 24px;
            background: white;
            margin-top: 2rem;
            margin-bottom: 2rem;
            border: 1px solid #f0fdf4;
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
        .card-title { font-size: 1.25rem; font-weight: 700; color: #111827; margin-bottom: 0.5rem; }
        .card-subtitle { color: #6b7280; font-size: 0.9rem; margin-bottom: 1.5rem; }
        
        /* Score Card */
        .score-card {
            background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
            border-radius: 16px;
            padding: 2rem;
            color: white;
            text-align: center;
        }
        .score-value { font-size: 4rem; font-weight: 800; line-height: 1; }
        .score-grade { font-size: 1.5rem; font-weight: 600; opacity: 0.9; }
        .score-label { font-size: 0.9rem; opacity: 0.8; margin-top: 0.5rem; }
        
        /* Component Score */
        .component-row {
            display: flex;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f3f4f6;
        }
        .component-icon { font-size: 1.5rem; width: 40px; }
        .component-name { flex: 1; font-weight: 500; color: #374151; }
        .component-bar-container { width: 120px; height: 8px; background: #e5e7eb; border-radius: 4px; margin: 0 1rem; }
        .component-bar { height: 100%; border-radius: 4px; }
        .component-value { width: 50px; text-align: right; font-weight: 600; color: #064e3b; }
        
        /* Risk/Positive Factor */
        .factor-item {
            display: flex;
            align-items: center;
            padding: 0.5rem 0.75rem;
            border-radius: 8px;
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }
        .factor-risk { background: #fef2f2; color: #991b1b; }
        .factor-positive { background: #f0fdf4; color: #166534; }
        
        /* Result Styles */
        .result-hero { text-align: center; padding: 2rem; }
        .result-icon { font-size: 5rem; margin-bottom: 1rem; }
        .result-title { font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; }
        .result-title.approved { color: #059669; }
        .result-title.conditional { color: #d97706; }
        .result-title.rejected { color: #dc2626; }
        
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
        .stat-value { font-size: 1.5rem; font-weight: 700; color: #064e3b; }
        .stat-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Certificate Box */
        .cert-box {
            background: linear-gradient(135deg, #064e3b 0%, #047857 100%);
            border-radius: 12px;
            padding: 1.5rem;
            color: white;
            margin: 1rem 0;
        }
        .cert-title { font-weight: 600; margin-bottom: 0.5rem; }
        .cert-hash {
            font-family: monospace;
            font-size: 0.75rem;
            background: rgba(0,0,0,0.2);
            padding: 0.5rem;
            border-radius: 6px;
            word-break: break-all;
        }
        
        /* Map container */
        iframe { border-radius: 12px !important; border: 2px solid #e5e7eb !important; }
        
        /* Hide streamlit elements */
        div[data-testid="stDecoration"] { display: none; }
        .stDeployButton { display: none; }
        </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def render_language_selector():
    """Render language selector."""
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    col1, col2 = st.columns([4, 1])
    with col2:
        current_lang = st.session_state.language
        lang_options = list(LANGUAGES.keys())
        lang_labels = list(LANGUAGES.values())
        current_idx = lang_options.index(current_lang) if current_lang in lang_options else 0
        
        selected_label = st.selectbox(
            "🌍", lang_labels, index=current_idx, label_visibility="collapsed"
        )
        
        selected_lang = lang_options[lang_labels.index(selected_label)]
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()


def render_brand():
    st.markdown(f"""
        <div class="brand">
            <div class="brand-icon">🌱</div>
            <div class="brand-name">
                {t('brand_name')}
            </div>
            <div class="brand-tagline">{t('brand_tagline')} • Multi-Temporal Analysis</div>
        </div>
    """, unsafe_allow_html=True)


def render_progress(current: int, total: int = 4):
    steps_html = ""
    for i in range(1, total + 1):
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
        if i < total:
            line_class = "completed" if i < current else ""
            steps_html += f'<div class="progress-line {line_class}"></div>'
    
    st.markdown(f'<div class="progress-container">{steps_html}</div>', unsafe_allow_html=True)


def render_sustainability_score(sustainability: Dict[str, Any]):
    """Render the sustainability score card with component breakdown."""
    overall = sustainability.get("overall_score", 0)
    grade = sustainability.get("grade", "N/A")
    components = sustainability.get("component_scores", {})
    
    # Main score
    st.markdown(f"""
        <div class="score-card">
            <div class="score-value">{overall}</div>
            <div class="score-grade">Grade {grade}</div>
            <div class="score-label">{sustainability.get('interpretation', '')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Score Components")
    
    # Component breakdown
    component_info = [
        ("📈", "Vegetation Trend", components.get("trend_score", 0), "#10b981"),
        ("🔄", "Farming Consistency", components.get("consistency_score", 0), "#3b82f6"),
        ("🌳", "No Deforestation", components.get("deforestation_score", 0), "#059669"),
        ("☁️", "Climate Resilience", components.get("climate_score", 0), "#8b5cf6"),
    ]
    
    for icon, name, score, color in component_info:
        bar_width = max(5, score)  # Minimum 5% for visibility
        st.markdown(f"""
            <div class="component-row">
                <div class="component-icon">{icon}</div>
                <div class="component-name">{name}</div>
                <div class="component-bar-container">
                    <div class="component-bar" style="width: {bar_width}%; background: {color};"></div>
                </div>
                <div class="component-value">{score}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Risk and positive factors
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚠️ Risk Factors")
        risk_factors = sustainability.get("risk_factors", [])
        if risk_factors:
            for factor in risk_factors:
                st.markdown(f'<div class="factor-item factor-risk">⚠️ {factor}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="factor-item factor-positive">✓ No significant risks identified</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### ✓ Positive Factors")
        positive_factors = sustainability.get("positive_factors", [])
        if positive_factors:
            for factor in positive_factors:
                st.markdown(f'<div class="factor-item factor-positive">✓ {factor}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="factor-item factor-risk">No positive factors detected</div>', unsafe_allow_html=True)


def render_ndvi_trend_chart(temporal_data: Dict[str, Any]):
    """Render NDVI trend chart using Plotly."""
    monthly_data = temporal_data.get("monthly_data", [])
    
    if not monthly_data:
        st.warning("No temporal data available for chart")
        return
    
    months = [m["month"] for m in monthly_data]
    ndvi_values = [m["ndvi"] for m in monthly_data]
    
    # Create figure
    fig = go.Figure()
    
    # NDVI line
    fig.add_trace(go.Scatter(
        x=months,
        y=ndvi_values,
        mode='lines+markers',
        name='NDVI',
        line=dict(color='#059669', width=3),
        marker=dict(size=10, color='#059669'),
        fill='tozeroy',
        fillcolor='rgba(5, 150, 105, 0.1)'
    ))
    
    # Threshold lines
    fig.add_hline(y=0.5, line_dash="dash", line_color="#f59e0b", 
                  annotation_text="Good (0.5)", annotation_position="right")
    fig.add_hline(y=0.3, line_dash="dash", line_color="#ef4444",
                  annotation_text="Poor (0.3)", annotation_position="right")
    
    fig.update_layout(
        title="6-Month NDVI Trend Analysis",
        xaxis_title="Month",
        yaxis_title="NDVI Score",
        yaxis=dict(range=[0, 1]),
        template="plotly_white",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend summary
    trend_direction = temporal_data.get("trend_direction", "stable")
    ndvi_change = temporal_data.get("ndvi_change", 0)
    
    if trend_direction == "improving":
        icon, color = "📈", "#059669"
    elif trend_direction == "declining":
        icon, color = "📉", "#dc2626"
    else:
        icon, color = "➡️", "#6b7280"
    
    st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f9fafb; border-radius: 12px;">
            <span style="font-size: 1.5rem;">{icon}</span>
            <span style="font-weight: 600; color: {color}; margin-left: 0.5rem;">
                Trend: {trend_direction.title()} ({ndvi_change:+.3f})
            </span>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_select_location():
    """Step 1: Location Selection with Polygon Drawing"""
    render_progress(1)
    
    st.markdown(f"""
        <div class="card">
            <div class="card-title">📍 {t('select_location_title')}</div>
            <div class="card-subtitle">{t('select_location_desc')} <strong>Draw your farm boundary for more accurate analysis!</strong></div>
        </div>
    """, unsafe_allow_html=True)
    
    col_map, col_controls = st.columns([1.5, 1], gap="large")
    
    with col_map:
        st.markdown("**🗺️ Click to place marker OR draw polygon boundary**")
        
        current_lat = st.session_state.get("lat", 20.0)
        current_lon = st.session_state.get("lon", 0.0)
        
        # Create map with drawing tools
        m = folium.Map(
            location=[current_lat, current_lon],
            zoom_start=3 if current_lat == 20.0 else 12,
            tiles=None
        )
        
        # Base layers
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr='&copy; OpenStreetMap &copy; CARTO',
            name='Clean Map'
        ).add_to(m)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite View'
        ).add_to(m)
        
        folium.LayerControl().add_to(m)
        
        # Add drawing tools
        draw = Draw(
            draw_options={
                'polygon': {
                    'shapeOptions': {
                        'color': '#059669',
                        'fillColor': '#059669',
                        'fillOpacity': 0.3
                    }
                },
                'rectangle': {
                    'shapeOptions': {
                        'color': '#059669',
                        'fillColor': '#059669',
                        'fillOpacity': 0.3
                    }
                },
                'marker': True,
                'circlemarker': False,
                'circle': False,
                'polyline': False
            },
            edit_options={'edit': True, 'remove': True}
        )
        draw.add_to(m)
        
        # Show existing polygon or marker
        polygon = st.session_state.get("polygon")
        if polygon and len(polygon) >= 3:
            folium.Polygon(
                locations=[[p[1], p[0]] for p in polygon],  # Convert [lon, lat] to [lat, lon]
                color='#059669',
                fill=True,
                fillColor='#059669',
                fillOpacity=0.3,
                popup="Farm Boundary"
            ).add_to(m)
        elif "lat" in st.session_state and st.session_state.lat != 20.0:
            folium.Marker(
                [st.session_state.lat, st.session_state.lon],
                popup=f"Selected: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}",
                icon=folium.DivIcon(
                    html='''
                        <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%);
                            width: 36px; height: 36px; border-radius: 50% 50% 50% 0;
                            transform: rotate(-45deg); display: flex; align-items: center;
                            justify-content: center; box-shadow: 0 4px 12px rgba(5, 150, 105, 0.4);
                            border: 3px solid white;">
                            <span style="transform: rotate(45deg); font-size: 16px;">🌱</span>
                        </div>
                    ''',
                    icon_size=(36, 36),
                    icon_anchor=(18, 36)
                )
            ).add_to(m)
        
        # Render map
        map_data = st_folium(
            m, height=450, width=None, key="location_map",
            returned_objects=["last_clicked", "all_drawings"]
        )
        
        # Handle map interactions
        if map_data:
            # Check for drawn polygon
            if map_data.get("all_drawings"):
                drawings = map_data["all_drawings"]
                for drawing in drawings:
                    if drawing.get("geometry", {}).get("type") == "Polygon":
                        coords = drawing["geometry"]["coordinates"][0]
                        st.session_state.polygon = coords
                        # Set center point
                        lats = [c[1] for c in coords]
                        lons = [c[0] for c in coords]
                        st.session_state.lat = sum(lats) / len(lats)
                        st.session_state.lon = sum(lons) / len(lons)
                        st.rerun()
            
            # Handle click (if no polygon)
            elif map_data.get("last_clicked") and not st.session_state.get("polygon"):
                clicked_lat = map_data["last_clicked"]["lat"]
                clicked_lon = map_data["last_clicked"]["lng"]
                if clicked_lat != st.session_state.get("lat") or clicked_lon != st.session_state.get("lon"):
                    st.session_state.lat = clicked_lat
                    st.session_state.lon = clicked_lon
                    st.rerun()
    
    with col_controls:
        st.markdown(f"**⚡ {t('quick_select')}:**")
        
        locations = [
            ("🇺🇸 Kansas, USA", 37.669, -100.749),
            ("🇮🇳 Punjab, India", 29.605, 76.273),
            ("🇧🇷 Goiás, Brazil", -15.826, -47.921),
            ("🇰🇪 Nairobi, Kenya", -1.286, 36.817),
        ]
        
        for name, lat, lon in locations:
            if st.button(name, key=f"loc_{name}", use_container_width=True):
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.polygon = None  # Clear polygon for preset
                st.rerun()
        
        st.markdown("---")
        
        # Show selection status
        if st.session_state.get("polygon"):
            polygon = st.session_state.polygon
            area_approx = abs((polygon[0][0] - polygon[2][0]) * (polygon[0][1] - polygon[2][1])) * 111000 * 111000 / 10000
            st.success(f"""
                **🗺️ Farm Boundary Drawn**
                - Points: {len(polygon)}
                - Approx Area: {area_approx:.1f} hectares
                - Center: {st.session_state.lat:.4f}, {st.session_state.lon:.4f}
            """)
            
            if st.button("🗑️ Clear Boundary", use_container_width=True):
                st.session_state.polygon = None
                st.rerun()
        elif "lat" in st.session_state and st.session_state.lat != 20.0:
            st.success(f"**📍 Point Selected:** {st.session_state.lat:.4f}, {st.session_state.lon:.4f}")
            st.info("💡 Tip: Draw a polygon for more accurate analysis!")
        else:
            st.info("Click on map or draw a polygon to select your farm")
        
        st.markdown("---")
        
        # Next button
        can_proceed = ("lat" in st.session_state and st.session_state.lat != 20.0)
        if st.button(f"{t('continue')} →", type="primary", use_container_width=True, disabled=not can_proceed):
            st.session_state.step = 2
            st.rerun()


def page_loan_details():
    """Step 2: Loan Details"""
    render_progress(2)
    
    st.markdown(f"""
        <div class="card">
            <div class="card-title">💰 {t('loan_purpose_title')}</div>
            <div class="card-subtitle">{t('loan_purpose_desc')}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Loan amount
    loan_amount = st.slider(
        "Loan Amount (USD)",
        min_value=100,
        max_value=10000,
        value=st.session_state.get("loan_amount", 500),
        step=100
    )
    st.session_state.loan_amount = loan_amount
    
    # Purpose presets with sustainability indicators
    st.markdown("**Select Purpose (Sustainable options marked ✓):**")
    
    purposes = [
        ("✓ 💧 Drip Irrigation", "Install drip irrigation system for water efficiency", True),
        ("✓ ☀️ Solar Pump", "Solar-powered water pump for sustainable energy", True),
        ("✓ 🌿 Organic Inputs", "Purchase organic fertilizers and pest control", True),
        ("✓ 🔄 Crop Rotation", "Implement crop rotation for soil health", True),
        ("🚜 Equipment", "Purchase general farming equipment", False),
        ("🌾 Seeds & Supplies", "Buy seeds and farming supplies", False),
    ]
    
    cols = st.columns(3)
    for i, (label, desc, sustainable) in enumerate(purposes):
        with cols[i % 3]:
            btn_type = "primary" if sustainable else "secondary"
            if st.button(label, key=f"purpose_{i}", use_container_width=True, type=btn_type):
                st.session_state.loan_purpose = desc
    
    st.markdown("---")
    
    # Custom input
    purpose = st.text_area(
        t('loan_purpose_label'),
        value=st.session_state.get("loan_purpose", ""),
        placeholder=t('loan_purpose_placeholder'),
        height=100
    )
    st.session_state.loan_purpose = purpose
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"← {t('back')}", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button(f"{t('analyze')} →", type="primary", use_container_width=True, disabled=not purpose):
            st.session_state.step = 3
            st.rerun()


def page_processing():
    """Step 3: Enhanced Processing with Multi-Temporal Analysis"""
    render_progress(3)
    
    st.markdown(f"""
        <div class="card">
            <div style="text-align: center; padding: 1rem;">
                <div style="font-size: 3rem;">🔬</div>
                <div style="font-size: 1.25rem; font-weight: 600; margin: 0.5rem 0;">{t('processing_title')}</div>
                <div style="color: #6b7280;">Enhanced Multi-Temporal Analysis</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    
    lat = st.session_state.lat
    lon = st.session_state.lon
    polygon = st.session_state.get("polygon")
    purpose = st.session_state.loan_purpose
    loan_amount = st.session_state.get("loan_amount", 500)
    
    def update_status(icon, text, progress_val):
        status_placeholder.markdown(f"""
            <div style="background: #f0fdf4; border-left: 4px solid #059669; padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0;">
                <span style="margin-right: 0.5rem;">{icon}</span>
                <span style="color: #065f46;">{text}</span>
            </div>
        """, unsafe_allow_html=True)
        # Using a custom colored progress bar is hard with st.progress, but the theme will handle it
        progress_bar.progress(progress_val)
        time.sleep(0.3)
    
    # ========== ANALYSIS STEPS ==========
    
    # Step 1: Multi-temporal NDVI
    update_status("🛰️", "Fetching 6 months of satellite imagery...", 0.05)
    temporal_data = get_multi_temporal_ndvi(lat, lon, months_back=6, polygon=polygon)
    update_status("📊", f"Analyzed {temporal_data.get('months_analyzed', 0)} months of NDVI data", 0.25)
    
    # Step 2: Deforestation check
    update_status("🌳", "Checking for recent deforestation...", 0.30)
    deforestation_data = check_deforestation(lat, lon, years_back=2, polygon=polygon)
    deforest_status = "✅ No deforestation" if not deforestation_data.get("deforestation_detected") else "⚠️ Potential clearing detected"
    update_status("🌲", deforest_status, 0.45)
    
    # Step 3: Weather analysis
    update_status("🌤️", "Analyzing 90-day climate data...", 0.50)
    weather_data = weather_service.get_weather_analysis(lat, lon)
    update_status("☁️", f"Weather risk: {weather_data.get('weather_status', 'Unknown')}", 0.60)
    
    # Step 4: Calculate sustainability score
    update_status("♻️", "Computing sustainability score...", 0.65)
    sustainability = calculate_sustainability_score(temporal_data, deforestation_data, weather_data)
    update_status("📈", f"Sustainability: {sustainability.get('overall_score', 0)}/100 (Grade {sustainability.get('grade', 'N/A')})", 0.75)
    
    # Step 5: Calculate loan risk
    update_status("💰", "Calculating loan risk...", 0.80)
    loan_risk = calculate_loan_risk_score(sustainability, loan_amount, purpose)
    update_status("🏦", f"Risk Score: {loan_risk.get('risk_score', 0)}/100", 0.85)
    
    # Step 6: RAG - Retrieve Regulatory Context
    update_status("📋", "Retrieving regulatory compliance context (RAG)...", 0.87)
    current_lang = st.session_state.get("language", "en")
    regulatory_context_data = None
    try:
        pinecone_index = get_index()
        if pinecone_index:
            sustainability_score = sustainability.get("overall_score", 50)
            regulatory_context_data = get_compliance_context(
                loan_purpose=purpose or "",
                sustainability_score=sustainability_score,
                geographic_region=None,  # Could extract from coordinates
                index=pinecone_index
            )
            if regulatory_context_data and regulatory_context_data.get("context"):
                update_status("✅", f"Retrieved {len(regulatory_context_data.get('context', []))} regulatory guidelines", 0.88)
            else:
                update_status("⚠️", "RAG: Using mock context (Pinecone not configured)", 0.88)
        else:
            update_status("⚠️", "RAG: Pinecone not available, using mock context", 0.88)
            # Use mock context
            regulatory_context_data = {
                "context": [
                    {
                        "text": "LMA Green Lending Guidelines: Loans for sustainable agriculture must demonstrate positive environmental impact.",
                        "document": "lma_guidelines",
                        "score": 0.85
                    }
                ],
                "formatted_context": "\n=== RELEVANT REGULATORY GUIDELINES ===\n[1] Source: lma_guidelines\nRelevance Score: 0.85\nContent: LMA Green Lending Guidelines: Loans for sustainable agriculture must demonstrate positive environmental impact.\n=== END REGULATORY GUIDELINES ===\n",
                "compliance_score": True
            }
    except Exception as e:
        print(f"[RAG] Error retrieving regulatory context: {str(e)}")
        regulatory_context_data = None
        update_status("⚠️", f"RAG error: {str(e)[:50]}", 0.88)
    
    # Step 7: Generate In-Depth Metric Explanations
    update_status("📊", "Generating detailed metric explanations...", 0.89)
    metric_explanations = None
    try:
        metrics_for_analysis = {
            "sustainability_score": sustainability.get("overall_score", 50),
            "sustainability_components": {
                "vegetation_trend": sustainability.get("component_scores", {}).get("vegetation_trend", 0),
                "consistency": sustainability.get("component_scores", {}).get("consistency", 0),
                "no_deforestation": sustainability.get("component_scores", {}).get("no_deforestation", 0),
                "climate_resilience": sustainability.get("component_scores", {}).get("climate_resilience", 0),
            },
            "ndvi_current": temporal_data.get("ndvi_current", 0.5),
            "ndvi_trend": temporal_data.get("trend_direction", "stable"),
            "ndvi_consistency": temporal_data.get("consistency_score", 0),
            "risk_score": loan_risk.get("risk_score", 0),
            "weather_data": weather_data
        }
        metric_explanations = generate_metric_explanations(metrics_for_analysis, language=current_lang)
    except Exception as e:
        print(f"[Analysis] Error generating explanations: {str(e)}")
        metric_explanations = None
    
    # Step 8: AI Analysis with RAG Context
    update_status("🤖", "Generating AI recommendations...", 0.92)
    
    combined_data = {
        "ndvi_score": temporal_data.get("ndvi_current", 0.5),
        "ndvi_trend": temporal_data.get("trend_direction", "stable"),
        "sustainability_score": sustainability.get("overall_score", 50),
        "sustainability_grade": sustainability.get("grade", "C"),
        "deforestation_risk": deforestation_data.get("risk_level", "none"),
        "weather": weather_data,
        "risk_factors": sustainability.get("risk_factors", []),
        "positive_factors": sustainability.get("positive_factors", [])
    }
    
    regulatory_context_text = None
    if regulatory_context_data:
        regulatory_context_text = regulatory_context_data.get("formatted_context")
    
    try:
        llm_result = llm_service.analyze_loan_risk(
            combined_data, 
            user_request=purpose, 
            language=current_lang,
            regulatory_context=regulatory_context_text
        )
    except Exception as e:
        # Fallback to rule-based decision
        score = sustainability.get("overall_score", 50)
        if score >= 65:
            decision = "APPROVED"
        elif score >= 45:
            decision = "CONDITIONAL"
        else:
            decision = "REJECTED"
        
        llm_result = {
            "decision": decision,
            "confidence": score / 100,
            "reasoning": f"Based on sustainability score of {score}/100",
            "recommendations": loan_risk.get("decision_factors", []),
            "model_used": "rule-based-fallback"
        }
    
    update_status("✅", "Analysis complete!", 1.0)
    
    # Store results
    st.session_state.result = {
        "temporal_data": temporal_data,
        "deforestation_data": deforestation_data,
        "weather_data": weather_data,
        "sustainability": sustainability,
        "loan_risk": loan_risk,
        "llm_result": llm_result,
        "regulatory_context": regulatory_context_data,
        "metric_explanations": metric_explanations
    }
    
    # Save to analytics database for banker terminal
    try:
        from services.analytics_service import save_application
        application_record = {
            "status": llm_result.get("decision", "PENDING"),
            "loan_amount": loan_amount,
            "sustainability_score": sustainability.get("overall_score", 0),
            "risk_score": loan_risk.get("risk_score", 0),
            "ndvi_current": temporal_data.get("ndvi_current", 0),
            "deforestation_detected": deforestation_data.get("deforestation_detected", False),
            "region": "Unknown",  # Could be enhanced with geocoding
            "loan_purpose": purpose,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        save_application(application_record)
    except Exception as e:
        print(f"[Analytics] Error saving application: {str(e)}")
    
    time.sleep(0.5)
    st.session_state.step = 4
    st.rerun()


def page_results():
    """Step 4: Enhanced Results with Full Breakdown"""
    render_progress(4)
    
    result = st.session_state.result
    temporal_data = result.get("temporal_data", {})
    deforestation_data = result.get("deforestation_data", {})
    weather = result.get("weather_data", {})
    sustainability = result.get("sustainability", {})
    loan_risk = result.get("loan_risk", {})
    llm = result.get("llm_result", {})
    
    decision = llm.get("decision", "PENDING")
    confidence = llm.get("confidence", 0)
    
    # Decision Hero
    if "APPROVED" in decision:
        icon, title, css_class = "🎉", t('approved'), "approved"
        st.balloons()
    elif "CONDITIONAL" in decision:
        icon, title, css_class = "⚡", t('conditional'), "conditional"
    else:
        icon, title, css_class = "😔", t('rejected'), "rejected"
    
    st.markdown(f"""
        <div class="result-hero">
            <div class="result-icon">{icon}</div>
            <div class="result-title {css_class}">{title}</div>
            <div style="margin-top: 0.5rem;">
                <span style="background: #f3f4f6; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.9rem;">
                    Confidence: {confidence:.0%} | Risk Score: {loan_risk.get('risk_score', 0)}/100
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Loan Terms (if approved)
    if "APPROVED" in decision or "CONDITIONAL" in decision:
        st.markdown("### 💰 Recommended Loan Terms")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Interest Rate", loan_risk.get("suggested_interest_rate_pct", "N/A"))
        with col2:
            st.metric("Max Amount", f"${loan_risk.get('max_recommended_amount', 0):,.0f}")
        with col3:
            st.metric("Approval Likelihood", loan_risk.get("approval_likelihood", "N/A").title())
    
    # Tabs for detailed analysis
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Sustainability Score", 
        "📈 NDVI Trend", 
        "🌳 Deforestation", 
        "🤖 AI Analysis",
        "📋 Compliance & Regulations"
    ])
    
    with tab1:
        render_sustainability_score(sustainability)
        
        # Add metric explanations if available
        metric_explanations = result.get("metric_explanations")
        if metric_explanations and metric_explanations.get("sustainability_explanation"):
            with st.expander("ℹ️ What does this sustainability score mean?", expanded=False):
                st.markdown(metric_explanations.get("sustainability_explanation", ""))
    
    with tab2:
        render_ndvi_trend_chart(temporal_data)
        
        # Additional metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current NDVI", f"{temporal_data.get('ndvi_current', 0):.3f}")
            metric_explanations = result.get("metric_explanations")
            if metric_explanations and metric_explanations.get("ndvi_explanation"):
                with st.expander("ℹ️ Explanation", expanded=False):
                    st.caption(metric_explanations.get("ndvi_explanation", "")[:200] + "...")
        with col2:
            st.metric("6-Month Avg", f"{temporal_data.get('ndvi_average', 0):.3f}")
        with col3:
            st.metric("Change", f"{temporal_data.get('ndvi_change', 0):+.3f}")
        with col4:
            st.metric("Consistency", f"{temporal_data.get('consistency_score', 0):.0%}")
        
        # Full NDVI explanation
        metric_explanations = result.get("metric_explanations")
        if metric_explanations and metric_explanations.get("ndvi_explanation"):
            with st.expander("📊 What These NDVI Numbers Mean", expanded=False):
                st.markdown(metric_explanations.get("ndvi_explanation", ""))
    
    with tab3:
        deforest_detected = deforestation_data.get("deforestation_detected", False)
        
        if deforest_detected:
            st.error("⚠️ Potential Deforestation Detected")
        else:
            st.success("✅ No Deforestation Detected")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Historical NDVI", f"{deforestation_data.get('ndvi_historical', 0):.3f}")
        with col2:
            st.metric("Recent NDVI", f"{deforestation_data.get('ndvi_recent', 0):.3f}")
        with col3:
            st.metric("Change", f"{deforestation_data.get('change_detected', 0):+.3f}")
        
        st.info(f"Analysis Period: {deforestation_data.get('analysis_period', 'N/A')}")
    
    with tab4:
        st.markdown("### AI Reasoning")
        st.markdown(llm.get("reasoning", "No analysis available."))
        
        if llm.get("recommendations"):
            st.markdown("### Recommendations")
            for rec in llm["recommendations"]:
                st.markdown(f"• {rec}")
        
        # Show actionable insights if available
        metric_explanations = result.get("metric_explanations")
        if metric_explanations and metric_explanations.get("actionable_insights"):
            st.markdown("### 💡 Actionable Insights")
            for insight in metric_explanations.get("actionable_insights", []):
                st.markdown(f"• {insight}")
        
        # Risk explanation
        if metric_explanations and metric_explanations.get("risk_explanation"):
            with st.expander("ℹ️ Risk Score Explanation", expanded=False):
                st.markdown(metric_explanations.get("risk_explanation", ""))
        
        st.caption(f"Model: {llm.get('model_used', 'Unknown')}")
    
    with tab5:
        regulatory_context = result.get("regulatory_context")
        
        if regulatory_context and regulatory_context.get("context"):
            st.markdown("### 📋 Relevant Regulatory Guidelines")
            
            context_items = regulatory_context.get("context", [])
            if context_items:
                for i, item in enumerate(context_items, 1):
                    with st.expander(f"[{i}] {item.get('document', 'Unknown').replace('_', ' ').title()} (Relevance: {item.get('score', 0):.2f})", expanded=(i == 1)):
                        st.markdown(f"**Source:** {item.get('document', 'Unknown').replace('_', ' ').title()}")
                        st.markdown(f"**Relevance Score:** {item.get('score', 0):.2f}")
                        st.markdown(f"**Content:**\n\n{item.get('text', '')}")
            else:
                st.info("No specific regulatory context retrieved for this application.")
        else:
            st.info("Regulatory compliance context not available. This may be due to Pinecone not being configured or documents not being ingested.")
        
        # Show compliance citations from LLM if available
        if llm.get("compliance_citations"):
            st.markdown("### ✅ Compliance Citations")
            for citation in llm.get("compliance_citations", []):
                st.markdown(f"• {citation}")
        
        # Compliance score indicator
        if regulatory_context:
            compliance_score = regulatory_context.get("compliance_score", False)
            if compliance_score:
                st.success("✅ Regulatory compliance context retrieved successfully")
            else:
                st.warning("⚠️ Limited regulatory context available")
    
    # Certificate
    if "APPROVED" in decision or "CONDITIONAL" in decision:
        farm_data = {"ndvi_score": temporal_data.get("ndvi_current", 0.5), "status": "Verified"}
        tx_hash = generate_blockchain_hash(farm_data, llm)
        
        st.markdown(f"""
            <div class="cert-box">
                <div class="cert-title">🔐 Blockchain Verification Hash</div>
                <div class="cert-hash">{tx_hash}</div>
            </div>
        """, unsafe_allow_html=True)
        
        try:
            pdf_path, _ = create_green_certificate(farm_data, llm)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    f"📄 {t('download_certificate')}",
                    data=f,
                    file_name="GreenChain_Certificate.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.warning(f"Certificate generation unavailable: {e}")
    
    st.markdown("---")
    
    # Start over
    if st.button(f"🔄 {t('new_application')}", use_container_width=True):
        for key in ["step", "lat", "lon", "loan_purpose", "loan_amount", "result", "polygon"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------
def main():
    setup_page()
    
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    if "step" not in st.session_state:
        st.session_state.step = 1
    
    render_language_selector()
    render_brand()
    
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
