"""
Streamlit frontend for the 🌱 GreenChain: AI Sustainable Finance Agent.

Dashboards:
- Sidebar: coordinates + controls
- Three main columns: Map, Satellite NDVI, AI Loan Decision
"""

import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Python path setup so we can import from backend/src
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_SRC = ROOT_DIR / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

# Load environment variables from .env.local at project root (if present)
env_path = ROOT_DIR / ".env.local"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to default .env if someone prefers that name
    load_dotenv()

import services.satellite_service as satellite_service  # type: ignore
from services.llm_service import analyze_loan_risk  # type: ignore
from services.verification_service import (  # type: ignore
    create_green_certificate,
    generate_blockchain_hash,
)


def run_analysis(latitude: float, longitude: float, user_request: str | None) -> Dict[str, Any]:
    """Run the full pipeline: satellite NDVI + LLM loan analysis."""
    farm_data = satellite_service.get_farm_ndvi(latitude, longitude)
    llm_result = analyze_loan_risk(farm_data, user_request=user_request)

    return {
        "farm_data": farm_data,
        "llm_result": llm_result,
    }


def render_status_badge(status: str) -> None:
    """Render a colored badge for vegetation status."""
    status_lower = status.lower()
    if "healthy" in status_lower or "excellent" in status_lower or "good" in status_lower:
        color = "#16a34a"  # green-600
    elif "warning" in status_lower or "stressed" in status_lower:
        color = "#f97316"  # orange-500
    else:
        color = "#dc2626"  # red-600

    st.markdown(
        f"""
        <span style="
            display:inline-block;
            padding:0.25rem 0.6rem;
            border-radius:999px;
            background-color:{color}1A;
            color:{color};
            font-weight:600;
            font-size:0.9rem;
        ">{status}</span>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="GreenChain Agent",
        page_icon="🌱",
        layout="wide",
    )

    st.title("🌱 GreenChain: AI Sustainable Finance Agent")
    st.caption(
        "Validate farm sustainability from satellite NDVI and AI credit analysis to power fair micro-loans."
    )

    # -----------------------------------------------------------------------
    # Sidebar controls
    # -----------------------------------------------------------------------
    st.sidebar.header("Farm Configuration")

    default_lat = 37.669
    default_lon = -100.749

    # Initialise coordinate state if not set
    if "lat" not in st.session_state:
        st.session_state.lat = default_lat
    if "lon" not in st.session_state:
        st.session_state.lon = default_lon

    # Sidebar numeric inputs bound to session state
    lat = st.sidebar.number_input(
        "Latitude",
        value=float(st.session_state.lat),
        format="%.6f",
        key="lat_input",
    )
    lon = st.sidebar.number_input(
        "Longitude",
        value=float(st.session_state.lon),
        format="%.6f",
        key="lon_input",
    )

    # Keep session state in sync with sidebar
    st.session_state.lat = float(lat)
    st.session_state.lon = float(lon)

    mock_mode = st.sidebar.checkbox("Mock Mode (fast, no live satellite fetch)", value=False)

    user_context = st.sidebar.text_area(
        "Loan Purpose / Context (optional)",
        value="Requesting a sustainable micro-loan to expand climate-resilient crops.",
        height=80,
    )

    analyze_clicked = st.sidebar.button("🔍 Analyze Farm", type="primary", use_container_width=True)

    # Allow toggling backend mock mode for hackathon speed
    satellite_service.MOCK_MODE = bool(mock_mode)

    # -----------------------------------------------------------------------
    # Main layout
    # -----------------------------------------------------------------------
    col_map, col_satellite, col_ai = st.columns(3)

    # Pre-populate map with current lat/lon and allow picking from map
    with col_map:
        st.subheader("Farm Location")
        enable_pick = st.checkbox(
            "Pick location by clicking on the map",
            value=True,
            help="Click on the map to update the latitude/longitude used for analysis.",
            key="pick_from_map",
        )

        current_lat = float(st.session_state.lat)
        current_lon = float(st.session_state.lon)

        if enable_pick:
            m = folium.Map(location=[current_lat, current_lon], zoom_start=7)
            folium.Marker(
                [current_lat, current_lon],
                tooltip="Selected farm location",
            ).add_to(m)

            map_data = st_folium(m, width="100%", height=350)

            # When user clicks on the map, update coordinates
            if map_data and map_data.get("last_clicked"):
                clicked = map_data["last_clicked"]
                st.session_state.lat = float(clicked["lat"])
                st.session_state.lon = float(clicked["lng"])
                current_lat = st.session_state.lat
                current_lon = st.session_state.lon

        # Simple overview map synced with current coordinates
        df_map = pd.DataFrame({"lat": [current_lat], "lon": [current_lon]})
        st.map(df_map, zoom=8)
        st.caption("Click on the map or adjust coordinates in the sidebar to set the farm location.")

    # Ensure we use the latest coordinates (possibly updated from the map)
    lat = float(st.session_state.lat)
    lon = float(st.session_state.lon)

    result: Dict[str, Any] | None = None

    if analyze_clicked:
        with st.spinner("Analyzing farm sustainability and loan risk..."):
            try:
                result = run_analysis(lat, lon, user_context.strip() or None)
            except Exception as e:  # noqa: BLE001
                st.error(f"Something went wrong while analyzing this farm: {e}")

    # Only render metrics once we have results
    if result is not None:
        farm_data = result.get("farm_data", {}) or {}
        llm_result = result.get("llm_result", {}) or {}

        ndvi_score = farm_data.get("ndvi_score", 0.0) or 0.0
        ndvi_status = farm_data.get("status", "Unknown")

        decision = (llm_result.get("decision") or "UNKNOWN").upper()
        confidence = llm_result.get("confidence", 0.0) or 0.0
        reasoning = llm_result.get("reasoning") or llm_result.get("raw_response", "")

        # --------------------- Column 2: Satellite NDVI ---------------------
        with col_satellite:
            st.subheader("Satellite Vegetation Health")
            st.metric("NDVI Score", f"{ndvi_score:.3f}")
            render_status_badge(str(ndvi_status))

            meta_lines = []
            if farm_data.get("cloud_cover") is not None:
                meta_lines.append(f"☁️ Cloud cover: {farm_data['cloud_cover']}%")
            if farm_data.get("acquisition_date"):
                meta_lines.append(f"📅 Acquisition: {farm_data['acquisition_date']}")
            if farm_data.get("image_id"):
                meta_lines.append(f"🛰️ Scene ID: `{farm_data['image_id']}`")
            if farm_data.get("note"):
                meta_lines.append(f"ℹ️ {farm_data['note']}")

            if meta_lines:
                st.markdown("<br>".join(meta_lines))

        # ---------------------- Column 3: AI Decision ----------------------
        with col_ai:
            st.subheader("AI Credit Decision")

            approved = "APPROVED" in decision
            conditional = "CONDITIONAL" in decision

            if approved and not conditional:
                decision_label = "✅ APPROVED"
                decision_color = "green"
            elif conditional or ("APPROVED" in decision and "CONDITIONAL" in decision):
                decision_label = "🟡 CONDITIONAL APPROVAL"
                decision_color = "orange"
            else:
                decision_label = "❌ REJECTED"
                decision_color = "red"

            st.markdown(
                f"<h3 style='color:{decision_color}; margin-bottom:0.25rem;'>{decision_label}</h3>",
                unsafe_allow_html=True,
            )
            st.metric("Model Confidence", f"{confidence:.2f}")

            # ---------------- Verification Layer -----------------
            if approved or conditional:
                st.success("✅ Transaction Verified on Ledger")

                verification_payload = {
                    "farm_data": farm_data,
                    "decision_data": llm_result,
                    "issued_at": result.get("timestamp"),
                    "latitude": lat,
                    "longitude": lon,
                }
                ledger_hash = generate_blockchain_hash(verification_payload)

                st.caption("Blockchain Proof ID")
                st.code(ledger_hash, language="text")

                # Generate certificate PDF
                cert_path = create_green_certificate(
                    farm_data=farm_data,
                    decision_data=llm_result,
                    ledger_hash=ledger_hash,
                    latitude=lat,
                    longitude=lon,
                )

                try:
                    with open(cert_path, "rb") as f:
                        pdf_bytes = f.read()

                    st.download_button(
                        label="📄 Download Green Certificate (PDF)",
                        data=pdf_bytes,
                        file_name=cert_path.name,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except OSError as e:  # noqa: PERF203
                    st.warning(f"Unable to load certificate file for download: {e}")

        # ---------------------- Agent’s Voice / Reasoning ------------------
        st.markdown("---")
        st.subheader("Agent's Reasoning")

        if reasoning:
            st.info(reasoning)
        else:
            st.info("No explanation returned from the AI model.")

    else:
        st.markdown("---")
        st.info(
            "Configure a farm location in the sidebar, then click **“Analyze Farm”** "
            "to see satellite NDVI, AI loan decisions, and full reasoning."
        )


if __name__ == "__main__":
    main()


