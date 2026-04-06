from dataclasses import dataclass
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_db
from src.provider.client import EventsProviderClient
from src.provider.factory import create_events_provider_client
from src.repositories.events import EventRepository
from src.services.events_service import EventsApplicationService


@lru_cache
def get_events_provider_client() -> EventsProviderClient:
    return create_events_provider_client()


@lru_cache
def get_events_application_service() -> EventsApplicationService:
    return EventsApplicationService(get_events_provider_client())


@dataclass(slots=True)
class EventsApiContext:
    service: EventsApplicationService
    repo: EventRepository
    session: AsyncSession


def get_events_api_context(
    session: AsyncSession = Depends(get_async_db),
    service: EventsApplicationService = Depends(get_events_application_service),
) -> EventsApiContext:
    return EventsApiContext(
        service=service,
        repo=EventRepository(session=session),
        session=session,
    )
