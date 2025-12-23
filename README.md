# 🌱 GreenChain Agent: AI-Powered Sustainable Finance

**Winner of the 'Dual Value' Challenge: Unlocking Capital for Sustainable Agriculture.**

## 🚀 Project Overview
GreenChain is an autonomous AI Agent that bridges the gap between **Financial Institutions** and **Sustainable Farmers**.
By leveraging **AWS Satellite Imagery (Sentinel-2)** and **GenAI**, it validates sustainable farming practices in real-time to approve micro-loans for underserved rural communities.

## 🎯 The Problem
* **Financial Exclusion:** Small farmers lack the paper trail (credit history) to get bank loans.
* **Greenwashing Risk:** Banks want to lend for sustainability but can't verify if a farm is actually "green" without expensive site visits.

## 💡 Our Solution
An AI Agent that acts as a "Digital Field Officer":
1.  **Perceives:** Fetches real-time satellite data (NDVI/Vegetation Index) using **AWS Open Data**.
2.  **Reasons:** Uses **Claude 3.5 Sonnet** to analyze the crop health and farming history.
3.  **Acts:** Approves loans and mints a **"Green Verification Certificate"** anchored on a simulated ledger.

## 🛠️ Tech Stack (Sponsor Integration)
* **Satellite Data:** AWS Open Data Registry (Sentinel-2 L2A) via `pystac-client`.
* **AI Engine:** Large Language Model (Claude 3.5 Sonnet) for risk reasoning.
* **Backend:** Python (FastAPI/Lambda structure).
* **Frontend:** Streamlit.
* **Verification:** Cryptographic Hashing (Simulating Caffeine AI/ICP Blockchain).

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
3.  Run the Agent:
    ```bash
    streamlit run app.py
    ```

## ✨ Key Features
- **Real-time Satellite Analysis:** Live NDVI (Normalized Difference Vegetation Index) calculation from Sentinel-2 data
- **AI-Powered Risk Assessment:** Claude 3.5 Sonnet analyzes crop health and sustainability metrics
- **Instant Loan Decisions:** Automated approval process based on verified sustainable practices
- **Blockchain Verification:** Cryptographically secure certificates with unique hashes
- **Interactive Dashboard:** Streamlit interface with maps, satellite imagery, and decision visualization
- **PDF Certificate Generation:** Downloadable verification documents for banking records

## 🏗️ Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│   AI Agent       │───▶│  Verification   │
│                 │    │  (Claude 3.5)    │    │   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ AWS Satellite   │    │  Risk Analysis   │    │ Blockchain Hash │
│   Data (STAC)   │    │  & Reasoning     │    │   Generation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🎥 Demo
1. **Enter Farm Coordinates:** Input latitude/longitude (e.g., Kansas: 37.669, -100.749)
2. **Analyze Sustainability:** Agent fetches Sentinel-2 satellite data and calculates NDVI
3. **AI Decision:** Claude analyzes crop health and approves/rejects loans
4. **Generate Certificate:** Download blockchain-verified PDF for banking records

## 📸 Screenshots
*(Add a screenshot of your Streamlit Dashboard showing the "Approved" certificate here)*

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
