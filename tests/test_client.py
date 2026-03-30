from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.provider.client import EventsProviderClient


@pytest.mark.asyncio
async def test_get_events():
    client = EventsProviderClient(base_url="http://test.com", api_key="test_key")

    fake_response = {
        "next": "http://...api/events?changed_at=2026-01-01&cursor=xyz",
        "previous": None,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Конференция по Python",
                "place": {
                    "id": "650e8400-e29b-41d4-a716-446655440001",
                    "name": "Конференц-зал Технопарк",
                    "city": "Москва",
                    "address": "ул. Ленина, д. 1",
                    "seats_pattern": "A1-1000,B1-2000",
                    "changed_at": "2025-01-01T03:00:00+03:00",
                    "created_at": "2025-01-01T03:00:00+03:00",
                },
                "event_time": "2026-01-11T17:00:00+03:00",
                "registration_deadline": "2026-01-10T17:00:00+03:00",
                "status": "published",
                "number_of_visitors": 5,
                "changed_at": "2026-01-04T22:28:35.325270+03:00",
                "created_at": "2026-01-04T22:28:35.325302+03:00",
                "status_changed_at": "2026-01-04T22:28:35.325386+03:00",
            }
        ],
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = MagicMock(return_value=fake_response)
        mock_get.return_value.raise_for_status = MagicMock()

        result = await client.get_events()

    assert result == fake_response
    assert mock_get.called


@pytest.mark.asyncio
async def test_get_seats():
    client = EventsProviderClient(base_url="http://test.com", api_key="test_key")

    fake_response = {"seat": "A15"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.json = MagicMock(return_value=fake_response)
        mock_get.return_value.raise_for_status = MagicMock()

        result = await client.get_seats(event_id="550e8400-e29b-41d4-a716-446655440000")

    assert result == fake_response
    assert mock_get.called


@pytest.mark.asyncio
async def test_register():
    client = EventsProviderClient(base_url="http://test.com", api_key="test_key")

    fake_response = {"ticket_id": "1fed0122-b675-42e2-8ae7-49bfb53e8d7f"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json = MagicMock(return_value=fake_response)
        mock_post.return_value.raise_for_status = MagicMock()

        result = await client.register(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            first_name="Иван",
            last_name="Иванов",
            email="ivan@example.com",
            seat="A15",
        )

    assert result == "1fed0122-b675-42e2-8ae7-49bfb53e8d7f"
    assert mock_post.called


@pytest.mark.asyncio
async def test_unregister():
    client = EventsProviderClient(base_url="http://test.com", api_key="test_key")

    fake_response = {"success": True}

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value.json = MagicMock(return_value=fake_response)
        mock_request.return_value.raise_for_status = MagicMock()

        result = await client.unregister(
            event_id="550e8400-e29b-41d4-a716-446655440000",
            ticket_id="1fed0122-b675-42e2-8ae7-49bfb53e8d7f",
        )

    assert result
    assert mock_request.called
