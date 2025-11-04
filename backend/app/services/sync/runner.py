# app/services/sync/runner.py
from __future__ import annotations

from typing import Any, List, Dict, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sync import SyncJob, SyncRecord, ExternalEntitySnapshot
from app.models.employee import Employee
from app.services.sync.preprocessor import preprocess_ad_payload
from app.services.sync.normalizer import normalize_employee, NormalizedEmployee
from app.services.sync.repository import (
    get_org_unit_by_name_and_type,
    upsert_employee_core,
    get_employee_by_external_ref,
    get_employee_by_email,  # <- добавили для определения намерения (create|update)
)
from app.schemas.sync import RawEmployeeAD


class SyncSummary(dict):
    def inc(self, key: str, delta: int = 1):
        self[key] = int(self.get(key, 0)) + delta


async def _detect_intended_action(
    session: AsyncSession, *, external_ref: Optional[str], email: str
) -> str:
    """
    Определяем намерение для записи: 'create' или 'update'.
    Нужен, чтобы в случае ошибки корректно писать action при status='error'.
    """
    existing: Optional[Employee] = None
    if external_ref:
        existing = await get_employee_by_external_ref(session, external_ref)
    if existing is None:
        existing = await get_employee_by_email(session, email)
    return "update" if existing else "create"


async def run_employee_sync(
    session: AsyncSession,
    *,
    payload: Any,
    trigger: str = "manual",  # 'manual' | 'scheduled'
) -> Dict[str, int]:
    """
    Главная точка входа: препроцессинг -> нормализация -> снапшоты -> апсерты -> связывание менеджеров -> orphaned -> итог.
    """
    job = SyncJob(
        trigger=trigger,
        status="running",
        started_at=datetime.now(timezone.utc),
        summary=None,
    )
    session.add(job)
    await session.flush()  # получить job.id

    summary = SyncSummary(created=0, updated=0, orphaned=0, errors=0)

    try:
        # 1) препроцессинг (делает RawEmployeeAD[])
        raw_list: List[RawEmployeeAD] = preprocess_ad_payload(payload)

        # 2) нормализация
        norm_list: List[NormalizedEmployee] = [normalize_employee(r) for r in raw_list]

        # 3) снапшоты нормализованных записей
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

        # 4) апсерты сотрудников (без менеджеров), каждую запись — в savepoint
        by_external: Dict[str, int] = {}
        for n in norm_list:
            ou_id: Optional[int] = None
            if n.department:
                dep = await get_org_unit_by_name_and_type(session, name=n.department, unit_type="department")
                if dep:
                    ou_id = dep.id
            if ou_id is None and n.company:
                le = await get_org_unit_by_name_and_type(session, name=n.company, unit_type="legal_entity")
                if le:
                    ou_id = le.id

            # заранее определяем намерение (create|update) для корректного action при ошибке
            intended_action = await _detect_intended_action(
                session,
                external_ref=n.external_ref,
                email=n.email,
            )

            # SAVEPOINT: чтобы ошибка по одной записи не ломала весь джоб
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
                        password_hash=n.password_hash,  # 🆕 добавлено
                    )

                    if created:
                        summary.inc("created")
                        session.add(SyncRecord(
                            job_id=job.id,
                            external_ref=n.external_ref or n.email,
                            action="create",
                            status="applied",
                            decision=None,
                            decided_by_employee_id=None,
                            decided_at=None,
                            message=None,
                        ))
                    elif changed:
                        summary.inc("updated")
                        session.add(SyncRecord(
                            job_id=job.id,
                            external_ref=n.external_ref or n.email,
                            action="update",
                            status="applied",
                            decision=None,
                            decided_by_employee_id=None,
                            decided_at=None,
                            message=None,
                        ))

                    if n.external_ref:
                        by_external[n.external_ref] = emp.id

                except Exception as e:
                    # логируем ошибку на уровне конкретной записи:
                    # action = намерение (create|update), status='error'
                    summary.inc("errors")
                    session.add(SyncRecord(
                        job_id=job.id,
                        external_ref=(n.external_ref or n.email),
                        action=intended_action,  # create | update
                        status="error",          # итог — ошибка
                        decision=None,
                        decided_by_employee_id=None,
                        decided_at=None,
                        message=str(e),
                    ))
            # конец savepoint

        await session.flush()

        # 5) второй проход — проставляем менеджеров по manager_external_ref (с дополнительными защитами)
        for n in norm_list:
            mgr_ext = (n.manager_external_ref or "").strip()
            if not mgr_ext:
                continue

            # кого линкуем (подчинённого) — не дергаем session.get с пустым PK
            subordinate = None
            sub_id = by_external.get(n.external_ref) if n.external_ref else None
            if sub_id:
                # PK гарантированно не None → не будет SAWarning
                subordinate = await session.get(Employee, sub_id)
            elif n.external_ref:
                # осторожно, здесь external_ref может быть пустым — но выше проверили
                subordinate = await get_employee_by_external_ref(session, n.external_ref)

            if not subordinate:
                continue

            # менеджер по external_ref (если пусто — выше бы не зашли)
            manager = await get_employee_by_external_ref(session, mgr_ext)
            if not manager:
                # менеджер пока не существует — слинкуем в одной из следующих синхр
                continue

            if subordinate.manager_id != manager.id:
                subordinate.manager_id = manager.id
                summary.inc("managers_linked")

        # 6) orphaned: локально есть активный сотрудник, но его нет в payload
        incoming_keys = {(x.external_ref or x.email) for x in norm_list if (x.external_ref or x.email)}
        res = await session.execute(select(Employee).where(Employee.status == "active"))
        local_active: list[Employee] = list(res.scalars())

        for emp in local_active:
            key = emp.external_ref or emp.email
            if key and key not in incoming_keys:
                summary.inc("orphaned")
                session.add(SyncRecord(
                    job_id=job.id,
                    external_ref=key,
                    action="archive",
                    status="orphaned",
                    decision=None,
                    decided_by_employee_id=None,
                    decided_at=None,
                    message="Missing in source payload",
                ))

        # 7) финализация
        job.status = "success"
        job.finished_at = datetime.now(timezone.utc)
        job.summary = dict(summary)

        await session.commit()
        return dict(summary)

    except Exception as e:
        # глобальная ошибка джоба — не пишем SyncRecord, только статус и текст в summary
        await session.rollback()
        job.status = "error"
        job.finished_at = datetime.now(timezone.utc)
        summary.inc("errors")
        job.summary = dict(summary) | {"error": str(e)}
        session.add(job)
        await session.commit()
        raise
