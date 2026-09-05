"""
Integration point for Member 4 (AI/ML + Risk Engine).

Expected contract: given a wallet address (+ graph/transaction context),
return a risk score (0-100), a risk_level bucket, and human-readable reasons.
"""
import requests

from app.config import settings


def calculate_risk(wallet_address: str, graph_data: dict | None = None) -> dict:
    if settings.USE_MOCK_SERVICES:
        return _mock_risk(wallet_address, graph_data)
    return _call_real_service(wallet_address, graph_data)


def _call_real_service(wallet_address: str, graph_data: dict | None) -> dict:
    try:
        resp = requests.post(
            f"{settings.RISK_SERVICE_URL}/risk/calculate",
            json={"wallet_address": wallet_address, "graph_data": graph_data},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        return {
            "score": 0.0,
            "risk_level": "UNKNOWN",
            "reasons": [f"risk service unavailable: {exc}"],
            "model_version": "unavailable",
        }


def _mock_risk(wallet_address: str, graph_data: dict | None) -> dict:
    has_pattern = bool(graph_data and graph_data.get("patterns"))
    score = 72.5 if has_pattern else 24.0
    level = "HIGH" if has_pattern else "LOW"
    reasons = (
        [
            "Detected fund-splitting pattern across 2+ wallets",
            "Rapid transfer within 10 minutes of receipt",
            "Downstream hop reaches an unattributed exchange wallet",
        ]
        if has_pattern
        else ["No suspicious graph patterns detected", "Transaction volume within normal range"]
    )
    return {
        "score": score,
        "risk_level": level,
        "reasons": reasons,
        "model_version": "mock-v0",
    }
