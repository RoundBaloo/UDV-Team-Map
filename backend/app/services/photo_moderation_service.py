from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.media import Media
from app.models.photo_moderation import PhotoModeration
from app.services.media_service import delete_media_and_object_by_id


# --- доменные исключения ---


class ModerationError(Exception):
    """Базовое исключение для операций модерации."""


class NotFound(ModerationError):
    """Ресурс не найден."""


class Forbidden(ModerationError):
    """Операция запрещена."""


class BadRequest(ModerationError):
    """Неверный запрос или данные."""


class Conflict(ModerationError):
    """Конфликт состояний (например, повторная обработка заявки)."""


# --- helpers ---


async def _ensure_employee(
    session: AsyncSession,
    employee_id: int,
) -> Employee:
    """Возвращает сотрудника по id или бросает NotFound."""
    res = await session.execute(
        select(Employee).where(Employee.id == employee_id),
    )
    emp = res.scalar_one_or_none()
    if not emp:
        raise NotFound(f"Employee #{employee_id} not found")
    return emp


async def _ensure_media(
    session: AsyncSession,
    media_id: int,
) -> Media:
    """Возвращает media по id или бросает NotFound."""
    res = await session.execute(
        select(Media).where(Media.id == media_id),
    )
    media = res.scalar_one_or_none()
    if not media:
        raise NotFound(f"Media #{media_id} not found")
    return media


async def _get_by_id(
    session: AsyncSession,
    moderation_id: int,
) -> PhotoModeration | None:
    """Возвращает заявку модерации по id или None."""
    res = await session.execute(
        select(PhotoModeration).where(PhotoModeration.id == moderation_id),
    )
    return res.scalar_one_or_none()


# --- public API ---


async def create_or_replace_request_for_employee(
    session: AsyncSession,
    employee_id: int,
    media_id: int,
) -> PhotoModeration:
    """Создаёт новую pending-заявку на модерацию, удаляя прошлые заявки сотрудника."""
    await _ensure_employee(session, employee_id)
    await _ensure_media(session, media_id)

    await session.execute(
        delete(PhotoModeration).where(
            PhotoModeration.employee_id == employee_id,
        ),
    )

    pm = PhotoModeration(
        employee_id=employee_id,
        media_id=media_id,
        status="pending",
        reviewer_employee_id=None,
        reviewed_at=None,
        reject_reason=None,
    )
    session.add(pm)
    await session.flush()
    return pm


async def get_latest_for_employee(
    session: AsyncSession,
    employee_id: int,
) -> PhotoModeration | None:
    """Возвращает последнюю заявку сотрудника или None, если заявок нет."""
    res = await session.execute(
        select(PhotoModeration)
        .where(PhotoModeration.employee_id == employee_id)
        .order_by(PhotoModeration.created_at.desc())
        .limit(1),
    )
    return res.scalar_one_or_none()


async def list_pending(session: AsyncSession) -> list[PhotoModeration]:
    """Возвращает все заявки в статусе pending."""
    rows = (
        await session.execute(
            select(PhotoModeration)
            .where(PhotoModeration.status == "pending")
            .order_by(PhotoModeration.created_at.asc()),
        )
    ).scalars().all()
    return rows


async def approve(
    session: AsyncSession,
    *,
    moderation_id: int,
    reviewer_id: int,
) -> PhotoModeration:
    """Подтверждает заявку: статус approved и установка photo_id сотруднику."""
    pm = await _get_by_id(session, moderation_id)
    if not pm:
        raise NotFound("Moderation request not found")

    if pm.status != "pending":
        raise Conflict("Request is not pending (already processed)")

    employee = (
        await session.execute(
            select(Employee).where(Employee.id == pm.employee_id),
        )
    ).scalar_one_or_none()
    if not employee:
        raise NotFound("Employee not found")

    old_photo_id = employee.photo_id

    employee.photo_id = pm.media_id
    pm.status = "approved"
    pm.reviewer_employee_id = reviewer_id
    pm.reviewed_at = datetime.now(timezone.utc)

    session.add(employee)
    session.add(pm)

    await session.flush()

    if old_photo_id and old_photo_id != pm.media_id:
        try:
            await delete_media_and_object_by_id(session, old_photo_id)
        except Exception:  # намеренно глушим ошибку удаления старого объекта
            pass

    return pm


async def reject(
    session: AsyncSession,
    *,
    moderation_id: int,
    reviewer_id: int,
    reason: str,
) -> PhotoModeration:
    """Отклоняет заявку: статус rejected и сохранение причины отказа."""
    if not reason or not reason.strip():
        raise BadRequest("Reject reason is required")

    pm = await _get_by_id(session, moderation_id)
    if not pm:
        raise NotFound(f"Moderation #{moderation_id} not found")

    if pm.status != "pending":
        raise Conflict("Request is not pending (already processed)")

    reviewer = await _ensure_employee(session, reviewer_id)

    pm.status = "rejected"
    pm.reviewer_employee_id = reviewer.id
    pm.reviewed_at = datetime.now(timezone.utc)
    pm.reject_reason = reason.strip()

    session.add(pm)
    await session.flush()
    return pm
