from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

from app.db.models.user_content import UserContentRelation


class UserContentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    @contextmanager
    def session_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_relation(
        self, 
        user_id: int, 
        target_table: str, 
        target_id: int, 
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserContentRelation:
        with self.session_scope() as session:
            # Check for existing relation to avoid unique constraint error
            stmt = select(UserContentRelation).where(
                UserContentRelation.user_id == user_id,
                UserContentRelation.target_table == target_table,
                UserContentRelation.target_id == target_id
            )
            existing = session.scalar(stmt)
            if existing:
                return existing

            relation = UserContentRelation(
                user_id=user_id,
                target_table=target_table,
                target_id=target_id,
                task_id=task_id,
                metadata_=metadata
            )
            session.add(relation)
            session.flush()
            session.refresh(relation)
            return relation

    def list_by_user(
        self, 
        user_id: int, 
        target_table: Optional[str] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[UserContentRelation]:
        with self.session_scope() as session:
            stmt = select(UserContentRelation).where(UserContentRelation.user_id == user_id)
            if target_table:
                stmt = stmt.where(UserContentRelation.target_table == target_table)
            
            stmt = stmt.order_by(UserContentRelation.created_at.desc()).limit(limit).offset(offset)
            return list(session.scalars(stmt).all())

    def delete_relation(self, user_id: int, target_table: str, target_id: int) -> bool:
        with self.session_scope() as session:
            stmt = delete(UserContentRelation).where(
                UserContentRelation.user_id == user_id,
                UserContentRelation.target_table == target_table,
                UserContentRelation.target_id == target_id
            )
            result = session.execute(stmt)
            return result.rowcount > 0
