import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_async_db
from src.provider.client import EventsProviderClient, EventsProviderHTTPError
from src.repositories.events import EventRepository
from src.schemas.events_schemas import (
    EventDetailSchema,
    EventListSchema,
    EventsResponseSchema,
    SeatsResponseSchema,
    TicketCreateRequestSchema,
    TicketCreateResponseSchema,
    TicketDeleteResponseSchema,
)

router = APIRouter()
_seats_cache: dict[str, tuple[datetime, list[str]]] = {}


def _seats_from_provider_payload(data: dict) -> list[str]:
    raw = data.get("seats")
    if raw is None:
        raw = data.get("seat")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return []


def _http_exception_from_provider(exc: EventsProviderHTTPError) -> HTTPException:
    if exc.status_code == 404:
        summary = (
            "Events provider returned 404. "
            "Usually the event is missing upstream "
            "(provider DB reset, wrong API key/environment) or your DB is stale — "
            "run sync again."
        )
        if exc.detail not in (None, "", {}):
            return HTTPException(
                status_code=502,
                detail={"summary": summary, "provider": exc.detail},
            )
        return HTTPException(status_code=502, detail=summary)
    if 400 <= exc.status_code < 500:
        return HTTPException(
            status_code=400,
            detail=exc.detail or "Provider rejected the request",
        )
    return HTTPException(
        status_code=502,
        detail=exc.detail or "Events provider error",
    )


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


@router.get("/api/events/{event_id}/seats", response_model=SeatsResponseSchema)
async def get_event_seats(
    event_id: str,
    session: AsyncSession = Depends(get_async_db),
):
    repo = EventRepository(session=session)
    event = await repo.get_event_by_id(event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != "published":
        raise HTTPException(
            status_code=400, detail="Event is not published for registration"
        )

    cache_key = str(event_id)
    now = datetime.now(timezone.utc)
    cached = _seats_cache.get(cache_key)
    if cached and cached[0] > now:
        seats = cached[1]
    else:
        client = EventsProviderClient(
            base_url=settings.events_provider_url,
            api_key=settings.events_provider_api_key,
        )
        try:
            data = await client.get_seats(event_id=event_id)
        except EventsProviderHTTPError as e:
            raise _http_exception_from_provider(e) from e
        seats = sorted(_seats_from_provider_payload(data))
        _seats_cache[cache_key] = (now + timedelta(seconds=30), seats)

    return SeatsResponseSchema(event_id=event.id, available_seats=seats)


@router.post("/api/tickets", response_model=TicketCreateResponseSchema, status_code=201)
async def create_ticket(
    payload: TicketCreateRequestSchema,
    session: AsyncSession = Depends(get_async_db),
):
    repo = EventRepository(session=session)
    event = await repo.get_event_by_id(event_id=str(payload.event_id))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != "published":
        raise HTTPException(status_code=400, detail="Event is not published")

    client = EventsProviderClient(
        base_url=settings.events_provider_url,
        api_key=settings.events_provider_api_key,
    )
    try:
        ticket_id = await client.register(
            event_id=str(payload.event_id),
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            seat=payload.seat,
        )
    except EventsProviderHTTPError as e:
        raise _http_exception_from_provider(e) from e
    await repo.create_ticket(
        {
            "ticket_id": uuid.UUID(ticket_id),
            "event_id": payload.event_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "email": payload.email,
            "seat": payload.seat,
        }
    )
    await session.commit()
    _seats_cache.pop(str(payload.event_id), None)
    return TicketCreateResponseSchema(ticket_id=uuid.UUID(ticket_id))


@router.delete(
    "/api/tickets/{ticket_id}",
    response_model=TicketDeleteResponseSchema,
    status_code=200,
)
async def delete_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_async_db),
):
    repo = EventRepository(session=session)
    ticket = await repo.get_ticket_by_id(ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    client = EventsProviderClient(
        base_url=settings.events_provider_url,
        api_key=settings.events_provider_api_key,
    )
    try:
        success = await client.unregister(
            event_id=str(ticket.event_id),
            ticket_id=ticket_id,
        )
    except EventsProviderHTTPError as e:
        raise _http_exception_from_provider(e) from e
    if success:
        await repo.delete_ticket_by_id(ticket_id=ticket_id)
        await session.commit()
        _seats_cache.pop(str(ticket.event_id), None)
    return TicketDeleteResponseSchema(success=success)
