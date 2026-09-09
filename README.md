# SIH26183 — Crypto Fraud & VASP Identification (CryptoTrace)

**CryptoTrace** is an end-to-end blockchain forensics and Virtual Asset Service Provider (VASP) identification platform designed for Smart India Hackathon (SIH) Problem Statement **26183**.

The system ingests on-chain transaction data, builds multi-hop graph topologies, evaluates composite risk scores, attributes target transactions to known exchange/VASP entity clusters, and compiles formal PDF investigation reports.

---

## 🚀 How to Run Locally

### 1. Prerequisites

Ensure the following tools are installed on your system before proceeding:

* **Python:** `v3.11+`
* **Node.js:** `v18.0.0+` / **npm:** `v9.0.0+`
* **PostgreSQL:** `v14+`
* **Git:** `v2.30+`

---

### 2. Clone Repository

```bash
git clone https://github.com/devanupriyj-code/SIHBlockchain.git
cd SIHBlockchain
```

---

### 3. PostgreSQL Setup

The backend connects to PostgreSQL to persist wallets, transactions, risk scores, patterns, VASP attributions, and report metadata.

1. Ensure PostgreSQL service is running on `localhost:5432`.
2. Open `psql` or your database manager and create the user and database:

```sql
CREATE USER sih_user WITH PASSWORD 'YOUR_DB_PASSWORD';
CREATE DATABASE crypto_fraud_db OWNER sih_user;
GRANT ALL PRIVILEGES ON DATABASE crypto_fraud_db TO sih_user;
```

> **Note:** Database tables (`users`, `wallets`, `transactions`, `risk_scores`, `suspicious_patterns`, `vasp_attributions`, `reports`) are automatically initialized on backend startup via SQLAlchemy (`Base.metadata.create_all`).

---

### 4. Backend Setup (`member3-backend/`)

The backend is built with **FastAPI** and provides the centralized API Gateway and database integration.

1. Navigate to the backend directory:
   ```bash
   cd member3-backend
   ```

2. Create and activate a Python virtual environment:
   * **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   * **Windows (CMD):**
     ```cmd
     python -m venv .venv
     .venv\Scripts\activate.bat
     ```
   * **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   pip install reportlab
   ```

4. Configure environment variables (create a `.env` file in `member3-backend/`):
   ```env
   APP_NAME="SIH26183 Crypto Fraud Backend"
   DEBUG=True
   DATABASE_URL=postgresql://sih_user:YOUR_DB_PASSWORD@localhost:5432/crypto_fraud_db
   SECRET_KEY=YOUR_SECRET_KEY
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   USE_MOCK_SERVICES=False
   ```

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

* **API Gateway Base URL:** `http://localhost:8000`
* **Interactive OpenAPI Docs:** `http://localhost:8000/docs`
* **Health Check Endpoint:** `http://localhost:8000/health`

---

### 5. Frontend Setup (`cryptofraud-dashboard/`)

The investigator UI is built with **React** and **Vite**.

1. Open a new terminal window/tab and navigate to the frontend directory:
   ```bash
   cd cryptofraud-dashboard
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the Vite React development server:
   ```bash
   npm run dev
   ```

* **Investigator Dashboard URL:** `http://localhost:5173`

---

### 6. Running Both Services & System Architecture

Running the application locally requires **two active terminals**:

* **Terminal 1:** PostgreSQL Service + FastAPI Backend (`http://localhost:8000`)
* **Terminal 2:** React / Vite Frontend (`http://localhost:5173`)

#### End-to-End System Architecture:

```text
React Dashboard (Port 5173)
        ↓  (HTTP / REST API with JWT Bearer Token)
FastAPI Backend Gateway (Port 8000)
        ↓
  ┌─────┴──────────────────┬──────────────────┬─────────────────┐
  ↓                        ↓                  ↓                 ↓
Blockchain Parser     Graph Engine       Risk Engine     VASP Attribution
(On-chain Data)     (NetworkX Graph)   (30/30/40 Model)  (Entity Matching)
  └─────┬──────────────────┴──────────────────┴─────────────────┘
        ↓
PostgreSQL Database (Port 5432 / crypto_fraud_db)
        ↓
Investigation PDF Report Generator (ReportLab)
```

---

### 7. Using the Application

1. Open `http://localhost:5173` in your web browser.
2. The dashboard automatically authenticates an investigator session.
3. Click **Investigation** in the sidebar navigation.
4. Enter a target cryptocurrency wallet address in the search field.
5. Click **Analyze Wallet**.
6. Review the live investigation findings:
   * Total transaction count
   * Transaction flow graph visualization and node inspection
   * Suspicious pattern indicators (e.g. fund-splitting, rapid movement)
   * **Investigation Risk Score** (0–100) & Risk Level (`HIGH`, `MEDIUM`, `LOW`)
   * Destination VASP attribution & confidence rating
   * On-chain transaction breakdown table
7. Click **Generate Investigation Report** to compile a formal backend PDF report.
8. Download the resulting PDF file (`CryptoTrace_Investigation_Report_<wallet>.pdf`).

---

### 8. Demo / Test Wallet

* **Target Demo Wallet Address:** `0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae`
* **Expected Analysis Results:**
  * `29` Ingested transactions
  * **Investigation Risk Score:** `72.5 / 100` (`HIGH`)
  * **Graph Topology:** `4` Nodes, `3` Flow Edges
  * **Suspicious Signals:** Fund splitting across intermediary wallets, rapid transfers under 10 minutes, hop reaching exchange cluster.
  * **VASP Match:** Binance Hot Wallet (`80.0%` attribution confidence)

---

### 9. Empty / Inactive Wallet Invariant Test

* **Empty Test Wallet Address:** `0x0000000000000000000000000000000000000001`
* **Expected System Invariants:**
  * `0` Ingested transactions
  * **Investigation Risk Score:** `0.0 / 100` (`LOW`)
  * **Graph Topology:** `1` Target Node, `0` Flow Edges
  * **VASP Match:** `Unattributed / None (0.0%)`

---

### 10. API Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /health` | GET | API Gateway health check status |
| `POST /auth/register` | POST | Register new investigator user account |
| `POST /auth/login` | POST | Authenticate user and receive JWT Bearer token |
| `GET /auth/me` | GET | Retrieve profile of authenticated user |
| `POST /risk/calculate` | POST | Run composite risk model & persist investigation results |
| `GET /transactions` | GET | Fetch transactions for wallet from PostgreSQL |
| `GET /graph/{wallet_address}` | GET | Retrieve graph nodes, edges, and detected flow patterns |
| `POST /vasp/attribute/{wallet_address}` | POST | Run VASP entity matching & attribution |
| `POST /reports/generate` | POST | Trigger background PDF investigation report generation |
| `GET /reports/{report_id}/download` | GET | Stream generated PDF report (`application/pdf`) |

---

### 11. Troubleshooting

* **Backend won't start:** Ensure virtual environment is activated (`.venv`), requirements installed (`pip install -r requirements.txt`), and PostgreSQL service is running on port `5432`.
* **401 Unauthorized:** Protected endpoints require a valid JWT `Authorization: Bearer <token>` header. The frontend automatically handles login via `api.ensureAuthToken()`.
* **Port 5432 unavailable:** PostgreSQL is stopped or configured on another port. Update `DATABASE_URL` in `.env`.
* **Port 8000 / 5173 in use:** Terminate any existing background `uvicorn` or `vite` dev server processes occupying ports 8000 or 5173.

---

### 12. Project Structure

```text
SIHBlockchain/
├── member3-backend/             # FastAPI Gateway, Auth, DB models, Endpoints & Integration Adapters
├── cryptofraud-dashboard/       # React / Vite Investigator Dashboard (Member 5)
├── blockchain/                  # Blockchain data parser, Etherscan API client & datasets (Member 2)
├── graph-and-forensic-analysis/ # NetworkX graph builder, topology tracer & pattern detector (Member 1)
├── risk-engine/                 # Composite Risk Engine (30% Behavioral + 30% ML + 40% Graph) (Member 4)
├── vasp/                        # VASP entity database & counterparty attribution module (Member 6)
└── README.md                    # System setup and documentation guide
```

---

### 13. ✅ Verification Commands

To verify the codebase setup locally:

* **Frontend Build Check:**
  ```bash
  cd cryptofraud-dashboard
  npm run build
  ```

* **Backend API & VASP Test Suite:**
  ```bash
  pytest member3-backend/tests test_vasp_improved.py vasp/tests -v
  ```
