import httpx


class EventsProviderClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}

    async def get_events(
        self, changed_at: str = "2000-01-01", cursor: str | None = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            if cursor:
                url = cursor
                params = {}
            else:
                url = f"{self.base_url}/api/events/"
                params = {"changed_at": changed_at}
            response = await client.get(url=url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_seats(self, event_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{self.base_url}/api/events/{event_id}/seats/",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f"{self.base_url}/api/events/{event_id}/register/",
                headers=self.headers,
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "seat": seat,
                },
            )
            response.raise_for_status()
            return response.json()["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method="DELETE",
                url=f"{self.base_url}/api/events/{event_id}/unregister/",
                headers=self.headers,
                json={"ticket_id": ticket_id},
            )
            response.raise_for_status()
            return response.json()["success"]
