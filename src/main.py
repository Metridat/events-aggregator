import logging

from fastapi import FastAPI

from src.api.routers import events
from src.api.routers.health import router as health_router
from src.api.routers.sync import router as sync_router

logging.basicConfig(level=logging.INFO)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     task = asyncio.create_task(sync_events())
#     try:
#         yield
#     finally:
#         task.cancel()
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass

app = FastAPI(title="Events Aggregator")

app.include_router(health_router)
app.include_router(sync_router)
app.include_router(events.router)
