# app/schemas/media.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class MediaInfo(BaseModel):
    id: int
    public_url: Optional[str] = None

class InitUploadRequest(BaseModel):
    content_type: str = Field(..., description="MIME типа будущего объекта, напр. image/jpeg")

class InitUploadResponse(BaseModel):
    storage_key: str
    upload_url: str
    public_url: Optional[str] = None   # если настроен S3_PUBLIC_BASE

class FinalizeUploadRequest(BaseModel):
    storage_key: str

class MediaItem(BaseModel):
    id: int
    storage_key: str
    public_url: Optional[str] = None
