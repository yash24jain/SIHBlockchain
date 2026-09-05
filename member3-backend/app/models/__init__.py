"""Import all models here so Base.metadata knows about every table
before create_all() is called (see app/main.py startup event)."""
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.risk import RiskScore, SuspiciousPattern
from app.models.vasp import VASP, VASPAttribution
from app.models.report import Report

__all__ = [
    "User",
    "Wallet",
    "Transaction",
    "RiskScore",
    "SuspiciousPattern",
    "VASP",
    "VASPAttribution",
    "Report",
]
