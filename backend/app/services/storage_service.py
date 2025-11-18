from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO
import mimetypes
import uuid

import anyio
import boto3
from botocore.client import Config

from app.core.config import settings


@dataclass(frozen=True)
class S3ObjectInfo:
    """Информация об объекте в S3-совместимом хранилище."""

    storage_key: str
    public_url: str | None = None
    presigned_url: str | None = None


_s3_client = None  # лениво инициализируемый клиент S3


def _get_client():
    """Возвращает S3-клиент, создавая его один раз на процесс."""
    global _s3_client  # noqa: PLW0603
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(s3={"addressing_style": "virtual"}),
        )
    return _s3_client


def make_storage_key(suffix: str | None = None) -> str:
    """Генерирует ключ хранения для объекта.

    Пример результата: "media/<uuid>.jpg".

    Параметры:
        suffix: расширение файла (с точкой или без), например ".jpg" или "jpg".
    """
    ext = (suffix or "").lstrip(".")
    fname = f"{uuid.uuid4().hex}{('.' + ext) if ext else ''}"
    return f"media/{fname}"


async def upload_fileobj(
    fp: BinaryIO,
    *,
    storage_key: str,
    content_type: str | None = None,
) -> S3ObjectInfo:
    """Загружает потоковый объект в бакет под заданным ключом."""
    ctype = content_type or "application/octet-stream"

    def _do() -> None:
        _get_client().upload_fileobj(
            Fileobj=fp,
            Bucket=settings.s3_bucket,
            Key=storage_key,
            ExtraArgs={"ContentType": ctype},
        )

    await anyio.to_thread.run_sync(_do)

    public = (
        f"{settings.s3_public_base.rstrip('/')}/{storage_key}"
        if settings.s3_public_base
        else None
    )
    return S3ObjectInfo(storage_key=storage_key, public_url=public)


def presign_put_url(
    storage_key: str,
    *,
    content_type: str | None = None,
    expires_seconds: int = 900,
) -> S3ObjectInfo:
    """Возвращает presigned URL для загрузки объекта PUT-запросом."""
    params: dict[str, str] = {
        "Bucket": settings.s3_bucket,
        "Key": storage_key,
    }
    if content_type:
        params["ContentType"] = content_type

    url = _get_client().generate_presigned_url(
        ClientMethod="put_object",
        Params=params,
        ExpiresIn=expires_seconds,
    )
    public = (
        f"{settings.s3_public_base.rstrip('/')}/{storage_key}"
        if settings.s3_public_base
        else None
    )
    return S3ObjectInfo(
        storage_key=storage_key,
        public_url=public,
        presigned_url=url,
    )


def object_public_url(storage_key: str) -> str | None:
    """Строит публичный URL по ключу хранения."""
    if not settings.s3_public_base:
        return None
    return f"{settings.s3_public_base.rstrip('/')}/{storage_key}"


async def delete_object(storage_key: str) -> None:
    """Удаляет объект из бакета по ключу хранения."""

    def _do() -> None:
        _get_client().delete_object(
            Bucket=settings.s3_bucket,
            Key=storage_key,
        )

    await anyio.to_thread.run_sync(_do)


def guess_ext_from_mime(content_type: str | None) -> str | None:
    """Определяет расширение файла по MIME-типу (без ведущей точки)."""
    if not content_type:
        return None
    ext = mimetypes.guess_extension(content_type)
    if ext:
        return ext.lstrip(".")
    return None
