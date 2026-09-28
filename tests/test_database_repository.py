"""Tests for recommendation serving persistence and metadata filtering."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.database.models import (
    Item,
    ItemCategory,
    RecommendationEvent,
    UserInteraction,
)
from src.database.repository import (
    add_recommendation_events,
    filter_candidate_indices,
    get_items_by_indices,
    get_user_history,
)
from src.database.session import Base


def build_test_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    session = Session(engine)

    session.add_all(
        [
            Item(
                global_idx=10,
                item_id="A10",
                title="Science Film",
                metadata_json={"year": 2024},
            ),
            Item(
                global_idx=20,
                item_id="A20",
                title="Drama Film",
                metadata_json={"year": 2023},
            ),
            Item(
                global_idx=30,
                item_id="A30",
                title="Another Science Film",
                metadata_json={"year": 2022},
            ),
        ]
    )

    session.add_all(
        [
            ItemCategory(global_idx=10, category="Sci-Fi"),
            ItemCategory(global_idx=10, category="Action"),
            ItemCategory(global_idx=20, category="Drama"),
            ItemCategory(global_idx=30, category="Sci-Fi"),
        ]
    )

    session.add_all(
        [
            UserInteraction(user_id=7, global_idx=20, position=0),
            UserInteraction(user_id=7, global_idx=10, position=1),
        ]
    )

    session.commit()
    return session


def test_get_user_history_preserves_sequence():
    session = build_test_session()

    assert get_user_history(session, 7) == [20, 10]

    session.close()


def test_get_items_by_indices_returns_metadata():
    session = build_test_session()

    items = get_items_by_indices(session, [10, 30])

    assert items[10].title == "Science Film"
    assert items[30].metadata_json["year"] == 2022

    session.close()


def test_metadata_filter_preserves_faiss_order():
    session = build_test_session()

    candidates = [20, 30, 10]

    filtered = filter_candidate_indices(
        session,
        candidates,
        category="Sci-Fi",
    )

    assert filtered == [30, 10]

    session.close()


def test_item_can_have_multiple_categories():
    session = build_test_session()

    candidates = [20, 30, 10]

    assert filter_candidate_indices(
        session,
        candidates,
        category="Action",
    ) == [10]

    assert filter_candidate_indices(
        session,
        candidates,
        category="Sci-Fi",
    ) == [30, 10]

    session.close()


def test_no_metadata_filter_keeps_all_candidates():
    session = build_test_session()

    candidates = [20, 30, 10]

    assert filter_candidate_indices(session, candidates) == candidates

    session.close()


def test_recommendation_events_are_persisted():
    session = build_test_session()

    recommendations = [
        {
            "global_idx": 30,
            "rank": 1,
            "retrieval_score": 0.91,
            "ranking_score": 0.97,
        },
        {
            "global_idx": 10,
            "rank": 2,
            "retrieval_score": 0.88,
            "ranking_score": 0.94,
        },
    ]

    add_recommendation_events(
        session,
        user_id=7,
        recommendations=recommendations,
        category_filter="Sci-Fi",
    )
    session.commit()

    events = list(
        session.scalars(
            select(RecommendationEvent).order_by(
                RecommendationEvent.rank
            )
        )
    )

    assert len(events) == 2
    assert events[0].global_idx == 30
    assert events[0].category_filter == "Sci-Fi"
    assert events[1].global_idx == 10

    session.close()
