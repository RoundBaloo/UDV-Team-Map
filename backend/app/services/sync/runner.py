from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.sync import SyncJob, SyncRecord
from app.schemas.sync import SyncEmployeePayload
from app.services.sync.preprocessor import load_sync_payload
from app.services.sync.repository import (
    get_employee_by_email,
    get_employee_by_external_ref,
    resolve_department_id_for_sync,
    upsert_employee_core,
)


class SyncSummary(dict):
    """Счётчик агрегированных метрик синхронизации."""

    def inc(self, key: str, delta: int = 1) -> None:
        """Увеличивает указанную метрику на delta."""
        self[key] = int(self.get(key, 0)) + delta


async def _detect_intended_action(
    session: AsyncSession,
    *,
    external_ref: str | None,
    email: str,
) -> str:
    """Определяет предполагаемое действие: create или update."""
    existing: Employee | None = None
    if external_ref:
        existing = await get_employee_by_external_ref(session, external_ref)
    if existing is None:
        existing = await get_employee_by_email(session, email)
    return "update" if existing else "create"


def _calc_is_blocked_from_sync(payload: SyncEmployeePayload) -> bool | None:
    """Определяет блокировку сотрудника по данным синхронизации."""
    if payload.is_in_blocked_ou is True:
        return True
    if payload.is_blocked_from_ad is True:
        return True
    return None


def _calc_status_from_sync(payload: SyncEmployeePayload) -> str | None:
    """Определяет статус сотрудника по данным синхронизации."""
    if payload.is_in_blocked_ou is True:
        return "dismissed"
    return None


async def run_employee_sync(
    session: AsyncSession,
    *,
    trigger: str = "manual",
) -> dict[str, int]:
    """Запускает полную синхронизацию сотрудников из AD.

    Источник данных определяется в load_sync_payload(), который:
    * в dev-режиме читает тестовый JSON-файл;
    * в бою обращается к интеграции с AD.
    """
    job = SyncJob(
        trigger=trigger,
        status="running",
        started_at=datetime.now(timezone.utc),
        summary=None,
    )
    session.add(job)
    await session.flush()

    summary = SyncSummary(created=0, updated=0, archived=0, errors=0)

    try:
        raw_items: list[SyncEmployeePayload] = await load_sync_payload()
        by_external: dict[str, int] = {}

        for item in raw_items:
            intended_action = await _detect_intended_action(
                session,
                external_ref=item.external_ref,
                email=item.email,
            )

            # company / department обязательны
            if not item.company or not item.department:
                summary.inc("errors")
                session.add(
                    SyncRecord(
                        job_id=job.id,
                        external_ref=item.external_ref or item.email,
                        action=intended_action,
                        status="error",
                        error_code="ORG_UNIT_MISSING",
                        message="Missing company or department in sync payload",
                    ),
                )
                continue

            department_id: int | None = await resolve_department_id_for_sync(
                session,
                company=item.company,
                department=item.department,
            )

            if department_id is None:
                summary.inc("errors")
                session.add(
                    SyncRecord(
                        job_id=job.id,
                        external_ref=item.external_ref or item.email,
                        action=intended_action,
                        status="error",
                        error_code="ORG_UNIT_NOT_FOUND",
                        message=(
                            "Org unit not found for "
                            f"company='{item.company}', "
                            f"department='{item.department}'"
                        ),
                    ),
                )
                continue

            is_blocked_from_sync = _calc_is_blocked_from_sync(item)
            status_from_sync = _calc_status_from_sync(item)

            async with session.begin_nested():
                try:
                    (
                        emp,
                        created,
                        changed,
                        dismissed_now,
                    ) = await upsert_employee_core(
                        session,
                        external_ref=item.external_ref,
                        email=item.email,
                        first_name=item.first_name,
                        middle_name=item.middle_name,
                        last_name=item.last_name,
                        title=item.title,
                        department_id=department_id,
                        password_hash=item.password_hash,
                        is_blocked_from_sync=is_blocked_from_sync,
                        status_from_sync=status_from_sync,
                    )

                    action: str | None = None
                    if created:
                        action = "create"
                        summary.inc("created")
                    elif dismissed_now:
                        action = "archive"
                        summary.inc("archived")
                    elif changed:
                        action = "update"
                        summary.inc("updated")

                    if action is not None:
                        session.add(
                            SyncRecord(
                                job_id=job.id,
                                external_ref=item.external_ref or item.email,
                                action=action,
                                status="applied",
                                error_code=None,
                                message=None,
                            ),
                        )

                    if item.external_ref:
                        by_external[item.external_ref] = emp.id

                except Exception as exc:
                    summary.inc("errors")

                    error_action = (
                        "archive" if item.is_in_blocked_ou is True else intended_action
                    )

                    session.add(
                        SyncRecord(
                            job_id=job.id,
                            external_ref=item.external_ref or item.email,
                            action=error_action,
                            status="error",
                            error_code="APPLY_ERROR",
                            message=str(exc),
                        ),
                    )

        await session.flush()

        # Вторая фаза — проставляем менеджеров по manager_external_ref
        for item in raw_items:
            mgr_ext = (item.manager_external_ref or "").strip()
            if not mgr_ext:
                continue

            subordinate_id = (
                by_external.get(item.external_ref) if item.external_ref else None
            )
            if subordinate_id:
                subordinate = await session.get(Employee, subordinate_id)
            elif item.external_ref:
                subordinate = await get_employee_by_external_ref(
                    session,
                    item.external_ref,
                )
            else:
                subordinate = None

            if not subordinate:
                continue

            manager = await get_employee_by_external_ref(session, mgr_ext)
            if not manager:
                continue

            if subordinate.manager_id != manager.id:
                subordinate.manager_id = manager.id

        errors = summary.get("errors", 0)
        successes = (
            summary.get("created", 0)
            + summary.get("updated", 0)
            + summary.get("archived", 0)
        )

        if errors > 0 and successes > 0:
            job.status = "partial"
        elif errors > 0 and successes == 0:
            job.status = "error"
        else:
            job.status = "success"

        job.finished_at = datetime.now(timezone.utc)
        job.summary = dict(summary)

        await session.commit()
        return dict(summary)

    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        job.status = "error"
        job.finished_at = datetime.now(timezone.utc)
        summary.inc("errors")
        job.summary = dict(summary) | {"error": str(exc)}
        session.add(job)
        await session.commit()
        raise
