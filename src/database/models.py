"""ORM models for recommendation serving data."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class Item(Base):
    """Queryable item metadata used during online recommendation."""

    __tablename__ = "items"

    global_idx: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )


class ItemCategory(Base):
    """Canonical categories associated with an item."""

    __tablename__ = "item_categories"
    __table_args__ = (
        UniqueConstraint(
            "global_idx",
            "category",
            name="uq_item_category",
        ),
        Index(
            "ix_item_categories_category_global_idx",
            "category",
            "global_idx",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    global_idx: Mapped[int] = mapped_column(
        ForeignKey("items.global_idx"),
        nullable=False,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )


class UserInteraction(Base):
    """Ordered interaction history used by the user tower."""

    __tablename__ = "user_interactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "global_idx",
            name="uq_user_interaction_item",
        ),
        Index(
            "ix_user_interactions_user_position",
            "user_id",
            "position",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )

    global_idx: Mapped[int] = mapped_column(
        ForeignKey("items.global_idx"),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(Integer, nullable=False)


class RecommendationEvent(Base):
    """Audit record for recommendations returned by the serving API."""

    __tablename__ = "recommendation_events"
    __table_args__ = (
        Index(
            "ix_recommendation_events_user_created",
            "user_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )

    global_idx: Mapped[int] = mapped_column(
        ForeignKey("items.global_idx"),
        nullable=False,
    )

    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_score: Mapped[float] = mapped_column(Float, nullable=False)
    ranking_score: Mapped[float] = mapped_column(Float, nullable=False)

    category_filter: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
