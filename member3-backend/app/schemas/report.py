import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ReportRequest(BaseModel):
    wallet_address: str


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    wallet_id: uuid.UUID
    file_path: str | None = None
    status: str
    created_at: datetime
    completed_at: datetime | None = None
