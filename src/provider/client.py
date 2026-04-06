from datetime import datetime
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import httpx


def _normalize_changed_at_param(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return "2000-01-01"
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        if len(s) == 10:
            return s
        if len(s) > 10 and s[10] in "T ":
            return s[:10]
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except ValueError:
        return "2000-01-01"


def _sanitize_events_list_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return url
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if "changed_at" not in qs or not qs["changed_at"]:
        return url
    raw = qs["changed_at"][0]
    normalized = _normalize_changed_at_param(raw)
    if raw == normalized:
        return url
    qs["changed_at"] = [normalized]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


class EventsProviderHTTPError(Exception):
    def __init__(
        self, status_code: int, detail: str | dict | list | None = None
    ) -> None:
        self.status_code = status_code
        self.detail = detail


def _raise_provider_status(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail: str | dict | list | None = None
        try:
            detail = e.response.json()
        except ValueError:
            text = e.response.text.strip()
            detail = text or None
        raise EventsProviderHTTPError(e.response.status_code, detail) from e


class EventsProviderClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"x-api-key": api_key}
        self.timeout = 10.0

    def _url(self, path: str) -> str:
        base = self.base_url if self.base_url.endswith("/") else f"{self.base_url}/"
        return urljoin(base, path.lstrip("/"))

    async def get_events(
        self, changed_at: str = "2000-01-01", cursor: str | None = None
    ) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if cursor:
                url = cursor
                params = None
            else:
                url = self._url("api/events/")
                params = {"changed_at": _normalize_changed_at_param(changed_at)}
            response = await client.get(
                url=url, headers=self.headers, params=params, follow_redirects=True
            )
            _raise_provider_status(response)
            return response.json()

    async def get_seats(self, event_id: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url=self._url(f"api/events/{event_id}/seats/"),
                headers=self.headers,
                follow_redirects=True,
            )
            _raise_provider_status(response)
            return response.json()

    async def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url=self._url(f"api/events/{event_id}/register/"),
                headers=self.headers,
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "seat": seat,
                },
                follow_redirects=True,
            )
            _raise_provider_status(response)
            return response.json()["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method="DELETE",
                url=self._url(f"api/events/{event_id}/unregister/"),
                headers=self.headers,
                json={"ticket_id": ticket_id},
                follow_redirects=True,
            )
            _raise_provider_status(response)
            return response.json()["success"]
