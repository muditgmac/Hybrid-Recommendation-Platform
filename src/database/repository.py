"""Database operations used by the online recommendation service."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import (
    Item,
    ItemCategory,
    RecommendationEvent,
    UserInteraction,
)


def get_user_history(
    session: Session,
    user_id: int,
) -> list[int]:
    """Return a user's item history in sequence order."""

    stmt = (
        select(UserInteraction.global_idx)
        .where(UserInteraction.user_id == user_id)
        .order_by(UserInteraction.position)
    )

    return list(session.scalars(stmt))


def get_items_by_indices(
    session: Session,
    global_indices: Sequence[int],
) -> dict[int, Item]:
    """Load item metadata keyed by global item index."""

    if not global_indices:
        return {}

    stmt = select(Item).where(Item.global_idx.in_(global_indices))

    return {
        item.global_idx: item
        for item in session.scalars(stmt)
    }


def filter_candidate_indices(
    session: Session,
    candidate_indices: Sequence[int],
    category: str | None = None,
) -> list[int]:
    """Filter FAISS candidates by canonical category.

    Candidate order is preserved so retrieval scores remain aligned.
    """

    if not category:
        return list(candidate_indices)

    if not candidate_indices:
        return []

    stmt = select(ItemCategory.global_idx).where(
        ItemCategory.global_idx.in_(candidate_indices),
        ItemCategory.category == category,
    )

    allowed = set(session.scalars(stmt))

    return [
        global_idx
        for global_idx in candidate_indices
        if global_idx in allowed
    ]


def add_recommendation_events(
    session: Session,
    *,
    user_id: int,
    recommendations: Sequence[dict],
    category_filter: str | None = None,
) -> None:
    """Persist one audit event for each recommendation returned."""

    events = [
        RecommendationEvent(
            user_id=user_id,
            global_idx=int(rec["global_idx"]),
            rank=int(rec["rank"]),
            retrieval_score=float(rec["retrieval_score"]),
            ranking_score=float(rec["ranking_score"]),
            category_filter=category_filter,
        )
        for rec in recommendations
    ]

    session.add_all(events)
