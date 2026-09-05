"""
SIH26183 — Crypto Fraud & VASP Identification
Backend + Database module (Member 3).

Wires together: Auth -> Wallets -> Transactions -> Graph (Member 1)
-> Risk Engine (Member 4) -> VASP Attribution (Member 6) -> Reports.
This is the single API surface Member 5's React dashboard talks to.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, graph, reports, risk, transactions, vasp, wallets
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for SIH26183 Crypto Fraud & VASP Identification",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(wallets.router)
app.include_router(transactions.router)
app.include_router(graph.router)
app.include_router(risk.router)
app.include_router(vasp.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup():
    logger.info("Starting %s (debug=%s)", settings.APP_NAME, settings.DEBUG)
    # For MVP/dev: auto-create tables. Swap for Alembic migrations once the
    # schema stabilizes (see alembic/ folder).
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
