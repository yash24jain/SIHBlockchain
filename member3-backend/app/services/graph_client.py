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
import os
import sys
import requests

from app.config import settings

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

GRAPH_DIR = os.path.join(REPO_ROOT, "graph-and-forensic-analysis")
if GRAPH_DIR not in sys.path:
    sys.path.insert(0, GRAPH_DIR)


def get_wallet_graph(wallet_address: str) -> dict:
    """Return graph nodes/edges + detected flow patterns for a wallet."""
    if settings.USE_MOCK_SERVICES:
        return _mock_graph(wallet_address)
    return _call_real_service(wallet_address)


def _call_real_service(wallet_address: str) -> dict:
    # 1. Try in-process Python module execution (Member 1's service)
    try:
        from graph.service import generate_wallet_graph_payload
        payload = generate_wallet_graph_payload(wallet_address)
        if payload and payload.get("nodes"):
            # Bridge features dict expected by risk_engine
            patterns = payload.get("patterns", [])
            has_splitting = any("peel" in str(p.get("pattern_type","")).lower() or "split" in str(p.get("description","")).lower() for p in patterns)
            has_rapid = any("rapid" in str(p.get("pattern_type","")).lower() for p in patterns)
            has_consolidation = any("consolidation" in str(p.get("description","")).lower() for p in patterns)
            
            payload["features"] = {
                "wallet_count": len(payload.get("nodes", [])),
                "transaction_count": len(payload.get("edges", [])),
                "destination_count": len([n for n in payload.get("nodes", []) if n.get("type") in ("exchange", "peer")]),
                "path_count": len(patterns) or 1,
                "fund_splitting": has_splitting,
                "fund_consolidation": has_consolidation,
                "rapid_movement": has_rapid,
                "high_value_transfer": any(float(e.get("amount", 0.0)) > 5.0 for e in payload.get("edges", [])),
                "max_hops": max([int(n.get("hop", 0)) for n in payload.get("nodes", [])] or [1])
            }
            return payload
    except Exception as exc:
        pass

    # 2. Try HTTP microservice if running
    try:
        resp = requests.get(
            f"{settings.GRAPH_SERVICE_URL}/graph/{wallet_address}", timeout=5
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        pass

    # 3. Fallback to realistic mock data
    return _mock_graph(wallet_address)


def _mock_graph(wallet_address: str) -> dict:
    if wallet_address.lower().strip() == "0x0000000000000000000000000000000000000001":
        return {
            "wallet_address": wallet_address,
            "nodes": [{"id": wallet_address, "type": "target", "label": "Target wallet"}],
            "edges": [],
            "patterns": [],
            "features": {
                "wallet_count": 1,
                "transaction_count": 0,
                "destination_count": 0,
                "path_count": 0,
                "fund_splitting": False,
                "fund_consolidation": False,
                "rapid_movement": False,
                "high_value_transfer": False,
                "max_hops": 0
            }
        }
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
        "features": {
            "wallet_count": 4,
            "transaction_count": 3,
            "destination_count": 3,
            "path_count": 2,
            "fund_splitting": True,
            "fund_consolidation": False,
            "rapid_movement": True,
            "high_value_transfer": False,
            "max_hops": 2
        }
    }

