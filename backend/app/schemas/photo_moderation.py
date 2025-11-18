from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.media import MediaInfo


class PhotoModerationItem(BaseModel):
    """Элемент списка модерации аватаров."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(serialization_alias="photo_moderation_id")
    employee_id: int

    employee_first_name: str
    employee_middle_name: str | None = None
    employee_last_name: str

    status: str  # 'pending' | 'approved' | 'rejected'
    reviewer_employee_id: int | None = None
    reviewed_at: datetime | None = None
    reject_reason: str | None = None
    created_at: datetime

    photo: MediaInfo | None = None


class CreateModerationRequestMe(BaseModel):
    """Запрос на создание/замену заявки на модерацию собственной аватарки."""

    media_id: int = Field(..., gt=0)


class DecisionPayload(BaseModel):
    """Решение модератора по заявке."""

    decision: str = Field(..., pattern="^(approve|reject)$")
    reason: str | None = None

    @model_validator(mode="after")
    def _check_reason(self) -> DecisionPayload:
        if self.decision == "reject" and not (self.reason and self.reason.strip()):
            raise ValueError("Reject decision requires non-empty reason")
        return self


class ModerationList(BaseModel):
    """Список заявок на модерацию."""

    items: list[PhotoModerationItem]


class MyModerationStatus(BaseModel):
    """Статус последней заявки текущего пользователя."""

    has_request: bool
    last: PhotoModerationItem | None = None
