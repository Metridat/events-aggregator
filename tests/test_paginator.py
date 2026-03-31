from unittest.mock import AsyncMock

import pytest

from src.provider.paginator import EventsPaginator


@pytest.mark.asyncio
async def test_paginator():
    page1 = {
        "next": "http://test.com/api/events/?cursor=abc",
        "results": [{"id": "1", "name": "Event 1"}, {"id": "2", "name": "Event 2"}],
    }
    page2 = {"next": None, "results": [{"id": "3", "name": "Event 3"}]}

    mock_client = AsyncMock()
    mock_client.get_events = AsyncMock(side_effect=[page1, page2])

    events = []

    async for event in EventsPaginator(mock_client):
        events.append(event)

    assert len(events) == 3
    assert events[0]["id"] == "1"
    assert events[2]["id"] == "3"
    assert mock_client.get_events.call_count == 2
