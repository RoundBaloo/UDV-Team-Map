from __future__ import annotations

from pydantic import BaseModel, Field


class MediaInfo(BaseModel):
    """Краткая информация о медиа-объекте (например, фото)."""

    id: int = Field(serialization_alias="media_id")
    public_url: str | None = None


class InitUploadRequest(BaseModel):
    """Запрос на инициализацию загрузки файла в хранилище."""

    content_type: str = Field(
        ...,
        description="MIME-тип будущего объекта, например image/jpeg",
    )


class InitUploadResponse(BaseModel):
    """Ответ с данными для прямой загрузки в хранилище."""

    storage_key: str
    upload_url: str
    public_url: str | None = None  # Если настроен S3_PUBLIC_BASE


class FinalizeUploadRequest(BaseModel):
    """Запрос на фиксацию загруженного файла."""

    storage_key: str


class MediaItem(BaseModel):
    """Полная информация о сохранённом медиа-объекте."""

    id: int = Field(serialization_alias="media_id")
    storage_key: str
    public_url: str | None = None
