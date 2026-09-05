"""
Integration point for Member 2 (Blockchain Data + APIs).

Member 2's job is to fetch + clean raw on-chain data (Etherscan/Alchemy/etc.)
and hand it to the backend. In practice they will either:
  a) call POST /transactions/bulk directly (see routers/transactions.py), or
  b) run as a service this client pulls from.

This client covers option (b) / on-demand refresh, with mock fallback.
"""
import requests

from app.config import settings


def fetch_wallet_transactions(wallet_address: str, limit: int = 50) -> list[dict]:
    if settings.USE_MOCK_SERVICES:
        return _mock_transactions(wallet_address, limit)
    return _call_real_service(wallet_address, limit)


def _call_real_service(wallet_address: str, limit: int) -> list[dict]:
    try:
        resp = requests.get(
            f"{settings.BLOCKCHAIN_SERVICE_URL}/wallet/{wallet_address}/transactions",
            params={"limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        return []


def _mock_transactions(wallet_address: str, limit: int) -> list[dict]:
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    return [
        {
            "tx_hash": f"0xmocktx{i:04d}",
            "from_address": wallet_address,
            "to_address": f"0xPEER{i:04d}",
            "amount": round(0.1 * (i + 1), 3),
            "token_symbol": "ETH",
            "chain": "ethereum",
            "block_number": 19000000 + i,
            "timestamp": (now - timedelta(hours=i)).isoformat(),
        }
        for i in range(min(limit, 5))
    ]
