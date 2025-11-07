# app/services/storage_service.py
from __future__ import annotations
from dataclasses import dataclass
from typing import BinaryIO, Optional
import mimetypes
import uuid
import boto3
from botocore.client import Config
import anyio

from app.core.config import settings

@dataclass(frozen=True)
class S3ObjectInfo:
    storage_key: str
    public_url: Optional[str] = None
    presigned_url: Optional[str] = None

def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=Config(s3={"addressing_style": "virtual"})  # YC совместим, virtual-hosted ok
    )

def make_storage_key(suffix: str | None = None) -> str:
    # Пример: avatars/2025/11/<uuid>.jpg
    # suffix можно передать из content-type (".jpg"), если знаем расширение
    ext = (suffix or "").lstrip(".")
    fname = f"{uuid.uuid4().hex}{('.' + ext) if ext else ''}"
    return f"media/{fname}"

async def upload_fileobj(fp: BinaryIO, *, storage_key: str, content_type: str | None = None) -> S3ObjectInfo:
    ctype = content_type or "application/octet-stream"

    def _do():
        _client().upload_fileobj(
            Fileobj=fp,
            Bucket=settings.s3_bucket,
            Key=storage_key,
            ExtraArgs={"ContentType": ctype}
        )

    await anyio.to_thread.run_sync(_do)

    public = f"{settings.s3_public_base.rstrip('/')}/{storage_key}" if settings.s3_public_base else None
    return S3ObjectInfo(storage_key=storage_key, public_url=public)

def presign_put_url(storage_key: str, *, content_type: str | None = None, expires_seconds: int = 900) -> S3ObjectInfo:
    params = {"Bucket": settings.s3_bucket, "Key": storage_key}
    if content_type:
        params["ContentType"] = content_type

    url = _client().generate_presigned_url(
        ClientMethod="put_object",
        Params=params,
        ExpiresIn=expires_seconds,
    )
    public = f"{settings.s3_public_base.rstrip('/')}/{storage_key}" if settings.s3_public_base else None
    return S3ObjectInfo(storage_key=storage_key, public_url=public, presigned_url=url)

def object_public_url(storage_key: str) -> Optional[str]:
    return f"{settings.s3_public_base.rstrip('/')}/{storage_key}" if settings.s3_public_base else None

async def delete_object(storage_key: str) -> None:
    def _do():
        _client().delete_object(Bucket=settings.s3_bucket, Key=storage_key)
    await anyio.to_thread.run_sync(_do)

def guess_ext_from_mime(content_type: str | None) -> str | None:
    if not content_type:
        return None
    ext = mimetypes.guess_extension(content_type)
    if ext:
        return ext.lstrip(".")
    return None
