"""
Integration point for Member 1 (Blockchain Forensics + Graph / NetworkX).

Two integration modes are supported:
1. In-process: if Member 1 ships a Python package/module, import it directly
   and call its functions inside `_call_real_service`.
2. HTTP microservice: if Member 1 exposes a FastAPI/Flask service, this
   client calls it over HTTP using settings.GRAPH_SERVICE_URL.

Until that module is ready, USE_MOCK_SERVICES=True (see .env) makes this
return realistic sample data so the rest of the API/frontend can be built
and demoed right now. Swap the mock out with zero changes to any router.
"""
import requests

from app.config import settings


def get_wallet_graph(wallet_address: str) -> dict:
    """Return graph nodes/edges + detected flow patterns for a wallet."""
    if settings.USE_MOCK_SERVICES:
        return _mock_graph(wallet_address)
    return _call_real_service(wallet_address)


def _call_real_service(wallet_address: str) -> dict:
    try:
        resp = requests.get(
            f"{settings.GRAPH_SERVICE_URL}/graph/{wallet_address}", timeout=15
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        # Fail soft so the API stays usable even if Member 1's service is down
        return {
            "wallet_address": wallet_address,
            "nodes": [],
            "edges": [],
            "patterns": [],
            "error": f"graph service unavailable: {exc}",
        }


def _mock_graph(wallet_address: str) -> dict:
    return {
        "wallet_address": wallet_address,
        "nodes": [
            {"id": wallet_address, "type": "target", "label": "Target wallet"},
            {"id": "0xAAA...111", "type": "peer", "label": "Peer wallet A"},
            {"id": "0xBBB...222", "type": "peer", "label": "Peer wallet B"},
            {"id": "0xCCC...333", "type": "exchange", "label": "Unknown exchange hot wallet"},
        ],
        "edges": [
            {"from": wallet_address, "to": "0xAAA...111", "amount": 2.5, "hop": 1},
            {"from": wallet_address, "to": "0xBBB...222", "amount": 1.8, "hop": 1},
            {"from": "0xAAA...111", "to": "0xCCC...333", "amount": 2.4, "hop": 2},
        ],
        "patterns": [
            {
                "pattern_type": "SPLITTING",
                "description": "Funds split into 2 wallets within 10 minutes",
                "related_addresses": ["0xAAA...111", "0xBBB...222"],
                "severity": "MEDIUM",
            }
        ],
    }
