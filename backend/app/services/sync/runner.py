from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.sync import ExternalEntitySnapshot, SyncJob, SyncRecord
from app.schemas.sync import RawEmployeeAD
from app.services.sync.normalizer import NormalizedEmployee, normalize_employee
from app.services.sync.preprocessor import preprocess_ad_payload
from app.services.sync.repository import (
    get_employee_by_email,
    get_employee_by_external_ref,
    get_org_unit_by_name_and_type,
    upsert_employee_core,
)


class SyncSummary(dict):
    """Счётчик агрегированных метрик синхронизации."""

    def inc(self, key: str, delta: int = 1) -> None:
        self[key] = int(self.get(key, 0)) + delta


class OrphanedPendingError(Exception):
    """Есть нерешенные orphaned-сотрудники, синхронизацию запускать нельзя."""


async def _has_unresolved_orphaned(session: AsyncSession) -> bool:
    """Проверяет наличие строк orphaned без decision в sync_record."""
    res = await session.execute(
        select(SyncRecord.id)
        .where(
            SyncRecord.status == "orphaned",
            SyncRecord.decision.is_(None),
        )
        .limit(1),
    )
    return res.scalar_one_or_none() is not None


async def _detect_intended_action(
    session: AsyncSession,
    *,
    external_ref: str | None,
    email: str,
) -> str:
    """Определяет предполагаемое действие для записи: create или update."""
    existing: Employee | None = None
    if external_ref:
        existing = await get_employee_by_external_ref(session, external_ref)
    if existing is None:
        existing = await get_employee_by_email(session, email)
    return "update" if existing else "create"


async def run_employee_sync(
    session: AsyncSession,
    *,
    payload: Any,
    trigger: str = "manual",
) -> dict[str, int]:
    """Запускает полную синхронизацию сотрудников из AD.

    Перед запуском проверяет наличие нерешенных orphaned-записей и
    при их наличии выбрасывает OrphanedPendingError.
    """
    if await _has_unresolved_orphaned(session):
        raise OrphanedPendingError(
            "Cannot start sync while there are orphaned employees without decision.",
        )

    job = SyncJob(
        trigger=trigger,
        status="running",
        started_at=datetime.now(timezone.utc),
        summary=None,
    )
    session.add(job)
    await session.flush()

    summary = SyncSummary(created=0, updated=0, orphaned=0, errors=0)

    try:
        raw_list: list[RawEmployeeAD] = preprocess_ad_payload(payload)
        norm_list: list[NormalizedEmployee] = [
            normalize_employee(r) for r in raw_list
        ]

        for n in norm_list:
            snapshot = ExternalEntitySnapshot(
                external_ref=n.external_ref or n.email,
                job_id=job.id,
                payload=n.__dict__,
                normalized=n.__dict__,
                received_at=datetime.now(timezone.utc),
            )
            session.add(snapshot)
        await session.flush()

        by_external: dict[str, int] = {}

        for n in norm_list:
            ou_id: int | None = None
            if n.department:
                dep = await get_org_unit_by_name_and_type(
                    session,
                    name=n.department,
                    unit_type="department",
                )
                if dep:
                    ou_id = dep.id
            if ou_id is None and n.company:
                le = await get_org_unit_by_name_and_type(
                    session,
                    name=n.company,
                    unit_type="legal_entity",
                )
                if le:
                    ou_id = le.id

            intended_action = await _detect_intended_action(
                session,
                external_ref=n.external_ref,
                email=n.email,
            )

            async with session.begin_nested():
                try:
                    emp, created, changed = await upsert_employee_core(
                        session,
                        external_ref=n.external_ref,
                        email=n.email,
                        first_name=n.first_name,
                        middle_name=n.middle_name,
                        last_name=n.last_name,
                        title=n.title,
                        bio=None,
                        skill_ratings=None,
                        lowest_org_unit_id=ou_id,
                        password_hash=n.password_hash,
                    )

                    if created:
                        summary.inc("created")
                        session.add(
                            SyncRecord(
                                job_id=job.id,
                                external_ref=n.external_ref or n.email,
                                action="create",
                                status="applied",
                                decision=None,
                                decided_by_employee_id=None,
                                decided_at=None,
                                message=None,
                            ),
                        )
                    elif changed:
                        summary.inc("updated")
                        session.add(
                            SyncRecord(
                                job_id=job.id,
                                external_ref=n.external_ref or n.email,
                                action="update",
                                status="applied",
                                decision=None,
                                decided_by_employee_id=None,
                                decided_at=None,
                                message=None,
                            ),
                        )

                    if n.external_ref:
                        by_external[n.external_ref] = emp.id

                except Exception as exc:
                    summary.inc("errors")
                    session.add(
                        SyncRecord(
                            job_id=job.id,
                            external_ref=n.external_ref or n.email,
                            action=intended_action,
                            status="error",
                            decision=None,
                            decided_by_employee_id=None,
                            decided_at=None,
                            message=str(exc),
                        ),
                    )

        await session.flush()

        for n in norm_list:
            mgr_ext = (n.manager_external_ref or "").strip()
            if not mgr_ext:
                continue

            subordinate: Employee | None = None
            sub_id = by_external.get(n.external_ref) if n.external_ref else None
            if sub_id:
                subordinate = await session.get(Employee, sub_id)
            elif n.external_ref:
                subordinate = await get_employee_by_external_ref(
                    session,
                    n.external_ref,
                )

            if not subordinate:
                continue

            manager = await get_employee_by_external_ref(session, mgr_ext)
            if not manager:
                continue

            if subordinate.manager_id != manager.id:
                subordinate.manager_id = manager.id
                summary.inc("managers_linked")

        incoming_keys = {
            x.external_ref or x.email
            for x in norm_list
            if (x.external_ref or x.email)
        }
        res = await session.execute(
            select(Employee).where(Employee.status == "active"),
        )
        local_active: list[Employee] = list(res.scalars())

        for emp in local_active:
            key = emp.external_ref or emp.email
            if key and key not in incoming_keys:
                summary.inc("orphaned")
                session.add(
                    SyncRecord(
                        job_id=job.id,
                        external_ref=key,
                        action="archive",
                        status="orphaned",
                        decision=None,
                        decided_by_employee_id=None,
                        decided_at=None,
                        message="Missing in source payload",
                    ),
                )

        job.status = "success"
        job.finished_at = datetime.now(timezone.utc)
        job.summary = dict(summary)

        await session.commit()
        return dict(summary)

    except Exception as exc:
        await session.rollback()
        job.status = "error"
        job.finished_at = datetime.now(timezone.utc)
        summary.inc("errors")
        job.summary = dict(summary) | {"error": str(exc)}
        session.add(job)
        await session.commit()
        raise
