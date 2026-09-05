"""
A blockchain wallet/address under investigation.
Populated by Member 2's blockchain-data pipeline; enriched by
Member 1 (graph features) and Member 4 (risk score).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(100), unique=True, nullable=False, index=True)
    chain = Column(String(30), default="ethereum")  # ethereum, bsc, polygon, etc.
    label = Column(String(255), nullable=True)  # e.g. "Suspected mixer"
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    tx_count = Column(Integer, default=0)

    # Latest cached values (source of truth is risk_scores / vasp_attributions
    # tables below; these are denormalized for fast dashboard search/sort)
    latest_risk_score = Column(Float, nullable=True)
    latest_risk_level = Column(String(20), nullable=True)  # LOW/MEDIUM/HIGH/CRITICAL

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
