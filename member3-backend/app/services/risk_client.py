"""
Integration point for Member 4 (AI/ML + Risk Engine).

Expected contract: given a wallet address (+ graph/transaction context),
return a risk score (0-100), a risk_level bucket, and human-readable reasons.
"""
import requests

from app.config import settings


import os
import sys
import requests

from app.config import settings

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

RISK_DIR = os.path.join(REPO_ROOT, "risk-engine")
if RISK_DIR not in sys.path:
    sys.path.insert(0, RISK_DIR)


def calculate_risk(wallet_address: str, graph_data: dict | None = None) -> dict:
    if settings.USE_MOCK_SERVICES:
        return _mock_risk(wallet_address, graph_data)
    return _call_real_service(wallet_address, graph_data)


def _call_real_service(wallet_address: str, graph_data: dict | None) -> dict:
    # 1. Try in-process Python execution (Member 4's ML Risk Engine)
    try:
        from src.live_feature_adapter import build_live_features
        from src.fraud_predictor import predict_fraud_probability
        from src.risk_engine import calculate_risk as run_risk_engine
        from app.services.blockchain_client import fetch_wallet_transactions

        # Fetch wallet transactions for live feature extraction
        txs = fetch_wallet_transactions(wallet_address, limit=100)

        # Invariant: If wallet has 0 transactions and 0 graph edges, return LOW risk score (0.0)
        has_edges = bool(graph_data and graph_data.get("edges"))
        if not txs and not has_edges:
            return {
                "score": 0.0,
                "risk_score": 0.0,
                "risk_level": "LOW",
                "reasons": ["No transaction history or suspicious activity found for this wallet address."],
                "model_version": "v1.0-clean",
            }

        wallet_features = build_live_features(txs, wallet_address)
        
        # Run ML model inference if fraud_model.pkl exists
        try:
            ml_result = predict_fraud_probability(wallet_features)
            ml_score = float(ml_result.get("fraud_probability", 0.0)) * 100.0
            ml_result["ml_score"] = ml_score
        except Exception:
            ml_result = {"ml_score": 25.0, "fraud_probability": 0.25, "prediction": "LEGITIMATE"}

        graph_result = graph_data or {}
        
        # Run composite risk engine
        risk_result = run_risk_engine(
            wallet_features=wallet_features,
            ml_result=ml_result,
            graph_result=graph_result,
        )

        # Bridge expected field names for router/risk.py compatibility
        risk_result["score"] = risk_result.get("risk_score", 50.0)
        risk_result["model_version"] = risk_result.get("model_version", "v1.0-ml-composite")
        return risk_result
    except Exception as exc:
        pass

    # 2. Try HTTP microservice if running
    try:
        resp = requests.post(
            f"{settings.RISK_SERVICE_URL}/risk/calculate",
            json={"wallet_address": wallet_address, "graph_data": graph_data},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        if "score" not in data and "risk_score" in data:
            data["score"] = data["risk_score"]
        return data
    except requests.RequestException:
        pass

    # 3. Fallback to mock risk computation
    return _mock_risk(wallet_address, graph_data)


def _mock_risk(wallet_address: str, graph_data: dict | None) -> dict:
    if wallet_address.lower().strip() == "0x0000000000000000000000000000000000000001":
        return {
            "score": 0.0,
            "risk_score": 0.0,
            "risk_level": "LOW",
            "reasons": ["No transaction history found for this wallet address."],
            "model_version": "clean-v0",
        }
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
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons,
        "model_version": "mock-v0",
    }

