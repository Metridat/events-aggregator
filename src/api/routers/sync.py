import asyncio

from fastapi import APIRouter

from src.worker.sync import sync_events

router = APIRouter()


@router.post("/api/sync/trigger")
async def trigger_sync():
    asyncio.create_task(sync_events())
    return {"status": "ok"}
