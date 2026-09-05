import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RiskScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: uuid.UUID
    wallet_id: uuid.UUID
    score: float
    risk_level: str
    reasons: list[str]
    model_version: str
    created_at: datetime


class SuspiciousPatternOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    wallet_id: uuid.UUID
    pattern_type: str
    description: str | None = None
    related_addresses: list[str]
    severity: str
    detected_at: datetime


class RiskCalculateRequest(BaseModel):
    wallet_address: str


class GraphAnalysisOut(BaseModel):
    """Shape returned to the frontend for the interactive transaction graph."""
    wallet_address: str
    nodes: list[dict]
    edges: list[dict]
    patterns: list[dict]
