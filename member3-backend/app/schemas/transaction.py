import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token_symbol: str = "ETH"
    chain: str = "ethereum"
    block_number: int | None = None
    timestamp: datetime


class TransactionBulkCreate(BaseModel):
    """Used by Member 2's ingestion pipeline to push cleaned data in bulk."""
    transactions: list[TransactionCreate]


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token_symbol: str
    chain: str
    block_number: int | None = None
    timestamp: datetime
