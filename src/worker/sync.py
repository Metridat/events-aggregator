import asyncio
import logging
import uuid
from datetime import datetime, timezone

from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.provider.client import EventsProviderClient
from src.provider.paginator import EventsPaginator
from src.repositories.events import EventRepository
from src.repositories.sync_metadata import SyncMetadataRepository

logger = logging.getLogger(__name__)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def changed_at_for_provider(stored: str | None) -> str:
    """Provider expects a date (YYYY-MM-DD), not a full ISO datetime."""
    if not stored:
        return "2000-01-01"
    s = stored.strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except ValueError:
        return "2000-01-01"


_sync_running = False


async def sync_events() -> None:
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
            sync_repo = SyncMetadataRepository(session=session)
            meta = await sync_repo.get_singleton()
            changed_at_param = changed_at_for_provider(meta.last_changed_at)
            meta.sync_status = "running"
            await session.flush()

            repo = EventRepository(session=session)
            max_changed: datetime | None = None

            try:
                async for event in EventsPaginator(
                    client=client, changed_at=changed_at_param
                ):
                    if not event.get("place"):
                        continue
                    place_raw = event["place"]
                    place_data = {
                        **place_raw,
                        "changed_at": parse_datetime(place_raw.get("changed_at")),
                        "created_at": parse_datetime(place_raw.get("created_at")),
                    }

                    await repo.upsert_place(place_data=place_data)

                    event_data = {k: v for k, v in event.items() if k != "place"}
                    event_data["place_id"] = event["place"]["id"]

                    event_data["id"] = uuid.UUID(event_data["id"])
                    event_data["place_id"] = uuid.UUID(event["place"]["id"])

                    event_data["event_time"] = parse_datetime(
                        event_data.get("event_time")
                    )
                    event_data["registration_deadline"] = parse_datetime(
                        event_data.get("registration_deadline")
                    )
                    event_data["changed_at"] = parse_datetime(
                        event_data.get("changed_at")
                    )
                    event_data["created_at"] = parse_datetime(
                        event_data.get("created_at")
                    )
                    event_data["status_changed_at"] = parse_datetime(
                        event_data.get("status_changed_at")
                    )

                    evt_changed = parse_datetime(event.get("changed_at"))
                    if evt_changed and (
                        max_changed is None or evt_changed > max_changed
                    ):
                        max_changed = evt_changed

                    await repo.upsert_event(event_data=event_data)

                meta.last_sync_time = datetime.now(timezone.utc)
                if max_changed is not None:
                    meta.last_changed_at = max_changed.date().isoformat()
                meta.sync_status = "success"
                await session.commit()
                logger.info("Sync complete!")
            except Exception:
                logger.exception("Sync failed")
                await session.rollback()
                try:
                    async with AsyncSessionLocal() as session_failed:
                        sync_failed = SyncMetadataRepository(session=session_failed)
                        meta_failed = await sync_failed.get_singleton()
                        meta_failed.sync_status = "failed"
                        await session_failed.commit()
                except Exception:
                    logger.exception("Could not persist sync failure status")
    finally:
        _sync_running = False


async def sync_worker() -> None:
    while True:
        try:
            await sync_events()
        except Exception:
            logger.exception("Unexpected error in sync worker loop")
        await asyncio.sleep(60 * 60 * 24)
