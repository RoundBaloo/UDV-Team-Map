from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.media import MediaInfo

class PhotoModerationItem(BaseModel):
    id: int
    employee_id: int
    status: str  # 'pending' | 'approved' | 'rejected'
    reviewer_employee_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime
    photo: Optional[MediaInfo] = None

class CreateModerationRequestMe(BaseModel):
    media_id: int = Field(..., gt=0)

class CreateModerationRequestAdmin(BaseModel):
    employee_id: int = Field(..., gt=0)
    media_id: int = Field(..., gt=0)

class RejectPayload(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)

class ModerationList(BaseModel):
    items: list[PhotoModerationItem]
    total: int
    limit: int
    offset: int

class MyModerationStatus(BaseModel):
    has_request: bool
    last: Optional[PhotoModerationItem] = None
