from src.provider.client import EventsProviderClient


class EventsPaginator:
    def __init__(self, client: EventsProviderClient, changed_at: str = "2000-01-01"):
        self.client = client
        self.changed_at = changed_at

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        cursor = None
        while True:
            response = await self.client.get_events(
                changed_at=self.changed_at, cursor=cursor
            )
            for event in response["results"]:
                yield event

            cursor = response["next"]
            if cursor is None:
                break
