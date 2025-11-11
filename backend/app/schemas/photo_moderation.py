from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict
from app.schemas.media import MediaInfo


class PhotoModerationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(serialization_alias="photo_moderation_id")
    employee_id: int

    # НОВОЕ: ФИО отдельными полями
    employee_first_name: str
    employee_middle_name: Optional[str] = None
    employee_last_name: str

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
        if self.decision == "reject" and not (self.reason and self.reason.strip()):
            raise ValueError("Reject decision requires non-empty reason")
        return self


class ModerationList(BaseModel):
    items: list[PhotoModerationItem]


class MyModerationStatus(BaseModel):
    has_request: bool
    last: Optional[PhotoModerationItem] = None
