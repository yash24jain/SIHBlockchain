# Investigation Module
# Orchestrates: blockchain data -> attribution -> evidence -> investigation result

from datetime import datetime, timezone

from .attribution import (
    _import_blockchain_api,
    attribute_blockchain_data,
    normalize_address,
)
from .evidence import create_evidence_from_results


def _empty_summary():
    """Deterministic empty transaction summary."""
    return {
        "total_transactions": 0,
        "incoming_transactions": 0,
        "outgoing_transactions": 0,
        "unique_counterparties": 0,
        "matched_vasp_entities": 0,
    }


def _now_iso():
    """Current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _build_investigation_result(wallet, blockchain_data):
    """
    Build the clean investigation result from already-fetched
    blockchain data.

    Pipeline:
        attribution -> evidence -> investigation result

    Used by run_investigation() and kept separate so it can be tested
    with synthetic data without any network/API access.
    """
    wallet = normalize_address(wallet)
    blockchain_data = blockchain_data or {}
    transactions = blockchain_data.get("transactions", []) or []

    attribution_result = attribute_blockchain_data(blockchain_data)

    evidence_records = create_evidence_from_results(
        wallet_address=wallet,
        attribution_result=attribution_result,
        transactions=transactions,
    )

    return {
        "wallet": wallet,
        "chain": blockchain_data.get("chain", "ethereum"),
        "investigation_status": "complete",
        "total_transactions": len(transactions),
        "attributions": attribution_result.get("attributions", []),
        "evidence": [ev.to_dict() for ev in evidence_records],
        "transaction_summary": attribution_result.get(
            "summary", _empty_summary()
        ),
        "generated_at": _now_iso(),
    }


def run_investigation(wallet_address):
    """
    Orchestrate the full investigation pipeline.

    Pipeline:
        blockchain data -> attribution -> evidence -> investigation result

    Input:
        wallet_address (str): Ethereum wallet address to investigate

    Output:
        dict: Clean investigation result dictionary:

            {
                "wallet": "...",
                "chain": "ethereum",
                "investigation_status": "complete",
                "total_transactions": int,
                "attributions": [...],
                "evidence": [...],
                "transaction_summary": {...},
                "generated_at": "...",
            }

    NOTE: risk_score / risk_level are NOT calculated here. They belong
    to the Risk Engine (Member 4).
    """
    wallet = normalize_address(wallet_address)

    if not wallet:
        return {
            "wallet": "",
            "chain": "ethereum",
            "investigation_status": "error",
            "error": "No wallet address provided",
            "total_transactions": 0,
            "attributions": [],
            "evidence": [],
            "transaction_summary": _empty_summary(),
            "generated_at": _now_iso(),
        }

    try:
        blockchain_api = _import_blockchain_api()
        blockchain_data = blockchain_api.get_clean_blockchain_data(wallet)
    except Exception as exc:
        return {
            "wallet": wallet,
            "chain": "ethereum",
            "investigation_status": "error",
            "error": str(exc),
            "total_transactions": 0,
            "attributions": [],
            "evidence": [],
            "transaction_summary": _empty_summary(),
            "generated_at": _now_iso(),
        }

    return _build_investigation_result(wallet, blockchain_data)