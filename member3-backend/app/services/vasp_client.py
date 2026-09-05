"""
Integration point for Member 6 (VASP + Reports).

Given a wallet address, attribute it to a known VASP/entity with a
confidence score and evidence list. Also used when generating the
final investigation PDF (routers/reports.py).
"""
import requests

from app.config import settings


def attribute_vasp(wallet_address: str) -> dict:
    if settings.USE_MOCK_SERVICES:
        return _mock_vasp(wallet_address)
    return _call_real_service(wallet_address)


def _call_real_service(wallet_address: str) -> dict:
    try:
        resp = requests.get(
            f"{settings.VASP_SERVICE_URL}/vasp/attribute/{wallet_address}", timeout=15
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        return {
            "vasp_name_guess": None,
            "confidence_score": 0.0,
            "evidence": [f"vasp service unavailable: {exc}"],
        }


def _mock_vasp(wallet_address: str) -> dict:
    return {
        "vasp_name_guess": "Unknown Exchange (cluster match)",
        "confidence_score": 0.63,
        "evidence": [
            "Wallet clusters with 3 known deposit addresses of Exchange-X",
            "Deposit pattern matches Exchange-X's hot wallet rotation schedule",
        ],
    }
