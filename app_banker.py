"""
🏦 GreenChain Banker Terminal - Bloomberg-Style Interface
Professional trading terminal UI for Green Finance Credit Officers

Features:
- Dark theme Bloomberg-inspired design
- Real-time data panels
- Multi-application portfolio view
- Advanced analytics dashboard
"""

import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timedelta
import random

import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px

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
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False


# ---------------------------------------------------------------------------
# Bloomberg Terminal Theme
# ---------------------------------------------------------------------------
def setup_bloomberg_theme():
    st.set_page_config(
        page_title="GreenChain Terminal",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
        
        :root {
            --bb-black: #000000;
            --bb-dark: #0a0a0a;
            --bb-panel: #111111;
            --bb-border: #2a2a2a;
            --bb-orange: #ff6600;
            --bb-amber: #ffaa00;
            --bb-yellow: #ffcc00;
            --bb-green: #00ff88;
            --bb-red: #ff3344;
            --bb-blue: #00aaff;
            --bb-cyan: #00ffcc;
            --bb-white: #ffffff;
            --bb-gray: #888888;
            --bb-light-gray: #cccccc;
        }
        
        * { font-family: 'JetBrains Mono', monospace !important; }
        
        .stApp {
            background: var(--bb-black) !important;
        }
        
        .block-container { 
            padding: 0.5rem 1rem !important; 
            max-width: 100% !important;
        }
        
        #MainMenu, footer, header { visibility: hidden !important; }
        div[data-testid="stDecoration"] { display: none !important; }
        .stDeployButton { display: none !important; }
        
        /* Terminal Header */
        .terminal-header {
            background: linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%);
            border-bottom: 2px solid var(--bb-orange);
            padding: 0.5rem 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: -0.5rem -1rem 1rem -1rem;
        }
        
        .terminal-title {
            color: var(--bb-orange);
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: 2px;
        }
        
        .terminal-time {
            color: var(--bb-amber);
            font-size: 0.9rem;
        }
        
        /* Bloomberg Panel */
        .bb-panel {
            background: var(--bb-panel);
            border: 1px solid var(--bb-border);
            border-radius: 0;
            margin: 0.25rem 0;
            overflow: hidden;
        }
        
        .bb-panel-header {
            background: linear-gradient(180deg, #222 0%, #111 100%);
            border-bottom: 1px solid var(--bb-border);
            padding: 0.4rem 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .bb-panel-title {
            color: var(--bb-amber);
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        .bb-panel-status {
            font-size: 0.65rem;
            padding: 0.15rem 0.4rem;
            border-radius: 2px;
        }
        
        .bb-panel-status.live {
            background: var(--bb-green);
            color: #000;
        }
        
        .bb-panel-status.pending {
            background: var(--bb-amber);
            color: #000;
        }
        
        .bb-panel-body {
            padding: 0.75rem;
        }
        
        /* Data Grid */
        .data-row {
            display: flex;
            justify-content: space-between;
            padding: 0.3rem 0;
            border-bottom: 1px solid #1a1a1a;
        }
        
        .data-row:last-child {
            border-bottom: none;
        }
        
        .data-label {
            color: var(--bb-gray);
            font-size: 0.75rem;
        }
        
        .data-value {
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .data-value.positive { color: var(--bb-green); }
        .data-value.negative { color: var(--bb-red); }
        .data-value.neutral { color: var(--bb-white); }
        .data-value.highlight { color: var(--bb-orange); }
        .data-value.amber { color: var(--bb-amber); }
        .data-value.cyan { color: var(--bb-cyan); }
        
        /* Score Display */
        .score-display {
            text-align: center;
            padding: 1rem;
        }
        
        .score-value-large {
            font-size: 3rem;
            font-weight: 700;
            line-height: 1;
        }
        
        .score-label {
            color: var(--bb-gray);
            font-size: 0.7rem;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-top: 0.5rem;
        }
        
        /* Ticker Tape */
        .ticker-tape {
            background: #0a0a0a;
            border-top: 1px solid var(--bb-border);
            border-bottom: 1px solid var(--bb-border);
            padding: 0.4rem 0;
            overflow: hidden;
            margin: 0.5rem -1rem;
        }
        
        .ticker-content {
            display: flex;
            gap: 2rem;
            animation: ticker 30s linear infinite;
            white-space: nowrap;
        }
        
        @keyframes ticker {
            0% { transform: translateX(0); }
            100% { transform: translateX(-50%); }
        }
        
        .ticker-item {
            display: inline-flex;
            gap: 0.5rem;
            font-size: 0.75rem;
        }
        
        .ticker-symbol { color: var(--bb-white); font-weight: 600; }
        .ticker-up { color: var(--bb-green); }
        .ticker-down { color: var(--bb-red); }
        
        /* Application Card */
        .app-card {
            background: var(--bb-panel);
            border: 1px solid var(--bb-border);
            padding: 0.75rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .app-card:hover {
            border-color: var(--bb-orange);
            background: #1a1a1a;
        }
        
        .app-card.selected {
            border-color: var(--bb-orange);
            border-width: 2px;
        }
        
        .app-id {
            color: var(--bb-orange);
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .app-meta {
            color: var(--bb-gray);
            font-size: 0.7rem;
            margin-top: 0.25rem;
        }
        
        /* Risk Meter */
        .risk-meter {
            display: flex;
            gap: 2px;
            margin: 0.5rem 0;
        }
        
        .risk-bar {
            flex: 1;
            height: 6px;
            background: #2a2a2a;
        }
        
        .risk-bar.filled.low { background: var(--bb-green); }
        .risk-bar.filled.medium { background: var(--bb-amber); }
        .risk-bar.filled.high { background: var(--bb-red); }
        
        /* Command Line */
        .command-line {
            background: #050505;
            border: 1px solid var(--bb-border);
            padding: 0.5rem 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .command-prompt {
            color: var(--bb-orange);
            font-weight: 700;
        }
        
        .command-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--bb-white);
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Function Keys */
        .func-keys {
            display: flex;
            gap: 0.5rem;
            padding: 0.5rem 0;
            border-top: 1px solid var(--bb-border);
            margin-top: 0.5rem;
        }
        
        .func-key {
            background: #1a1a1a;
            border: 1px solid var(--bb-border);
            color: var(--bb-amber);
            padding: 0.3rem 0.6rem;
            font-size: 0.65rem;
            cursor: pointer;
        }
        
        .func-key:hover {
            background: var(--bb-orange);
            color: #000;
        }
        
        /* Alert Banner */
        .alert-banner {
            padding: 0.4rem 0.75rem;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .alert-banner.success {
            background: rgba(0, 255, 136, 0.1);
            border-left: 3px solid var(--bb-green);
            color: var(--bb-green);
        }
        
        .alert-banner.warning {
            background: rgba(255, 170, 0, 0.1);
            border-left: 3px solid var(--bb-amber);
            color: var(--bb-amber);
        }
        
        .alert-banner.danger {
            background: rgba(255, 51, 68, 0.1);
            border-left: 3px solid var(--bb-red);
            color: var(--bb-red);
        }
        
        /* Override Streamlit Elements */
        .stButton > button {
            background: #1a1a1a !important;
            border: 1px solid var(--bb-border) !important;
            color: var(--bb-amber) !important;
            border-radius: 0 !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.75rem !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            padding: 0.5rem 1rem !important;
        }
        
        .stButton > button:hover {
            background: var(--bb-orange) !important;
            color: #000 !important;
            border-color: var(--bb-orange) !important;
        }
        
        .stButton > button[kind="primary"] {
            background: var(--bb-orange) !important;
            color: #000 !important;
        }
        
        .stTextInput > div > div > input {
            background: #0a0a0a !important;
            border: 1px solid var(--bb-border) !important;
            color: var(--bb-white) !important;
            border-radius: 0 !important;
        }
        
        .stSelectbox > div > div {
            background: #0a0a0a !important;
            border: 1px solid var(--bb-border) !important;
            border-radius: 0 !important;
        }
        
        .stSlider > div > div > div {
            background: var(--bb-orange) !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background: #111 !important;
            gap: 0 !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: #1a1a1a !important;
            color: var(--bb-gray) !important;
            border: 1px solid var(--bb-border) !important;
            border-radius: 0 !important;
            font-size: 0.75rem !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--bb-panel) !important;
            color: var(--bb-orange) !important;
            border-bottom-color: var(--bb-orange) !important;
        }
        
        .stMetric {
            background: var(--bb-panel) !important;
            padding: 0.75rem !important;
            border: 1px solid var(--bb-border) !important;
        }
        
        .stMetric label {
            color: var(--bb-gray) !important;
            font-size: 0.7rem !important;
        }
        
        .stMetric [data-testid="stMetricValue"] {
            color: var(--bb-amber) !important;
        }
        
        div[data-testid="stAppViewBlockContainer"] {
            background: var(--bb-black) !important;
        }
        
        /* Map styling */
        iframe {
            border: 1px solid var(--bb-border) !important;
            border-radius: 0 !important;
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #2a2a2a;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--bb-orange);
        }
        
        /* Blinking cursor effect */
        .blink {
            animation: blink 1s step-end infinite;
        }
        
        @keyframes blink {
            50% { opacity: 0; }
        }
        
        /* Status indicators */
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.5rem;
        }
        
        .status-dot.green { background: var(--bb-green); box-shadow: 0 0 6px var(--bb-green); }
        .status-dot.amber { background: var(--bb-amber); box-shadow: 0 0 6px var(--bb-amber); }
        .status-dot.red { background: var(--bb-red); box-shadow: 0 0 6px var(--bb-red); }
        </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Mock Data for Demo
# ---------------------------------------------------------------------------
def generate_mock_applications():
    """Generate mock loan applications for demo."""
    applications = [
        {
            "id": "GCH-2026-001847",
            "applicant": "Rajesh Kumar",
            "location": "Punjab, India",
            "lat": 29.605,
            "lon": 76.273,
            "amount": 5000,
            "purpose": "Drip irrigation system installation",
            "submitted": "2026-01-14 09:23:45",
            "status": "PENDING",
            "sustainability_score": 78,
            "risk_score": 32,
            "ndvi_current": 0.65,
            "ndvi_trend": "+0.12",
            "deforestation": False,
        },
        {
            "id": "GCH-2026-001846",
            "applicant": "Maria Santos",
            "location": "Goiás, Brazil",
            "lat": -15.826,
            "lon": -47.921,
            "amount": 8500,
            "purpose": "Solar-powered water pump",
            "submitted": "2026-01-14 08:45:12",
            "status": "APPROVED",
            "sustainability_score": 85,
            "risk_score": 18,
            "ndvi_current": 0.72,
            "ndvi_trend": "+0.08",
            "deforestation": False,
        },
        {
            "id": "GCH-2026-001845",
            "applicant": "John Mitchell",
            "location": "Kansas, USA",
            "lat": 37.669,
            "lon": -100.749,
            "amount": 12000,
            "purpose": "Organic fertilizer transition",
            "submitted": "2026-01-14 07:12:33",
            "status": "CONDITIONAL",
            "sustainability_score": 58,
            "risk_score": 45,
            "ndvi_current": 0.48,
            "ndvi_trend": "-0.03",
            "deforestation": False,
        },
        {
            "id": "GCH-2026-001844",
            "applicant": "Samuel Okonkwo",
            "location": "Lagos, Nigeria",
            "lat": 6.524,
            "lon": 3.379,
            "amount": 3200,
            "purpose": "Sustainable farming equipment",
            "submitted": "2026-01-13 16:45:00",
            "status": "REJECTED",
            "sustainability_score": 32,
            "risk_score": 78,
            "ndvi_current": 0.28,
            "ndvi_trend": "-0.15",
            "deforestation": True,
        },
        {
            "id": "GCH-2026-001843",
            "applicant": "Aisha Mohammed",
            "location": "Nairobi, Kenya",
            "lat": -1.286,
            "lon": 36.817,
            "amount": 4500,
            "purpose": "Crop rotation implementation",
            "submitted": "2026-01-13 14:30:22",
            "status": "APPROVED",
            "sustainability_score": 82,
            "risk_score": 22,
            "ndvi_current": 0.68,
            "ndvi_trend": "+0.09",
            "deforestation": False,
        },
    ]
    return applications


def get_portfolio_stats():
    """Calculate portfolio statistics."""
    return {
        "total_applications": 847,
        "pending_review": 23,
        "approved_today": 12,
        "rejected_today": 3,
        "total_disbursed": 2847500,
        "avg_sustainability": 72.4,
        "green_compliance": 94.2,
        "carbon_offset_tons": 1284,
    }


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def render_terminal_header():
    """Render Bloomberg-style terminal header."""
    now = datetime.now()
    st.markdown(f"""
        <div class="terminal-header">
            <div class="terminal-title">GREENCHAIN TERMINAL</div>
            <div style="display: flex; gap: 2rem; align-items: center;">
                <span style="color: #888; font-size: 0.75rem;">BANKER WORKSTATION</span>
                <span class="terminal-time">{now.strftime("%Y-%m-%d %H:%M:%S")} UTC</span>
                <span style="color: #00ff88; font-size: 0.75rem;">● CONNECTED</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_ticker_tape():
    """Render market ticker tape."""
    st.markdown("""
        <div class="ticker-tape">
            <div class="ticker-content">
                <span class="ticker-item">
                    <span class="ticker-symbol">CARBON</span>
                    <span class="ticker-up">▲ 47.82 +2.3%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">ESG.IDX</span>
                    <span class="ticker-up">▲ 1,284.50 +0.8%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">GREENBOND</span>
                    <span class="ticker-down">▼ 102.35 -0.2%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">NDVI.AVG</span>
                    <span class="ticker-up">▲ 0.642 +0.5%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">AGRI.RISK</span>
                    <span class="ticker-down">▼ 23.4 -1.2%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">SUSTAIN</span>
                    <span class="ticker-up">▲ 78.9 +0.3%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">CARBON</span>
                    <span class="ticker-up">▲ 47.82 +2.3%</span>
                </span>
                <span class="ticker-item">
                    <span class="ticker-symbol">ESG.IDX</span>
                    <span class="ticker-up">▲ 1,284.50 +0.8%</span>
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_portfolio_panel(stats):
    """Render portfolio overview panel."""
    st.markdown("""
        <div class="bb-panel">
            <div class="bb-panel-header">
                <span class="bb-panel-title">📊 Portfolio Overview</span>
                <span class="bb-panel-status live">LIVE</span>
            </div>
            <div class="bb-panel-body">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="score-display">
                <div class="score-value-large" style="color: #ffaa00;">{stats['total_applications']}</div>
                <div class="score-label">Total Applications</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="score-display">
                <div class="score-value-large" style="color: #ff6600;">{stats['pending_review']}</div>
                <div class="score-label">Pending Review</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="score-display">
                <div class="score-value-large" style="color: #00ff88;">${stats['total_disbursed']:,.0f}</div>
                <div class="score-label">Total Disbursed</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="score-display">
                <div class="score-value-large" style="color: #00ffcc;">{stats['green_compliance']:.1f}%</div>
                <div class="score-label">Green Compliance</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_application_queue(applications):
    """Render pending applications queue."""
    st.markdown("""
        <div class="bb-panel">
            <div class="bb-panel-header">
                <span class="bb-panel-title">📋 Application Queue</span>
                <span class="bb-panel-status pending">23 PENDING</span>
            </div>
            <div class="bb-panel-body" style="padding: 0;">
    """, unsafe_allow_html=True)
    
    for app in applications:
        status_color = {
            "PENDING": "#ffaa00",
            "APPROVED": "#00ff88",
            "CONDITIONAL": "#00aaff",
            "REJECTED": "#ff3344"
        }.get(app["status"], "#888")
        
        trend_color = "#00ff88" if app["ndvi_trend"].startswith("+") else "#ff3344"
        
        if st.button(
            f"📄 {app['id']} | {app['applicant'][:15]} | ${app['amount']:,} | Score: {app['sustainability_score']}",
            key=f"app_{app['id']}",
            use_container_width=True
        ):
            st.session_state.selected_application = app
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_application_detail(app):
    """Render detailed application view."""
    status_colors = {
        "PENDING": ("amber", "#ffaa00"),
        "APPROVED": ("green", "#00ff88"),
        "CONDITIONAL": ("cyan", "#00aaff"),
        "REJECTED": ("red", "#ff3344")
    }
    
    status_class, status_color = status_colors.get(app["status"], ("amber", "#ffaa00"))
    
    # Header
    st.markdown(f"""
        <div class="bb-panel">
            <div class="bb-panel-header">
                <span class="bb-panel-title">🔍 APPLICATION DETAILS: {app['id']}</span>
                <span class="bb-panel-status" style="background: {status_color}; color: #000;">{app['status']}</span>
            </div>
            <div class="bb-panel-body">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem;">
                    <div>
                        <div class="data-row">
                            <span class="data-label">APPLICANT</span>
                            <span class="data-value neutral">{app['applicant']}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">LOCATION</span>
                            <span class="data-value cyan">{app['location']}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">COORDINATES</span>
                            <span class="data-value neutral">{app['lat']:.4f}, {app['lon']:.4f}</span>
                        </div>
                    </div>
                    <div>
                        <div class="data-row">
                            <span class="data-label">AMOUNT</span>
                            <span class="data-value highlight">${app['amount']:,}</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">PURPOSE</span>
                            <span class="data-value neutral">{app['purpose'][:30]}...</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">SUBMITTED</span>
                            <span class="data-value neutral">{app['submitted']}</span>
                        </div>
                    </div>
                    <div>
                        <div class="data-row">
                            <span class="data-label">SUSTAINABILITY</span>
                            <span class="data-value {'positive' if app['sustainability_score'] >= 60 else 'negative'}">{app['sustainability_score']}/100</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">RISK SCORE</span>
                            <span class="data-value {'positive' if app['risk_score'] <= 40 else 'negative'}">{app['risk_score']}/100</span>
                        </div>
                        <div class="data-row">
                            <span class="data-label">DEFORESTATION</span>
                            <span class="data-value {'negative' if app['deforestation'] else 'positive'}">{'⚠ DETECTED' if app['deforestation'] else '✓ CLEAR'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_ndvi_analysis_panel(app):
    """Render NDVI analysis with charts."""
    # Generate mock temporal data
    months = ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"]
    base_ndvi = app["ndvi_current"]
    trend_val = float(app["ndvi_trend"])
    
    ndvi_values = [
        base_ndvi - trend_val + random.uniform(-0.03, 0.03),
        base_ndvi - trend_val * 0.8 + random.uniform(-0.03, 0.03),
        base_ndvi - trend_val * 0.6 + random.uniform(-0.03, 0.03),
        base_ndvi - trend_val * 0.4 + random.uniform(-0.03, 0.03),
        base_ndvi - trend_val * 0.2 + random.uniform(-0.03, 0.03),
        base_ndvi
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=months,
        y=ndvi_values,
        mode='lines+markers',
        name='NDVI',
        line=dict(color='#00ff88', width=2),
        marker=dict(size=8, color='#00ff88'),
        fill='tozeroy',
        fillcolor='rgba(0, 255, 136, 0.1)'
    ))
    
    # Threshold lines
    fig.add_hline(y=0.5, line_dash="dash", line_color="#ffaa00", 
                  annotation_text="GOOD", annotation_position="right",
                  annotation_font_color="#ffaa00")
    fig.add_hline(y=0.3, line_dash="dash", line_color="#ff3344",
                  annotation_text="POOR", annotation_position="right",
                  annotation_font_color="#ff3344")
    
    fig.update_layout(
        title=dict(text="6-MONTH NDVI TREND", font=dict(color="#ffaa00", size=12)),
        xaxis=dict(
            title="",
            color="#888",
            gridcolor="#2a2a2a",
            linecolor="#2a2a2a"
        ),
        yaxis=dict(
            title="NDVI",
            range=[0, 1],
            color="#888",
            gridcolor="#2a2a2a",
            linecolor="#2a2a2a"
        ),
        template="plotly_dark",
        paper_bgcolor="#111111",
        plot_bgcolor="#0a0a0a",
        height=300,
        margin=dict(l=40, r=20, t=40, b=30),
        font=dict(family="JetBrains Mono, monospace", size=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_risk_gauge(app):
    """Render risk assessment gauge."""
    risk = app["risk_score"]
    sustainability = app["sustainability_score"]
    
    fig = go.Figure()
    
    # Risk gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=risk,
        title=dict(text="RISK SCORE", font=dict(size=12, color="#888")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#888"),
            bar=dict(color="#ff6600"),
            bgcolor="#1a1a1a",
            bordercolor="#2a2a2a",
            steps=[
                dict(range=[0, 30], color="#00ff88"),
                dict(range=[30, 60], color="#ffaa00"),
                dict(range=[60, 100], color="#ff3344")
            ],
            threshold=dict(
                line=dict(color="#fff", width=2),
                thickness=0.75,
                value=risk
            )
        ),
        domain=dict(x=[0, 0.45], y=[0, 1]),
        number=dict(font=dict(color="#ff6600"))
    ))
    
    # Sustainability gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=sustainability,
        title=dict(text="SUSTAINABILITY", font=dict(size=12, color="#888")),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#888"),
            bar=dict(color="#00ff88"),
            bgcolor="#1a1a1a",
            bordercolor="#2a2a2a",
            steps=[
                dict(range=[0, 40], color="#ff3344"),
                dict(range=[40, 70], color="#ffaa00"),
                dict(range=[70, 100], color="#00ff88")
            ],
            threshold=dict(
                line=dict(color="#fff", width=2),
                thickness=0.75,
                value=sustainability
            )
        ),
        domain=dict(x=[0.55, 1], y=[0, 1]),
        number=dict(font=dict(color="#00ff88"))
    ))
    
    fig.update_layout(
        paper_bgcolor="#111111",
        font=dict(family="JetBrains Mono, monospace", color="#888"),
        height=200,
        margin=dict(l=20, r=20, t=30, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_satellite_map(app):
    """Render satellite map view."""
    m = folium.Map(
        location=[app["lat"], app["lon"]],
        zoom_start=12,
        tiles=None
    )
    
    # Dark tile layer
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='CartoDB Dark',
        name='Dark Map'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Satellite',
        name='Satellite'
    ).add_to(m)
    
    # Add marker
    folium.CircleMarker(
        location=[app["lat"], app["lon"]],
        radius=15,
        color='#ff6600',
        fill=True,
        fillColor='#ff6600',
        fillOpacity=0.3,
        popup=f"{app['id']}<br>NDVI: {app['ndvi_current']}"
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    st_folium(m, height=300, width=None, key="detail_map")


def render_decision_panel(app):
    """Render decision action panel."""
    st.markdown("""
        <div class="bb-panel">
            <div class="bb-panel-header">
                <span class="bb-panel-title">⚡ Quick Actions</span>
            </div>
            <div class="bb-panel-body">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✓ APPROVE", key="approve_btn", type="primary", use_container_width=True):
            st.session_state.selected_application["status"] = "APPROVED"
            st.success("Application APPROVED")
    
    with col2:
        if st.button("⚡ CONDITIONAL", key="cond_btn", use_container_width=True):
            st.session_state.selected_application["status"] = "CONDITIONAL"
            st.warning("Marked as CONDITIONAL")
    
    with col3:
        if st.button("✗ REJECT", key="reject_btn", use_container_width=True):
            st.session_state.selected_application["status"] = "REJECTED"
            st.error("Application REJECTED")
    
    with col4:
        if st.button("↻ RE-ANALYZE", key="reanalyze_btn", use_container_width=True):
            st.info("Triggering re-analysis...")
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_live_analysis_panel():
    """Render live analysis with real service calls."""
    st.markdown("""
        <div class="bb-panel">
            <div class="bb-panel-header">
                <span class="bb-panel-title">🛰️ Live Satellite Analysis</span>
                <span class="bb-panel-status live">REAL-TIME</span>
            </div>
            <div class="bb-panel-body">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Enter Coordinates:**")
        lat = st.number_input("Latitude", value=29.605, format="%.4f", key="live_lat")
        lon = st.number_input("Longitude", value=76.273, format="%.4f", key="live_lon")
        
        if st.button("🔍 ANALYZE", key="live_analyze", use_container_width=True, type="primary"):
            with st.spinner("Fetching satellite data..."):
                if SERVICES_AVAILABLE:
                    temporal_data = get_multi_temporal_ndvi(lat, lon, months_back=6)
                    deforestation = check_deforestation(lat, lon)
                    weather = weather_service.get_weather_analysis(lat, lon)
                    sustainability = calculate_sustainability_score(temporal_data, deforestation, weather)
                    
                    st.session_state.live_analysis = {
                        "temporal": temporal_data,
                        "deforestation": deforestation,
                        "weather": weather,
                        "sustainability": sustainability
                    }
                else:
                    st.error("Services not available")
    
    with col2:
        if "live_analysis" in st.session_state:
            analysis = st.session_state.live_analysis
            sust = analysis["sustainability"]
            
            st.markdown(f"""
                <div class="alert-banner success">
                    <span class="status-dot green"></span>
                    Analysis Complete | Score: {sust.get('overall_score', 0)}/100 | Grade: {sust.get('grade', 'N/A')}
                </div>
            """, unsafe_allow_html=True)
            
            # Display results
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("NDVI Current", f"{analysis['temporal'].get('ndvi_current', 0):.3f}")
            with col_b:
                st.metric("Trend", analysis['temporal'].get('trend_direction', 'stable').upper())
            with col_c:
                deforest = "⚠ YES" if analysis['deforestation'].get('deforestation_detected') else "✓ NO"
                st.metric("Deforestation", deforest)
    
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_function_keys():
    """Render Bloomberg-style function keys."""
    st.markdown("""
        <div class="func-keys">
            <span class="func-key">F1 HELP</span>
            <span class="func-key">F2 QUEUE</span>
            <span class="func-key">F3 SEARCH</span>
            <span class="func-key">F4 ANALYZE</span>
            <span class="func-key">F5 REFRESH</span>
            <span class="func-key">F6 REPORTS</span>
            <span class="func-key">F7 EXPORT</span>
            <span class="func-key">F8 SETTINGS</span>
        </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
def main():
    setup_bloomberg_theme()
    
    if not SERVICES_AVAILABLE:
        st.error("⚠ Backend services unavailable. Running in demo mode.")
    
    # Initialize state
    if "applications" not in st.session_state:
        st.session_state.applications = generate_mock_applications()
    
    if "selected_application" not in st.session_state:
        st.session_state.selected_application = None
    
    render_terminal_header()
    render_ticker_tape()
    
    # Portfolio stats
    stats = get_portfolio_stats()
    render_portfolio_panel(stats)
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📋 APPLICATION QUEUE", "🛰️ LIVE ANALYSIS", "📊 PORTFOLIO ANALYTICS"])
    
    with tab1:
        if st.session_state.selected_application:
            app = st.session_state.selected_application
            
            # Back button
            if st.button("← BACK TO QUEUE", key="back_btn"):
                st.session_state.selected_application = None
                st.rerun()
            
            render_application_detail(app)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("""
                    <div class="bb-panel">
                        <div class="bb-panel-header">
                            <span class="bb-panel-title">📈 NDVI Analysis</span>
                        </div>
                        <div class="bb-panel-body">
                """, unsafe_allow_html=True)
                render_ndvi_analysis_panel(app)
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                    <div class="bb-panel">
                        <div class="bb-panel-header">
                            <span class="bb-panel-title">🎯 Risk Assessment</span>
                        </div>
                        <div class="bb-panel-body">
                """, unsafe_allow_html=True)
                render_risk_gauge(app)
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            col3, col4 = st.columns([1, 1])
            
            with col3:
                st.markdown("""
                    <div class="bb-panel">
                        <div class="bb-panel-header">
                            <span class="bb-panel-title">🗺️ Location View</span>
                        </div>
                        <div class="bb-panel-body">
                """, unsafe_allow_html=True)
                render_satellite_map(app)
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                    <div class="bb-panel">
                        <div class="bb-panel-header">
                            <span class="bb-panel-title">📋 AI Recommendation</span>
                        </div>
                        <div class="bb-panel-body">
                """, unsafe_allow_html=True)
                
                if app["sustainability_score"] >= 70:
                    st.markdown("""
                        <div class="alert-banner success">
                            <span>✓ RECOMMENDATION: APPROVE</span>
                        </div>
                        <p style="color: #888; font-size: 0.75rem; margin-top: 1rem;">
                        Strong sustainability indicators. NDVI trend positive. No deforestation detected.
                        Low climate risk. Purpose aligns with green finance criteria.
                        </p>
                    """, unsafe_allow_html=True)
                elif app["sustainability_score"] >= 50:
                    st.markdown("""
                        <div class="alert-banner warning">
                            <span>⚡ RECOMMENDATION: CONDITIONAL</span>
                        </div>
                        <p style="color: #888; font-size: 0.75rem; margin-top: 1rem;">
                        Moderate sustainability score. Consider requiring additional documentation
                        or reduced loan amount. Monitor quarterly.
                        </p>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                        <div class="alert-banner danger">
                            <span>✗ RECOMMENDATION: REJECT</span>
                        </div>
                        <p style="color: #888; font-size: 0.75rem; margin-top: 1rem;">
                        Low sustainability score. Potential deforestation detected or declining
                        vegetation health. Does not meet green finance criteria.
                        </p>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
            
            render_decision_panel(app)
        else:
            render_application_queue(st.session_state.applications)
    
    with tab2:
        render_live_analysis_panel()
        
        if "live_analysis" in st.session_state:
            analysis = st.session_state.live_analysis
            temporal = analysis["temporal"]
            
            # Show detailed temporal chart
            if temporal.get("monthly_data"):
                monthly = temporal["monthly_data"]
                months = [m["month"] for m in monthly]
                ndvi_vals = [m["ndvi"] for m in monthly]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=months, y=ndvi_vals,
                    mode='lines+markers',
                    line=dict(color='#00ff88', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0, 255, 136, 0.1)'
                ))
                
                fig.add_hline(y=0.5, line_dash="dash", line_color="#ffaa00")
                fig.add_hline(y=0.3, line_dash="dash", line_color="#ff3344")
                
                fig.update_layout(
                    title="REAL-TIME NDVI TREND",
                    template="plotly_dark",
                    paper_bgcolor="#111111",
                    plot_bgcolor="#0a0a0a",
                    height=350,
                    font=dict(family="JetBrains Mono")
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="bb-panel">
                    <div class="bb-panel-header">
                        <span class="bb-panel-title">📊 Portfolio Distribution</span>
                    </div>
                    <div class="bb-panel-body">
            """, unsafe_allow_html=True)
            
            # Status distribution
            fig = go.Figure(data=[go.Pie(
                labels=['Approved', 'Conditional', 'Pending', 'Rejected'],
                values=[523, 124, 23, 177],
                hole=0.6,
                marker_colors=['#00ff88', '#00aaff', '#ffaa00', '#ff3344']
            )])
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#111111",
                plot_bgcolor="#0a0a0a",
                height=300,
                font=dict(family="JetBrains Mono", color="#888"),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div class="bb-panel">
                    <div class="bb-panel-header">
                        <span class="bb-panel-title">🌍 Geographic Distribution</span>
                    </div>
                    <div class="bb-panel-body">
            """, unsafe_allow_html=True)
            
            fig = go.Figure(data=[go.Bar(
                x=['India', 'Brazil', 'Kenya', 'USA', 'Nigeria', 'Other'],
                y=[234, 187, 156, 124, 89, 57],
                marker_color=['#ff6600', '#00ff88', '#00aaff', '#ffaa00', '#00ffcc', '#888']
            )])
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#111111",
                plot_bgcolor="#0a0a0a",
                height=300,
                font=dict(family="JetBrains Mono", color="#888"),
                xaxis=dict(gridcolor="#2a2a2a"),
                yaxis=dict(gridcolor="#2a2a2a", title="Applications")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Monthly trend
        st.markdown("""
            <div class="bb-panel">
                <div class="bb-panel-header">
                    <span class="bb-panel-title">📈 Monthly Application Trend</span>
                </div>
                <div class="bb-panel-body">
        """, unsafe_allow_html=True)
        
        months = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
        approved = [45, 52, 68, 72, 89, 97]
        rejected = [12, 15, 18, 14, 22, 16]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=approved, name='Approved', 
                                  line=dict(color='#00ff88', width=2), fill='tozeroy',
                                  fillcolor='rgba(0, 255, 136, 0.1)'))
        fig.add_trace(go.Scatter(x=months, y=rejected, name='Rejected',
                                  line=dict(color='#ff3344', width=2)))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111111",
            plot_bgcolor="#0a0a0a",
            height=250,
            font=dict(family="JetBrains Mono", color="#888"),
            xaxis=dict(gridcolor="#2a2a2a"),
            yaxis=dict(gridcolor="#2a2a2a"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    render_function_keys()
    
    # Command line footer
    st.markdown("""
        <div class="command-line">
            <span class="command-prompt">GCH&gt;</span>
            <span style="color: #888;">Type command or press F1 for help</span>
            <span class="blink" style="color: #ff6600;">_</span>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
