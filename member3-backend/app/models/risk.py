"""
Risk scores + human-readable reasons, produced by Member 4's
AI/ML risk engine and also suspicious flow patterns detected by
Member 1's graph module.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0-100
    risk_level = Column(String(20), nullable=False)  # LOW/MEDIUM/HIGH/CRITICAL
    reasons = Column(JSON, default=list)  # ["Rapid fan-out to 40 wallets", ...]
    model_version = Column(String(50), default="v0-mock")
    created_at = Column(DateTime, default=datetime.utcnow)


class SuspiciousPattern(Base):
    """Patterns detected by Member 1's graph module (splitting, consolidation, etc.)"""
    __tablename__ = "suspicious_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # SPLITTING/CONSOLIDATION/RAPID_TRANSFER
    description = Column(String(500), nullable=True)
    related_addresses = Column(JSON, default=list)
    severity = Column(String(20), default="MEDIUM")
    detected_at = Column(DateTime, default=datetime.utcnow)
