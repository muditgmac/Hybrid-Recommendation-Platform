"""Database engine and SQLAlchemy session helpers."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class for ORM models."""


def build_engine(database_url: str, *, echo: bool = False) -> Engine:
    """Create the application database engine."""
    return create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
    )


def build_session_factory(engine: Engine) -> sessionmaker:
    """Return a reusable factory for short-lived database sessions."""
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def create_schema(engine: Engine) -> None:
    """Create application tables that do not already exist."""
    from src.database import models  # noqa: F401

    Base.metadata.create_all(engine)
