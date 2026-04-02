import asyncio
import logging
import uuid
from datetime import datetime

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.provider.client import EventsProviderClient
from src.provider.paginator import EventsPaginator
from src.repositories.events import EventRepository

logger = logging.getLogger(__name__)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


_sync_running = False


async def sync_events():

    client = EventsProviderClient(
        base_url=settings.events_provider_url,
        api_key=settings.events_provider_api_key,
    )
    global _sync_running
    if _sync_running:
        logger.info("Sync already running, skipping...")
        return
    _sync_running = True
    try:
        logger.info("Starting sync...")

        async with AsyncSessionLocal() as session:
            session.autoflush = False
            repo = EventRepository(session=session)

            async for event in EventsPaginator(client=client):
                if not event.get("place"):
                    continue
                place_data = event["place"]

                place_data["changed_at"] = parse_datetime(place_data.get("changed_at"))
                place_data["created_at"] = parse_datetime(place_data.get("created_at"))

                await repo.upsert_place(place_data=place_data)

                event_data = {k: v for k, v in event.items() if k != "place"}
                event_data["place_id"] = event["place"]["id"]

                event_data["id"] = uuid.UUID(event_data["id"])
                event_data["place_id"] = uuid.UUID(event["place"]["id"])

                event_data["event_time"] = parse_datetime(event_data.get("event_time"))
                event_data["registration_deadline"] = parse_datetime(
                    event_data.get("registration_deadline")
                )
                event_data["changed_at"] = parse_datetime(event_data.get("changed_at"))
                event_data["created_at"] = parse_datetime(event_data.get("created_at"))
                event_data["status_changed_at"] = parse_datetime(
                    event_data.get("status_changed_at")
                )

                await repo.upsert_event(event_data=event_data)

            await session.commit()
            logger.info("Sync complete!")

    finally:
        _sync_running = False


async def sync_worker():
    while True:
        await asyncio.sleep(60 * 60 * 24)
        try:
            await sync_events()
        except Exception as e:
            logger.error(f"Sync failed: {e}")
