# 🌱 GreenChain Agent: AI-Powered Sustainable Finance

**Winner of the 'Dual Value' Challenge: Unlocking Capital for Sustainable Agriculture.**

## 🚀 Project Overview
GreenChain is an autonomous AI Agent that bridges the gap between **Financial Institutions** and **Sustainable Farmers**.
By leveraging **AWS Satellite Imagery (Sentinel-2)** and **GenAI**, it validates sustainable farming practices in real-time to approve micro-loans for underserved rural communities.

## 🎯 The Problem
* **Financial Exclusion:** Small farmers lack the paper trail (credit history) to get bank loans.
* **Greenwashing Risk:** Banks want to lend for sustainability but can't verify if a farm is actually "green" without expensive site visits.
* **Lack of Transparency:** Single-point-in-time analysis doesn't capture farming history.

## 💡 Our Solution
An AI Agent that acts as a "Digital Field Officer":
1.  **Perceives:** Fetches 6 months of satellite data (NDVI trend) using **AWS Open Data**.
2.  **Detects:** Checks for deforestation and land-use changes over 2 years.
3.  **Scores:** Calculates transparent sustainability metrics with component breakdown.
4.  **Reasons:** Uses **Google Gemini Pro** to analyze risks and provide recommendations.
5.  **Acts:** Approves loans with suggested interest rates and mints a **"Green Verification Certificate"**.

## 🛠️ Tech Stack (Sponsor Integration)
* **Satellite Data:** AWS Open Data Registry (Sentinel-2 L2A) via `pystac-client`
* **AI Engine:** Large Language Model (Google Gemini Pro) for risk reasoning
* **Visualization:** Plotly for interactive NDVI trend charts
* **Backend:** Python with advanced satellite services (multi-temporal analysis)
* **Frontend:** Streamlit with Folium maps (polygon drawing support)
* **Verification:** Cryptographic Hashing (Simulating Caffeine AI/ICP Blockchain)

## ⚡ How to Run
1.  Clone the repo:
    ```bash
    git clone https://github.com/yourusername/greenchain-agent.git
    cd greenchain-agent
    ```
2.  Install dependencies:
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  Set up environment variables (optional - see env-example.txt):
    ```bash
    # Copy the example file and add your API key
    cp env-example.txt .env.local
    # Edit .env.local with your Gemini API key
    ```
4.  Run the Agent:
    ```bash
    streamlit run app.py
    ```

### 🔑 API Keys Setup
- **Google Gemini API Key**: Required for AI analysis using Gemini Pro
  - Sign up at [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Get your API key from the dashboard
  - Add it to `.env.local` as `GEMINI_API_KEY=your_key_here`
- **Mock Mode**: The app includes mock modes for both satellite data and AI analysis

## ✨ Key Features
- **Multi-Temporal NDVI Analysis:** 6-month historical NDVI trends with consistency scoring
- **Deforestation Detection:** 2-year land-use change analysis to prevent greenwashing
- **Polygon Farm Boundaries:** Draw precise farm boundaries for accurate area analysis
- **Sustainability Score Breakdown:**
  - 📈 Vegetation Trend Score
  - 🔄 Farming Consistency Score
  - 🌳 No Deforestation Score
  - ☁️ Climate Resilience Score
- **Loan Risk Calculator:** Suggested interest rates and max loan amounts
- **Interactive NDVI Charts:** Plotly visualization of 6-month trends
- **AI-Powered Analysis:** Gemini Pro reasoning with risk factors and recommendations
- **Blockchain Verification:** Cryptographically secure certificates

## 🏗️ Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│  Advanced        │───▶│  Sustainability │
│  (Polygon Draw) │    │  Satellite Svc   │    │  Score Engine   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Multi-Temporal  │    │  Deforestation   │    │  Loan Risk      │
│ NDVI (6 months) │    │  Detection (2yr) │    │  Calculator     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ AWS Sentinel-2  │    │  Gemini Pro AI   │    │ Blockchain Hash │
│   (STAC API)    │    │  Analysis        │    │ & Certificate   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎥 Demo (4-Step Wizard)
1. **Select Location:** Click map OR draw polygon farm boundary
2. **Loan Details:** Select loan amount ($100-$10,000) and purpose
3. **Processing:** Multi-temporal NDVI, deforestation check, weather analysis, sustainability scoring
4. **Results:** View sustainability score, NDVI trends, deforestation status, AI analysis, and loan terms

## 📸 Screenshots
*(Add screenshots showing: polygon drawing, sustainability score breakdown, NDVI trend chart, results tabs)*

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Built with ❤️ for sustainable agriculture and financial inclusion**
