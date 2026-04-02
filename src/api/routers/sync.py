from fastapi import APIRouter

from src.worker.sync import sync_worker

router = APIRouter()


@router.post("/api/sync/trigger")
async def trigger_sync():
    await sync_worker()
    return {"status": "ok"}
