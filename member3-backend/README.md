# SIH26183 — Crypto Fraud & VASP Identification
### Backend + Database module (Member 3)

FastAPI + PostgreSQL backend that connects every team member's module into
one API for the React dashboard (Member 5):

```
Suspect Wallet → Blockchain Data (M2) → Graph Analysis (M1) → Risk Engine (M4)
              → VASP Attribution (M6) → Dashboard (M5) → Investigation Report (M6)
```

## 1. Project structure

```
member3-backend/
├── app/
│   ├── main.py              # FastAPI app, router wiring, startup
│   ├── config.py            # env-based settings (DB, JWT, other members' service URLs)
│   ├── database.py          # SQLAlchemy engine/session/Base
│   ├── models/               # ORM tables (users, wallets, transactions, risk, vasp, reports)
│   ├── schemas/               # Pydantic request/response models
│   ├── routers/               # REST endpoints, one file per resource
│   │   ├── auth.py            # register/login/me (JWT)
│   │   ├── wallets.py         # CRUD + search wallets
│   │   ├── transactions.py    # bulk ingest (Member 2) + query
│   │   ├── graph.py           # wallet transaction graph (Member 1)
│   │   ├── risk.py            # risk scoring pipeline (Member 4)
│   │   ├── vasp.py            # VASP attribution (Member 6)
│   │   └── reports.py         # PDF report generation (Member 6)
│   ├── auth/                  # password hashing, JWT, current-user dependency
│   ├── services/               # integration clients to other members' modules
│   │   ├── graph_client.py     # → Member 1
│   │   ├── blockchain_client.py# → Member 2
│   │   ├── risk_client.py      # → Member 4
│   │   └── vasp_client.py      # → Member 6
│   └── utils/logger.py
├── tests/                       # pytest tests
├── init_db.sql                  # raw SQL schema (alternative to auto-create)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml            # postgres + backend, one command to run everything
├── .env.example
└── README.md
```

## 2. Quick start (Docker — recommended)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- Postgres: localhost:5432 (user: `sih_user`, pass: `sih_pass`, db: `crypto_fraud_db`)

Tables are created automatically on startup. To use the raw SQL file instead:
```bash
docker exec -i sih_postgres psql -U sih_user -d crypto_fraud_db < init_db.sql
```

## 3. Quick start (without Docker)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start a local Postgres and update DATABASE_URL in .env accordingly
cp .env.example .env

uvicorn app.main:app --reload
```

## 4. Auth flow

```bash
# Register
curl -X POST localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@sih.com","password":"Passw0rd!"}'

# Login → get JWT
curl -X POST localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Passw0rd!"}'

# Use the token
curl localhost:8000/wallets -H "Authorization: Bearer <access_token>"
```

## 5. How each teammate plugs in

**Member 1 (Graph/NetworkX)** — implement your logic, then either:
- expose it as a small FastAPI/Flask service and set `GRAPH_SERVICE_URL` in `.env`, matching the contract in `app/services/graph_client.py::_call_real_service`, **or**
- hand me your module and I'll call it in-process from `graph_client.py`.
Expected response shape: `{wallet_address, nodes[], edges[], patterns[]}` (see the mock in the same file).

**Member 2 (Blockchain data)** — push cleaned transactions straight into the DB:
```
POST /transactions/bulk
{ "transactions": [ {tx_hash, from_address, to_address, amount, token_symbol, chain, block_number, timestamp}, ... ] }
```

**Member 4 (Risk/ML engine)** — same pattern as Member 1, via `RISK_SERVICE_URL` / `app/services/risk_client.py`. Expected response: `{score, risk_level, reasons[], model_version}`.

**Member 5 (Frontend)** — talk to this API only. Key endpoints:
- `GET /wallets?q=...&risk_level=...` — search/list for the dashboard table
- `GET /wallets/{address}` — wallet detail
- `GET /graph/{address}` — data for the interactive graph
- `GET /risk/{address}` and `GET /risk/{address}/patterns` — risk + reasons
- `GET /vasp/{address}` — VASP attribution
- `POST /reports/generate` then `GET /reports/{id}` (poll) then `GET /reports/{id}/download`
CORS is open to `http://localhost:3000` and `:5173` by default — add your dev URL to `CORS_ORIGINS` in `.env` if different.

**Member 6 (VASP + Reports)** — attribution via `VASP_SERVICE_URL` / `app/services/vasp_client.py` (same contract pattern). For reports, replace the stub in `app/routers/reports.py::_generate_report_file` with your real PDF generator (reportlab/weasyprint) — it already runs as a background task and writes to the `reports` table.

Until any of these are ready, `USE_MOCK_SERVICES=True` in `.env` makes the backend return realistic sample data automatically, so the API and frontend can be built and demoed end-to-end right now. Flip it to `False` per-service once each teammate's module is live.

## 6. Running tests

```bash
pytest -v
```

## 7. Notes / next steps

- Auto `create_all()` is fine for the MVP; switch to Alembic migrations (folder already scaffolded) once the schema stabilizes.
- Add role-based checks (`require_admin` in `app/auth/dependencies.py`) to any endpoint that should be investigator/admin-only.
- Rate limiting / pagination limits should be tightened before a public demo deploy.
