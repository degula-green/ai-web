from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.ai_model import AIModelProviderConfig, AITokenUsageLog


@dataclass(slots=True)
class AITokenUsageSummary:
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    estimated_cost: float
    records: int


@dataclass(slots=True)
class LLMConfigRecord:
    id: int
    config_name: str
    provider: str
    is_active: bool
    api_key: str | None
    base_url: str | None
    model_name: str
    enable_thinking: bool
    thinking_budget_tokens: int
    reasoning_effort: str | None
    support_multimodal: bool
    description: str | None


class AIModelRepository:
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

    def upsert_provider_config(
        self,
        *,
        provider_code: str,
        provider_name: str,
        base_url: str,
        api_key: str,
        default_model: str,
        timeout_seconds: int,
        is_enabled: bool,
        extra_config: dict | None,
        updated_by: int,
        test_status: str | None,
        test_message: str | None,
    ) -> AIModelProviderConfig:
        with self.session_scope() as session:
            model = session.scalar(
                select(AIModelProviderConfig).where(AIModelProviderConfig.provider_code == provider_code)
            )
            now = datetime.utcnow()
            if model is None:
                model = AIModelProviderConfig(
                    provider_code=provider_code,
                    provider_name=provider_name,
                    base_url=base_url,
                    api_key=api_key,
                    default_model=default_model,
                    timeout_seconds=timeout_seconds,
                    is_enabled=is_enabled,
                    extra_config=extra_config,
                    created_by=updated_by,
                    updated_by=updated_by,
                    last_test_status=test_status,
                    last_test_message=test_message,
                    last_test_at=now if test_status else None,
                )
                session.add(model)
            else:
                model.provider_name = provider_name
                model.base_url = base_url
                model.api_key = api_key
                model.default_model = default_model
                model.timeout_seconds = timeout_seconds
                model.is_enabled = is_enabled
                model.extra_config = extra_config
                model.updated_by = updated_by
                model.last_test_status = test_status
                model.last_test_message = test_message
                model.last_test_at = now if test_status else model.last_test_at

            session.flush()
            session.refresh(model)
            return model

    def list_provider_configs(self, *, include_disabled: bool = True) -> list[AIModelProviderConfig]:
        with self.session_scope() as session:
            stmt = select(AIModelProviderConfig).order_by(AIModelProviderConfig.id.desc())
            if not include_disabled:
                stmt = stmt.where(AIModelProviderConfig.is_enabled.is_(True))
            return list(session.scalars(stmt).all())

    def get_provider_config(self, provider_code: str) -> AIModelProviderConfig | None:
        with self.session_scope() as session:
            return session.scalar(
                select(AIModelProviderConfig).where(AIModelProviderConfig.provider_code == provider_code)
            )

    def get_active_llm_config(self) -> LLMConfigRecord | None:
        with self.session_scope() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                        id,
                        config_name,
                        provider,
                        is_active,
                        api_key,
                        base_url,
                        model_name,
                        enable_thinking,
                        thinking_budget_tokens,
                        reasoning_effort,
                        support_multimodal,
                        description
                    FROM llm_configs
                    WHERE is_active = 1
                    ORDER BY id ASC
                    LIMIT 1
                    """
                )
            ).mappings().first()
            if row is None:
                return None
            return LLMConfigRecord(
                id=int(row["id"]),
                config_name=str(row["config_name"]),
                provider=str(row["provider"]),
                is_active=bool(row["is_active"]),
                api_key=str(row["api_key"] or "").strip() or None,
                base_url=str(row["base_url"] or "").strip() or None,
                model_name=str(row["model_name"]),
                enable_thinking=bool(row["enable_thinking"]),
                thinking_budget_tokens=int(row["thinking_budget_tokens"] or 4096),
                reasoning_effort=str(row["reasoning_effort"] or "").strip() or None,
                support_multimodal=bool(row["support_multimodal"]),
                description=str(row["description"] or "").strip() or None,
            )

    def create_usage_log(
        self,
        *,
        user_id: int,
        task_id: str | None,
        scene: str,
        provider_code: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int,
        estimated_cost: float,
        currency: str,
        request_id: str | None,
        remark: str | None,
        metadata_json: dict | None,
    ) -> AITokenUsageLog:
        with self.session_scope() as session:
            total_tokens = max(0, input_tokens) + max(0, output_tokens) + max(0, cached_tokens)
            model = AITokenUsageLog(
                user_id=user_id,
                task_id=task_id,
                scene=scene,
                provider_code=provider_code,
                model_name=model_name,
                input_tokens=max(0, input_tokens),
                output_tokens=max(0, output_tokens),
                cached_tokens=max(0, cached_tokens),
                total_tokens=total_tokens,
                estimated_cost=max(0.0, estimated_cost),
                currency=currency,
                request_id=request_id,
                remark=remark,
                metadata_json=metadata_json,
            )
            session.add(model)
            session.flush()
            session.refresh(model)
            return model

    def summarize_usage(
        self,
        *,
        user_id: int,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> AITokenUsageSummary:
        with self.session_scope() as session:
            stmt = select(
                func.coalesce(func.sum(AITokenUsageLog.input_tokens), 0),
                func.coalesce(func.sum(AITokenUsageLog.output_tokens), 0),
                func.coalesce(func.sum(AITokenUsageLog.cached_tokens), 0),
                func.coalesce(func.sum(AITokenUsageLog.total_tokens), 0),
                func.coalesce(func.sum(AITokenUsageLog.estimated_cost), 0),
                func.count(AITokenUsageLog.id),
            ).where(AITokenUsageLog.user_id == user_id)
            if from_time is not None:
                stmt = stmt.where(AITokenUsageLog.created_at >= from_time)
            if to_time is not None:
                stmt = stmt.where(AITokenUsageLog.created_at < to_time)

            row = session.execute(stmt).one()
            return AITokenUsageSummary(
                input_tokens=int(row[0] or 0),
                output_tokens=int(row[1] or 0),
                cached_tokens=int(row[2] or 0),
                total_tokens=int(row[3] or 0),
                estimated_cost=float(row[4] or 0.0),
                records=int(row[5] or 0),
            )
