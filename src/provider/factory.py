from src.core.config import settings
from src.provider.client import EventsProviderClient


def create_events_provider_client() -> EventsProviderClient:
    return EventsProviderClient(
        base_url=settings.events_provider_url,
        api_key=settings.events_provider_api_key,
    )
