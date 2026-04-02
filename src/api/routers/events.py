import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.repositories.events import EventRepository
from src.schemas.events_schemas import (
    EventDetailSchema,
    EventListSchema,
    EventsResponseSchema,
)

router = APIRouter()


@router.get("/api/events", response_model=EventsResponseSchema)
async def get_events(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    date_from: str | None = None,
    session: AsyncSession = Depends(get_async_db),
):
    repo = EventRepository(session=session)
    events, total = await repo.get_events(
        page=page, page_size=page_size, date_from=date_from
    )

    base_url = str(request.base_url)
    next_url = (
        f"{base_url}api/events?page={page + 1}&page_size={page_size}"
        if page * page_size < total
        else None
    )
    prev_url = (
        f"{base_url}api/events?page={page - 1}&page_size={page_size}"
        if page > 1
        else None
    )

    results = []
    for e in events:
        if not e.place:
            continue
        results.append(EventListSchema.model_validate(e))

    return EventsResponseSchema(
        count=total,
        next=next_url,
        previous=prev_url,
        results=results,
    )


@router.get("/api/events/{event_id}", response_model=EventDetailSchema)
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_async_db),
):
    try:
        uuid.UUID(event_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Event not found")

    repo = EventRepository(session=session)
    event = await repo.get_event_by_id(event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
