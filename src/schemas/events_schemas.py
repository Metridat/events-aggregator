import uuid
from datetime import datetime

from pydantic import BaseModel


class PlaceListSchema(BaseModel):
    id: uuid.UUID
    name: str
    city: str
    address: str

    model_config = {"from_attributes": True}


class PlaceDetailSchema(PlaceListSchema):
    seats_pattern: str | None = None


class EventListSchema(BaseModel):
    id: uuid.UUID
    name: str
    place: PlaceListSchema
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = {"from_attributes": True}


class EventDetailSchema(EventListSchema):
    place: PlaceDetailSchema


class EventsResponseSchema(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventListSchema]
