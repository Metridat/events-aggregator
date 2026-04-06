from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.deps import EventsApiContext, get_events_api_context
from src.schemas.events_schemas import (
    EventDetailSchema,
    EventsResponseSchema,
    SeatsResponseSchema,
    TicketCreateRequestSchema,
    TicketCreateResponseSchema,
    TicketDeleteResponseSchema,
)
from src.services.exceptions import EventsServiceError

router = APIRouter()


@router.get("/api/events", response_model=EventsResponseSchema)
async def get_events(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    date_from: str | None = None,
    ctx: EventsApiContext = Depends(get_events_api_context),
):
    try:
        return await ctx.service.list_events(
            ctx.repo,
            page=page,
            page_size=page_size,
            date_from=date_from,
            base_url=str(request.base_url),
        )
    except EventsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/api/events/{event_id}", response_model=EventDetailSchema)
async def get_event(
    event_id: str,
    ctx: EventsApiContext = Depends(get_events_api_context),
):
    try:
        return await ctx.service.get_event_detail(ctx.repo, event_id)
    except EventsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.get("/api/events/{event_id}/seats", response_model=SeatsResponseSchema)
async def get_event_seats(
    event_id: str,
    ctx: EventsApiContext = Depends(get_events_api_context),
):
    try:
        return await ctx.service.get_event_seats(ctx.repo, event_id)
    except EventsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e


@router.post("/api/tickets", response_model=TicketCreateResponseSchema, status_code=201)
async def create_ticket(
    payload: TicketCreateRequestSchema,
    ctx: EventsApiContext = Depends(get_events_api_context),
):
    try:
        result = await ctx.service.create_ticket(ctx.repo, payload)
    except EventsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    await ctx.session.commit()
    return result


@router.delete(
    "/api/tickets/{ticket_id}",
    response_model=TicketDeleteResponseSchema,
    status_code=200,
)
async def delete_ticket(
    ticket_id: str,
    ctx: EventsApiContext = Depends(get_events_api_context),
):
    try:
        result = await ctx.service.delete_ticket(ctx.repo, ticket_id)
    except EventsServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    if result.success:
        await ctx.session.commit()
    return result
