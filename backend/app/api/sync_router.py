from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path as PathParam,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user
from app.db.session import get_async_session
from app.models.employee import Employee
from app.models.sync import SyncJob, SyncRecord
from app.schemas.common import ErrorCode, ErrorResponse
from app.schemas.sync import (
    SyncJobDetail,
    SyncJobListItem,
    SyncJobRunResponse,
    SyncJobSummary,
    SyncRecordItem,
)
from app.services.sync.runner import run_employee_sync

router = APIRouter(
    prefix="/sync",
    tags=["Sync"],
    dependencies=[Depends(get_current_user)],
)


def _ensure_admin(user: Employee) -> None:
    """Проверяет, что запрос делает администратор."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse.single(
                code=ErrorCode.AUTH_FORBIDDEN,
                message="Требуются права администратора",
                status=403,
            ).model_dump(),
        )


@router.post(
    "/jobs/run",
    response_model=SyncJobRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_sync_job(
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> SyncJobRunResponse:
    """Запускает синхронизацию сотрудников из внешнего источника.

    Источник данных определяется реализацией сервиса синхронизации.
    """
    _ensure_admin(current_user)

    try:
        summary_dict = await run_employee_sync(
            session,
            trigger="manual",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Не удалось запустить синхронизацию: {exc}",
                status=500,
            ).model_dump(),
        ) from exc

    res = await session.execute(
        select(SyncJob).order_by(SyncJob.started_at.desc()).limit(1),
    )
    job = res.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse.single(
                code=ErrorCode.INTERNAL_ERROR,
                message="Синхронизация завершилась, но запись SyncJob не найдена.",
                status=500,
            ).model_dump(),
        )

    summary = SyncJobSummary(**(summary_dict or {}))

    return SyncJobRunResponse(
        job_id=job.id,
        status=job.status,
        summary=summary,
    )


@router.get("/jobs", response_model=list[SyncJobListItem])
async def list_sync_jobs(
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Максимальное количество запусков в списке.",
    ),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> list[SyncJobListItem]:
    """Возвращает список последних запусков синхронизации."""
    _ensure_admin(current_user)

    res = await session.execute(
        select(SyncJob)
        .order_by(SyncJob.started_at.desc())
        .limit(limit),
    )
    jobs = list(res.scalars().all())

    items: list[SyncJobListItem] = []
    for job in jobs:
        started_date = job.started_at.date()
        finished_date = job.finished_at.date() if job.finished_at else None
        summary = SyncJobSummary(**(job.summary or {}))

        items.append(
            SyncJobListItem(
                id=job.id,
                trigger=job.trigger,
                status=job.status,
                started_date=started_date,
                finished_date=finished_date,
                summary=summary,
            ),
        )

    return items


@router.get("/jobs/{job_id}", response_model=SyncJobDetail)
async def get_sync_job_detail(
    job_id: int = PathParam(..., gt=0),
    action: str | None = Query(
        default=None,
        description="Фильтр по действию: create / update / archive",
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Фильтр по статусу записи: applied / error",
    ),
    session: AsyncSession = Depends(get_async_session),
    current_user: Employee = Depends(get_current_user),
) -> SyncJobDetail:
    """Возвращает детали запуска синхронизации и журнал записей."""
    _ensure_admin(current_user)

    job = (
        await session.execute(
            select(SyncJob)
            .where(SyncJob.id == job_id)
            .options(selectinload(SyncJob.records)),
        )
    ).scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse.single(
                code=ErrorCode.NOT_FOUND,
                message="Запуск синхронизации не найден",
                status=404,
            ).model_dump(),
        )

    records: list[SyncRecord] = list(job.records)

    if action:
        records = [r for r in records if r.action == action]

    if status_filter:
        records = [r for r in records if r.status == status_filter]

    started_date = job.started_at.date()
    finished_date = job.finished_at.date() if job.finished_at else None
    summary = SyncJobSummary(**(job.summary or {}))

    record_items = [
        SyncRecordItem(
            id=r.id,
            external_ref=r.external_ref,
            action=r.action,
            status=r.status,
            error_code=r.error_code,
            message=r.message,
        )
        for r in records
    ]

    return SyncJobDetail(
        id=job.id,
        trigger=job.trigger,
        status=job.status,
        started_date=started_date,
        finished_date=finished_date,
        summary=summary,
        records=record_items,
    )
