from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        # 使用赋值而非 setdefault：否则机器/终端里已存在的同名变量会挡住 .env，
        # 例如 MINIO_ENDPOINT 仍为旧端口时，改 .env 不生效。
        os.environ[key] = value


_load_local_env()


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


def _get_list(name: str, default: str) -> list[str]:
    raw = _get_env(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(raw_path: str, *, base_dir: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _prefer_existing_path(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


@dataclass(slots=True, frozen=True)
class AppSettings:
    name: str
    env: str
    debug: bool
    host: str
    port: int
    api_prefix: str
    allowed_origins: list[str]
    task_store_backend: str


@dataclass(slots=True, frozen=True)
class MySQLSettings:
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int
    echo: bool

    @property
    def sqlalchemy_url(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass(slots=True, frozen=True)
class RedisSettings:
    host: str
    port: int
    db: int
    username: str
    password: str
    use_ssl: bool

    @property
    def url(self) -> str:
        scheme = "rediss" if self.use_ssl else "redis"
        credentials = ""
        if self.username and self.password:
            credentials = f"{self.username}:{self.password}@"
        elif self.password:
            credentials = f":{self.password}@"
        elif self.username:
            credentials = f"{self.username}@"
        return f"{scheme}://{credentials}{self.host}:{self.port}/{self.db}"


@dataclass(slots=True, frozen=True)
class QdrantSettings:
    host: str
    port: int
    api_key: str
    collection: str


@dataclass(slots=True, frozen=True)
class StorageSettings:
    provider: str
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    use_ssl: bool


@dataclass(slots=True, frozen=True)
class AuthSettings:
    jwt_secret: str
    jwt_algorithm: str
    access_token_ttl_seconds: int
    refresh_token_ttl_seconds: int
    session_ttl_seconds: int
    bootstrap_password: str
    password_pepper: str


@dataclass(slots=True, frozen=True)
class VerificationSettings:
    cache_backend: str
    code_length: int
    code_ttl_seconds: int
    max_attempts: int
    mock_fixed_code: str
    resend_interval_seconds: int


@dataclass(slots=True, frozen=True)
class EmailSettings:
    provider: str
    from_email: str
    from_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_ssl: bool


@dataclass(slots=True, frozen=True)
class SmsSettings:
    provider: str
    sign_name: str
    template_code: str
    access_key_id: str
    access_key_secret: str
    endpoint: str


@dataclass(slots=True, frozen=True)
class LLMSettings:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout: int


@dataclass(slots=True, frozen=True)
class EmbeddingSettings:
    provider: str
    model: str


@dataclass(slots=True, frozen=True)
class FeishuSettings:
    app_id: str
    app_secret: str
    webhook: str


@dataclass(slots=True, frozen=True)
class CelerySettings:
    broker_url: str
    result_backend: str
    task_always_eager: bool


@dataclass(slots=True, frozen=True)
class LoggingSettings:
    level: str
    json: bool


@dataclass(slots=True, frozen=True)
class MediaCrawlerSettings:
    enabled: bool
    uv_bin: str
    root_dir: str
    python_project_dir: str
    signsrv_project_dir: str
    crawler_api_base_url: str
    signsrv_autostart: bool
    signsrv_strict_startup: bool
    signsrv_host: str
    signsrv_port: int
    signsrv_bind_address: str
    signsrv_sign_type: str
    signsrv_playwright_headless: bool
    signsrv_startup_timeout_seconds: int
    run_timeout_seconds: int
    default_account_pool_save_type: str
    default_cookie_bridge_url: str
    default_db_type: str
    default_save_data_option: str
    default_enable_ip_proxy: bool
    default_checkpoint_storage_type: str


@dataclass(slots=True, frozen=True)
class Settings:
    app: AppSettings
    mysql: MySQLSettings
    redis: RedisSettings
    qdrant: QdrantSettings
    storage: StorageSettings
    auth: AuthSettings
    verification: VerificationSettings
    email: EmailSettings
    sms: SmsSettings
    llm: LLMSettings
    embedding: EmbeddingSettings
    feishu: FeishuSettings
    celery: CelerySettings
    logging: LoggingSettings
    media_crawler: MediaCrawlerSettings


@lru_cache
def get_settings() -> Settings:
    backend_root = _backend_root()
    mediacrawler_root = _resolve_path(
        _get_env("MEDIACRAWLER_ROOT_DIR", str(backend_root / "agent-stack")),
        base_dir=backend_root,
    )
    default_python_dir = _prefer_existing_path(
        mediacrawler_root / "crawler-engine",
        mediacrawler_root / "MediaCrawlerPro-Python",
    )
    mediacrawler_python_dir = _resolve_path(
        _get_env("MEDIACRAWLER_PYTHON_DIR", str(default_python_dir)),
        base_dir=backend_root,
    )
    default_signsrv_dir = _prefer_existing_path(
        mediacrawler_root / "sign-service",
        mediacrawler_root / "MediaCrawlerPro-SignSrv",
    )
    mediacrawler_signsrv_dir = _resolve_path(
        _get_env("MEDIACRAWLER_SIGNSRV_DIR", str(default_signsrv_dir)),
        base_dir=backend_root,
    )
    return Settings(
        app=AppSettings(
            name=_get_env("APP_NAME", "AI Content Automation Workflow"),
            env=_get_env("APP_ENV", "dev"),
            debug=_get_bool("APP_DEBUG", True),
            host=_get_env("APP_HOST", "0.0.0.0"),
            port=_get_int("APP_PORT", 8000),
            api_prefix=_get_env("API_PREFIX", "/api/v1"),
            allowed_origins=_get_list("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"),
            task_store_backend=_get_env("TASK_STORE_BACKEND", "memory"),
        ),
        mysql=MySQLSettings(
            host=_get_env("MYSQL_HOST", "127.0.0.1"),
            port=_get_int("MYSQL_PORT", 3306),
            user=_get_env("MYSQL_USER", "root"),
            password=_get_env("MYSQL_PASSWORD", "change_me"),
            database=_get_env("MYSQL_DATABASE", "ai_content_automation"),
            pool_size=_get_int("MYSQL_POOL_SIZE", 10),
            echo=_get_bool("MYSQL_ECHO", False),
        ),
        redis=RedisSettings(
            host=_get_env("REDIS_HOST", "127.0.0.1"),
            port=_get_int("REDIS_PORT", 6379),
            db=_get_int("REDIS_DB", 0),
            username=os.getenv("REDIS_USERNAME", "").strip(),
            password=os.getenv("REDIS_PASSWORD", "").strip(),
            use_ssl=_get_bool("REDIS_USE_SSL", False),
        ),
        qdrant=QdrantSettings(
            host=_get_env("QDRANT_HOST", "127.0.0.1"),
            port=_get_int("QDRANT_PORT", 6333),
            api_key=os.getenv("QDRANT_API_KEY", "").strip(),
            collection=_get_env("QDRANT_COLLECTION", "kb_default"),
        ),
        storage=StorageSettings(
            provider=_get_env("STORAGE_PROVIDER", "minio"),
            endpoint=_get_env("MINIO_ENDPOINT", "127.0.0.1:9000"),
            access_key=_get_env("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=_get_env("MINIO_SECRET_KEY", "minioadmin"),
            bucket=_get_env("MINIO_BUCKET", "ai-content-assets"),
            use_ssl=_get_bool("MINIO_USE_SSL", False),
        ),
        auth=AuthSettings(
            jwt_secret=_get_env("AUTH_JWT_SECRET", "change_me_to_a_long_random_secret"),
            jwt_algorithm=_get_env("AUTH_JWT_ALGORITHM", "HS256"),
            access_token_ttl_seconds=_get_int("AUTH_ACCESS_TOKEN_TTL_SECONDS", 7200),
            refresh_token_ttl_seconds=_get_int("AUTH_REFRESH_TOKEN_TTL_SECONDS", 604800),
            session_ttl_seconds=_get_int("AUTH_SESSION_TTL_SECONDS", 604800),
            bootstrap_password=_get_env("AUTH_BOOTSTRAP_PASSWORD", "123456"),
            password_pepper=_get_env("AUTH_PASSWORD_PEPPER", "local_dev_pepper"),
        ),
        verification=VerificationSettings(
            cache_backend=_get_env("AUTH_VERIFICATION_CACHE_BACKEND", "memory"),
            code_length=_get_int("AUTH_VERIFICATION_CODE_LENGTH", 6),
            code_ttl_seconds=_get_int("AUTH_VERIFICATION_CODE_TTL_SECONDS", 300),
            max_attempts=_get_int("AUTH_VERIFICATION_MAX_ATTEMPTS", 5),
            mock_fixed_code="", # 禁用 Mock 验证码回显
            resend_interval_seconds=_get_int("AUTH_VERIFICATION_RESEND_INTERVAL_SECONDS", 60),
        ),
        email=EmailSettings(
            provider="smtp", # 强制使用真实邮件
            from_email="1361788424@qq.com",
            from_name="AI 内容自动化系统",
            smtp_host="smtp.qq.com",
            smtp_port=465, # QQ 邮箱 SSL 端口
            smtp_username="1361788424@qq.com",
            smtp_password="REDACTED_EMAIL_SMTP_PASSWORD", # 用户提供的 QQ 授权码
            smtp_use_tls=False,
            smtp_use_ssl=True,
        ),
        sms=SmsSettings(
            provider="aliyun", # 强制使用真实短信
            sign_name="速通互联验证码", # 来源于 docs
            template_code="100001",
            access_key_id="REDACTED_ALIYUN_ACCESS_KEY_ID",
            access_key_secret="REDACTED_ALIYUN_ACCESS_KEY_SECRET",
            endpoint="dypnsapi.aliyuncs.com",
        ),
        llm=LLMSettings(
            provider=_get_env("LLM_PROVIDER", "openai_compatible"),
            base_url=_get_env("LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("LLM_API_KEY", "").strip(),
            model=_get_env("LLM_MODEL", "gpt-4o-mini"),
            timeout=_get_int("LLM_TIMEOUT", 60),
        ),
        embedding=EmbeddingSettings(
            provider=_get_env("EMBEDDING_PROVIDER", "openai_compatible"),
            model=_get_env("EMBEDDING_MODEL", "text-embedding-3-small"),
        ),
        feishu=FeishuSettings(
            app_id=os.getenv("FEISHU_APP_ID", "").strip(),
            app_secret=os.getenv("FEISHU_APP_SECRET", "").strip(),
            webhook=os.getenv("FEISHU_WEBHOOK", "").strip(),
        ),
        celery=CelerySettings(
            broker_url=_get_env("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1"),
            result_backend=_get_env("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2"),
            task_always_eager=_get_bool("CELERY_TASK_ALWAYS_EAGER", False),
        ),
        logging=LoggingSettings(
            level=_get_env("LOG_LEVEL", "INFO"),
            json=_get_bool("LOG_JSON", False),
        ),
        media_crawler=MediaCrawlerSettings(
            enabled=_get_bool("MEDIACRAWLER_ENABLED", True),
            uv_bin=_get_env("MEDIACRAWLER_UV_BIN", "uv"),
            root_dir=str(mediacrawler_root),
            python_project_dir=str(mediacrawler_python_dir),
            signsrv_project_dir=str(mediacrawler_signsrv_dir),
            crawler_api_base_url=_get_env("MEDIACRAWLER_API_BASE_URL", "http://127.0.0.1:8005"),
            signsrv_autostart=_get_bool("MEDIACRAWLER_SIGNSRV_AUTOSTART", True),
            signsrv_strict_startup=_get_bool("MEDIACRAWLER_SIGNSRV_STRICT_STARTUP", True),
            signsrv_host=_get_env("MEDIACRAWLER_SIGNSRV_HOST", "127.0.0.1"),
            signsrv_port=_get_int("MEDIACRAWLER_SIGNSRV_PORT", 8989),
            signsrv_bind_address=_get_env("MEDIACRAWLER_SIGNSRV_BIND_ADDRESS", "127.0.0.1"),
            signsrv_sign_type=_get_env("MEDIACRAWLER_SIGNSRV_SIGN_TYPE", "javascript"),
            signsrv_playwright_headless=_get_bool("MEDIACRAWLER_SIGNSRV_PLAYWRIGHT_HEADLESS", True),
            signsrv_startup_timeout_seconds=_get_int("MEDIACRAWLER_SIGNSRV_STARTUP_TIMEOUT_SECONDS", 90),
            run_timeout_seconds=_get_int("MEDIACRAWLER_RUN_TIMEOUT_SECONDS", 1800),
            default_account_pool_save_type=_get_env("MEDIACRAWLER_DEFAULT_ACCOUNT_POOL_SAVE_TYPE", "mysql"),
            default_cookie_bridge_url=_get_env(
                "MEDIACRAWLER_DEFAULT_COOKIE_BRIDGE_URL", "http://127.0.0.1:8274"
            ),
            default_db_type=_get_env("MEDIACRAWLER_DEFAULT_DB_TYPE", "mysql"),
            default_save_data_option=_get_env("MEDIACRAWLER_DEFAULT_SAVE_DATA_OPTION", "db"),
            default_enable_ip_proxy=_get_bool("MEDIACRAWLER_DEFAULT_ENABLE_IP_PROXY", False),
            default_checkpoint_storage_type=_get_env(
                "MEDIACRAWLER_DEFAULT_CHECKPOINT_STORAGE_TYPE", "file"
            ),
        ),
    )
