from fastapi import FastAPI
from src.api.routers import health

app = FastAPI(title="Events Aggregator")


app.include_router(health.router)
