from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.models import Event, Place, Ticket


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_place(self, place_data: dict) -> None:
        stmt = insert(Place).values(**place_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=place_data,
        )
        await self.session.execute(stmt)

    async def upsert_event(self, event_data: dict) -> None:
        stmt = insert(Event).values(**event_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=event_data,
        )
        await self.session.execute(stmt)

    async def get_events(
        self,
        page: int = 1,
        page_size: int = 20,
        date_from: str | None = None,
    ) -> tuple[list[Event], int]:
        query = select(Event).options(joinedload(Event.place))
        count_query = select(func.count()).select_from(Event)

        if date_from:
            date_from_dt = datetime.fromisoformat(date_from)
            query = query.where(Event.event_time >= date_from_dt)
            count_query = count_query.where(Event.event_time >= date_from_dt)

        total = await self.session.scalar(count_query) or 0

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        events = list(result.scalars().unique().all())

        return events, total

    async def get_event_by_id(self, event_id: str) -> Event | None:
        result = await self.session.execute(
            select(Event).options(joinedload(Event.place)).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def create_ticket(self, ticket_data: dict) -> None:
        stmt = insert(Ticket).values(**ticket_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticket_id"],
            set_=ticket_data,
        )
        await self.session.execute(stmt)

    async def get_ticket_by_id(self, ticket_id: str) -> Ticket | None:
        result = await self.session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def delete_ticket_by_id(self, ticket_id: str) -> None:
        ticket = await self.get_ticket_by_id(ticket_id=ticket_id)
        if ticket:
            await self.session.delete(ticket)
