from __future__ import annotations

from datetime import datetime
from typing import Literal, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.sync import SyncJob
from app.providers.base_ad_provider import BaseADProvider
from app.services.sync_utils import (
    upsert_org_units,
    upsert_teams,
    upsert_employees_first_pass,
    apply_org_unit_managers,
    apply_team_leads,
    apply_team_org_units,
    apply_employee_managers_and_org_units,
    apply_employee_team_memberships,
    detect_orphaned_entities,
)
from app.utils.logger import logger


async def run_sync(
    session: AsyncSession,
    provider: BaseADProvider,
    trigger: Literal["manual", "scheduled"] = "manual",
) -> Dict[str, Any]:
    """
    Главная точка синхронизации структуры:
    - создаёт SyncJob
    - получает данные из провайдера (JSON/AD и т.д.)
    - апсерты org_unit / team / employee
    - второй проход для связей (менеджеры, лиды, участие)
    - фиксация orphaned
    - финальный статус и сводка
    """

    logger.info("🔁 Запуск синхронизации (trigger=%s)", trigger)
    job = SyncJob(
        trigger=trigger,
        status="running",
        started_at=datetime.utcnow(),
    )
    session.add(job)
    await session.flush()

    try:
        # --- 1. Загрузка данных из провайдера ---
        payload = provider.load()
        logger.info(
            "Источник данных загружен: %s org_units, %s teams, %s employees",
            len(payload.get("org_units", [])),
            len(payload.get("teams", [])),
            len(payload.get("employees", [])),
        )

        # --- 2. OrgUnits ---
        ou_stats = await upsert_org_units(session, job.id, payload.get("org_units", []))

        # --- 3. Teams ---
        team_stats = await upsert_teams(session, job.id, payload.get("teams", []))

        # --- 4. Employees (первый проход) ---
        emp_stats_first = await upsert_employees_first_pass(
            session, job.id, payload.get("employees", [])
        )

        # --- 5. Применяем связи (второй проход) ---
        await session.flush()

        await apply_org_unit_managers(
            session=session,
            job_id=job.id,
            data=payload.get("org_units", []),
        )
        await apply_team_leads(
            session=session,
            job_id=job.id,
            data=payload.get("teams", []),
        )
        await apply_team_org_units(
            session=session,
            job_id=job.id,
            data=payload.get("teams", [])
        )
        await apply_employee_managers_and_org_units(
            session=session,
            job_id=job.id,
            data=payload.get("employees", []),
        )
        await apply_employee_team_memberships(
            session=session,
            job_id=job.id,
            data=payload.get("employees", []),
        )

        # --- 6. Orphaned ---
        # сравниваем с payload, а не с SyncRecord(applied)!
        orphaned_stats = await detect_orphaned_entities(
            session,
            job,
            org_units_payload=payload.get("org_units", []),
            teams_payload=payload.get("teams", []),
            employees_payload=payload.get("employees", []),
        )

        # --- 7. Финализируем SyncJob ---
        job.finished_at = datetime.utcnow()
        job.status = "success"
        job.summary = {
            "org_units": ou_stats,
            "teams": team_stats,
            "employees": emp_stats_first,
            "orphaned": orphaned_stats,
        }

        await session.commit()
        logger.info("✅ Синхронизация завершена успешно")
        return job.summary

    except Exception as e:
        await session.rollback()
        job.status = "error"
        job.finished_at = datetime.utcnow()
        await session.commit()
        logger.exception("❌ Ошибка синхронизации: %s", e)
        return {"error": str(e)}
