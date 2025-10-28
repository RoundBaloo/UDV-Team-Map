from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee


async def get_all_employees(session: AsyncSession) -> List[Employee]:
    """
    Вернём только активных сотрудников.
    Можно добавить сортировку по фамилии.
    """
    query = (
        select(Employee)
        .where(Employee.status == "active")
        .order_by(Employee.last_name.asc(), Employee.first_name.asc())
    )
    res = await session.execute(query)
    return list(res.scalars().all())


async def get_employee_by_id(
    session: AsyncSession,
    employee_id: int,
) -> Optional[Employee]:
    query = select(Employee).where(Employee.id == employee_id)
    res = await session.execute(query)
    return res.scalar_one_or_none()
