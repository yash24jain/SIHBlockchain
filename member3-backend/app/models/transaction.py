"""
On-chain transactions. Bulk-ingested from Member 2's cleaned
blockchain-data output.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tx_hash = Column(String(100), unique=True, nullable=False, index=True)
    from_address = Column(String(100), nullable=False, index=True)
    to_address = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    token_symbol = Column(String(20), default="ETH")
    chain = Column(String(30), default="ethereum")
    block_number = Column(BigInteger, nullable=True)
    timestamp = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
