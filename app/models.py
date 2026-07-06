"""Database tables."""

from datetime import date, datetime, timezone

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[str]
    question: Mapped[str]
    answer: Mapped[str]
    explanation: Mapped[str]

    # SM-2 state lives on the card
    repetitions: Mapped[int] = mapped_column(default=0)
    interval_days: Mapped[int] = mapped_column(default=0)
    ease_factor: Mapped[float] = mapped_column(default=2.5)
    due_date: Mapped[date] = mapped_column(default=lambda: date.today())

    reviews: Mapped[list["Review"]] = relationship(back_populates="card")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"))
    grade: Mapped[int]
    reviewed_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    card: Mapped["Card"] = relationship(back_populates="reviews")