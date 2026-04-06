import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urljoin

from src.provider.client import EventsProviderClient, EventsProviderHTTPError
from src.repositories.events import EventRepository
from src.schemas.events_schemas import (
    EventListSchema,
    EventsResponseSchema,
    SeatsResponseSchema,
    TicketCreateRequestSchema,
    TicketCreateResponseSchema,
    TicketDeleteResponseSchema,
)
from src.services.exceptions import EventsServiceError


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


def _raise_from_provider(exc: EventsProviderHTTPError) -> None:
    if exc.status_code == 404:
        summary = (
            "Events provider returned 404. "
            "Usually the event is missing upstream "
            "(provider DB reset, wrong API key/environment) or your DB is stale — "
            "run sync again."
        )
        if exc.detail not in (None, "", {}):
            raise EventsServiceError(
                502,
                {"summary": summary, "provider": exc.detail},
            ) from exc
        raise EventsServiceError(502, summary) from exc
    if 400 <= exc.status_code < 500:
        raise EventsServiceError(
            400,
            exc.detail or "Provider rejected the request",
        ) from exc
    raise EventsServiceError(
        502,
        exc.detail or "Events provider error",
    ) from exc


def _build_events_page_url(base_url: str, page: int, page_size: int) -> str:
    path_url = urljoin(base_url, "api/events")
    query = urlencode({"page": page, "page_size": page_size})
    return f"{path_url}?{query}"


class EventsApplicationService:
    def __init__(self, provider: EventsProviderClient) -> None:
        self._provider = provider
        self._seats_cache: dict[str, tuple[datetime, list[str]]] = {}

    async def list_events(
        self,
        repo: EventRepository,
        page: int,
        page_size: int,
        date_from: str | None,
        base_url: str,
    ) -> EventsResponseSchema:
        events, total = await repo.get_events(
            page=page, page_size=page_size, date_from=date_from
        )

        next_url = (
            _build_events_page_url(base_url, page + 1, page_size)
            if page * page_size < total
            else None
        )
        prev_url = (
            _build_events_page_url(base_url, page - 1, page_size) if page > 1 else None
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

    async def get_event_detail(self, repo: EventRepository, event_id: str):
        try:
            uuid.UUID(event_id)
        except ValueError:
            raise EventsServiceError(404, "Event not found") from None

        event = await repo.get_event_by_id(event_id=event_id)
        if not event:
            raise EventsServiceError(404, "Event not found")
        return event

    async def get_event_seats(
        self,
        repo: EventRepository,
        event_id: str,
    ) -> SeatsResponseSchema:
        event = await repo.get_event_by_id(event_id=event_id)
        if not event:
            raise EventsServiceError(404, "Event not found")
        if event.status != "published":
            raise EventsServiceError(
                400,
                "Event is not published for registration",
            )

        cache_key = str(event_id)
        now = datetime.now(timezone.utc)
        cached = self._seats_cache.get(cache_key)
        if cached and cached[0] > now:
            seats = cached[1]
        else:
            try:
                data = await self._provider.get_seats(event_id=event_id)
            except EventsProviderHTTPError as e:
                _raise_from_provider(e)
            seats = sorted(_seats_from_provider_payload(data))
            self._seats_cache[cache_key] = (now + timedelta(seconds=30), seats)

        return SeatsResponseSchema(event_id=event.id, available_seats=seats)

    async def create_ticket(
        self,
        repo: EventRepository,
        payload: TicketCreateRequestSchema,
    ) -> TicketCreateResponseSchema:
        event_uuid = payload.event_id
        event = await repo.get_event_by_id(event_id=str(event_uuid))

        if not event:
            raise EventsServiceError(404, "Event not found")
        if event.status != "published":
            raise EventsServiceError(400, "Event is not published")

        try:
            ticket_id = await self._provider.register(
                event_id=str(payload.event_id),
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                seat=payload.seat,
            )
        except EventsProviderHTTPError as e:
            _raise_from_provider(e)

        await repo.create_ticket(
            {
                "ticket_id": uuid.UUID(ticket_id),
                "event_id": event_uuid,
                "first_name": payload.first_name,
                "last_name": payload.last_name,
                "email": payload.email,
                "seat": payload.seat,
            }
        )
        await repo.commit()
        self._seats_cache.pop(str(payload.event_id), None)
        return TicketCreateResponseSchema(ticket_id=uuid.UUID(ticket_id))

    async def delete_ticket(
        self,
        repo: EventRepository,
        ticket_id: str,
    ) -> TicketDeleteResponseSchema:
        ticket = await repo.get_ticket_by_id(ticket_id=ticket_id)
        if not ticket:
            raise EventsServiceError(404, "Ticket not found")

        try:
            success = await self._provider.unregister(
                event_id=str(ticket.event_id),
                ticket_id=ticket_id,
            )
        except EventsProviderHTTPError as e:
            _raise_from_provider(e)

        if success:
            await repo.delete_ticket_by_id(ticket_id=ticket_id)
            await repo.commit()
            self._seats_cache.pop(str(ticket.event_id), None)
        return TicketDeleteResponseSchema(success=success)
