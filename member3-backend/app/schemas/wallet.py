import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class WalletCreate(BaseModel):
    address: str
    chain: str = "ethereum"
    label: Optional[str] = None


class WalletOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    address: str
    chain: str
    label: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    tx_count: int
    latest_risk_score: Optional[float] = None
    latest_risk_level: Optional[str] = None
    created_at: datetime


class WalletSearchResult(BaseModel):
    wallets: list[WalletOut]
    total: int
