import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column as mc

from src.core.database import Base


class Place(Base):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mc(primary_key=True, default=uuid.uuid4, index=True)

    name: Mapped[str] = mc(String(200))

    city: Mapped[str] = mc(String(100))

    address: Mapped[str] = mc(String(200))

    seats_pattern: Mapped[str | None] = mc(String, nullable=True)

    changed_at: Mapped[datetime] = mc(DateTime(timezone=True))

    created_at: Mapped[datetime] = mc(DateTime(timezone=True))

    events: Mapped[list["Event"]] = relationship(back_populates="place")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mc(primary_key=True, default=uuid.uuid4, index=True)

    name: Mapped[str] = mc(String(200))

    place_id: Mapped[uuid.UUID] = mc(ForeignKey("places.id"), nullable=False)

    event_time: Mapped[datetime] = mc(DateTime(timezone=True))

    registration_deadline: Mapped[datetime] = mc(DateTime(timezone=True))

    status: Mapped[str] = mc(String(20))

    number_of_visitors: Mapped[int] = mc(Integer, nullable=False, default=0)

    changed_at: Mapped[datetime] = mc(DateTime(timezone=True))

    created_at: Mapped[datetime] = mc(DateTime(timezone=True))

    status_changed_at: Mapped[datetime | None] = mc(
        DateTime(timezone=True), nullable=True
    )

    place: Mapped["Place"] = relationship(back_populates="events")


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id: Mapped[uuid.UUID] = mc(primary_key=True, default=uuid.uuid4, index=True)

    event_id: Mapped[uuid.UUID] = mc(ForeignKey("events.id"), nullable=False)

    first_name: Mapped[str] = mc(String(30), index=True, nullable=False)

    last_name: Mapped[str] = mc(String(30), index=True, nullable=False)

    email: Mapped[str] = mc(String(100), index=True, nullable=False)

    seat: Mapped[str] = mc(String(20), index=True, nullable=False)


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    id: Mapped[int] = mc(Integer, primary_key=True, default=1)

    last_sync_time: Mapped[datetime | None] = mc(DateTime(timezone=True), nullable=True)

    last_changed_at: Mapped[str | None] = mc(String(128), nullable=True)

    sync_status: Mapped[str] = mc(String(32), nullable=False, default="idle")
