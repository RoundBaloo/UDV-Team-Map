from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator
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

class DecisionPayload(BaseModel):
    decision: str = Field(..., pattern="^(approve|reject)$")
    reason: str | None = None

    @model_validator(mode="after")
    def _check_reason(self):
        if self.decision == "reject":
            if not (self.reason and self.reason.strip()):
                raise ValueError("Reject decision requires non-empty reason")
        return self

class ModerationList(BaseModel):
    items: list[PhotoModerationItem]

class MyModerationStatus(BaseModel):
    has_request: bool
    last: Optional[PhotoModerationItem] = None
