"""VASP (Virtual Asset Service Provider) attribution — Member 6's module."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class VASP(Base):
    """Known exchange/entity registry (e.g. Binance, Coinbase hot wallets)."""
    __tablename__ = "vasps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    known_addresses = Column(JSON, default=list)
    jurisdiction = Column(String(100), nullable=True)
    entity_type = Column(String(50), default="exchange")  # exchange/mixer/darknet/unknown
    created_at = Column(DateTime, default=datetime.utcnow)


class VASPAttribution(Base):
    """Result of attributing a wallet to a VASP, with confidence + evidence."""
    __tablename__ = "vasp_attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False, index=True)
    vasp_id = Column(UUID(as_uuid=True), ForeignKey("vasps.id"), nullable=True)
    vasp_name_guess = Column(String(150), nullable=True)  # used if vasp_id unknown
    confidence_score = Column(Float, default=0.0)  # 0-1
    evidence = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
