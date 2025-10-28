import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.employee import Employee
from app.models.team import Team
from app.models.sync import SyncJob, SyncRecord

async def main():
    async with AsyncSessionLocal() as session:

        print("\n=== Employees ===")
        res_emp = await session.execute(
            select(Employee.id,
                   Employee.external_ref,
                   Employee.first_name,
                   Employee.last_name,
                   Employee.title,
                   Employee.status,
                   Employee.manager_id,
                   Employee.primary_org_unit_id)
        )
        for row in res_emp.all():
            print(row)

        print("\n=== Teams ===")
        res_team = await session.execute(
            select(Team.id,
                   Team.external_ref,
                   Team.name,
                   Team.org_unit_id,
                   Team.lead_id)
        )
        for row in res_team.all():
            print(row)

        print("\n=== Sync jobs ===")
        res_job = await session.execute(
            select(SyncJob.id,
                   SyncJob.status,
                   SyncJob.trigger,
                   SyncJob.started_at,
                   SyncJob.summary)
            .order_by(SyncJob.id)
        )
        for row in res_job.all():
            print(row)

        print("\n=== Sync records (last job) ===")
        # возьмём самый свежий job.id
        last_job_id_row = await session.execute(
            select(SyncJob.id).order_by(SyncJob.id.desc()).limit(1)
        )
        last_job_id = last_job_id_row.scalar_one()
        print(f"last_job_id = {last_job_id}")

        res_records = await session.execute(
            select(SyncRecord.id,
                   SyncRecord.entity_type,
                   SyncRecord.external_ref,
                   SyncRecord.action,
                   SyncRecord.status,
                   SyncRecord.message)
            .where(SyncRecord.job_id == last_job_id)
        )
        for row in res_records.all():
            print(row)

asyncio.run(main())
