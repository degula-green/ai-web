from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def build_engine(settings: Settings | None = None):
    resolved = settings or get_settings()
    return create_engine(resolved.mysql.sqlalchemy_url, echo=resolved.mysql.echo, future=True)


def build_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    engine = build_engine(settings)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)
