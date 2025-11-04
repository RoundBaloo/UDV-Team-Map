# scripts/print_sync_state.py
from __future__ import annotations

import asyncio
from typing import Dict, Optional, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.employee import Employee
from app.models.org_unit import OrgUnit
from app.models.sync import SyncJob, SyncRecord


def _h2(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("-" * 80)


async def _map_external_ref_to_emp_id(session: AsyncSession, external_refs: Iterable[Optional[str]]) -> Dict[str, int]:
    """Строит мапу external_ref/email -> employee.id, чтобы красиво печатать SyncRecord."""
    keys = {k for k in external_refs if k}
    if not keys:
        return {}

    # 1) по external_ref
    res1 = await session.execute(
        select(Employee.external_ref, Employee.id).where(Employee.external_ref.in_(keys))
    )
    by_ext = {ext: emp_id for ext, emp_id in res1.all() if ext}

    # 2) по email (если external_ref на самом деле email)
    left = keys - set(by_ext.keys())
    if left:
        res2 = await session.execute(
            select(Employee.email, Employee.id).where(Employee.email.in_(left))
        )
        by_email = {email: emp_id for email, emp_id in res2.all() if email}
        by_ext.update(by_email)

    return by_ext


async def print_employees(session: AsyncSession) -> None:
    _h2("EMPLOYEES")
    res = await session.execute(select(Employee).order_by(Employee.id.asc()))
    rows = res.scalars().all()
    if not rows:
        print("(empty)")
        return

    for e in rows:
        name = " ".join(x for x in [e.last_name, e.first_name, e.middle_name] if x)
        print(
            f"[id={e.id}] ext= {e.external_ref or ''} | email={e.email} | "
            f"name={name} | title={e.title} | mgr_id={e.manager_id} | "
            f"ou_id={e.lowest_org_unit_id} | created={e.created_at} | updated={e.updated_at}"
        )


async def print_org_units(session: AsyncSession) -> None:
    _h2("ORG_UNITS")
    res = await session.execute(select(OrgUnit).order_by(OrgUnit.id.asc()))
    rows = res.scalars().all()
    if not rows:
        print("(empty)")
        return

    for u in rows:
        print(
            f"[id={u.id}] type={u.unit_type} | name={u.name} | parent_id={u.parent_id} | "
            f"archived={u.is_archived} | created={u.created_at} | updated={u.updated_at}"
        )


async def print_sync_jobs(session: AsyncSession) -> None:
    _h2("SYNC_JOB")
    res = await session.execute(select(SyncJob).order_by(SyncJob.id.desc()))
    rows = res.scalars().all()
    if not rows:
        print("(empty)")
        return

    for j in rows:
        print(
            f"[id={j.id}] trigger={j.trigger} | status={j.status} | "
            f"started={j.started_at} | finished={j.finished_at} | summary={j.summary}"
        )


async def print_sync_records(session: AsyncSession) -> None:
    _h2("SYNC_RECORD")
    res = await session.execute(select(SyncRecord).order_by(SyncRecord.id.desc()))
    rows = res.scalars().all()
    if not rows:
        print("(empty)")
        return

    # Построим мапу external_ref/email -> employee.id, чтобы печатать “local_emp_id”
    ext_map = await _map_external_ref_to_emp_id(session, (r.external_ref for r in rows))

    for r in rows:
        local_emp_id = ext_map.get(r.external_ref or "", None)
        print(
            f"[id={r.id}] job_id={r.job_id} | action={r.action} | status={r.status} | "
            f"external_ref={r.external_ref} | local_emp_id={local_emp_id} | "
            f"msg={r.message} | created_at={r.created_at}"
        )


async def main() -> None:
    async with async_session_maker() as session:
        await print_employees(session)
        await print_org_units(session)
        await print_sync_jobs(session)
        await print_sync_records(session)


if __name__ == "__main__":
    asyncio.run(main())
