import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class VASPOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    known_addresses: list[str]
    jurisdiction: str | None = None
    entity_type: str


class VASPAttributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    wallet_id: uuid.UUID
    vasp_name_guess: str | None = None
    confidence_score: float
    evidence: list[str]
    created_at: datetime
