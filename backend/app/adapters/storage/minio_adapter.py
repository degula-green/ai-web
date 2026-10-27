from __future__ import annotations

import io
import logging
from datetime import timedelta

from app.adapters.storage.base import BaseObjectStorage
from app.core.config import StorageSettings

logger = logging.getLogger(__name__)


class MinIOStorageAdapter(BaseObjectStorage):
    def __init__(self, settings: StorageSettings) -> None:
        self.settings = settings
        self.client = None
        try:
            from minio import Minio
            candidate_client = Minio(
                endpoint=settings.endpoint,
                access_key=settings.access_key,
                secret_key=settings.secret_key,
                secure=settings.use_ssl
            )

            # Do not block whole service startup when MinIO endpoint is temporarily unreachable.
            # In that case we keep client=None and fallback to URL generation mode.
            if not candidate_client.bucket_exists(settings.bucket):
                candidate_client.make_bucket(settings.bucket)
                # optionally set policy here for public read if needed
            self.client = candidate_client
        except ImportError:
            logger.warning("minio package not installed, MinIOStorageAdapter will only generate URLs")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "MinIO unavailable at startup (%s), fallback to URL-only mode. endpoint=%s bucket=%s",
                exc,
                settings.endpoint,
                settings.bucket,
            )

    def upload(self, object_name: str, data: bytes, *, content_type: str) -> str:
        if self.client:
            self.client.put_object(
                bucket_name=self.settings.bucket,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            
        scheme = "https" if self.settings.use_ssl else "http"
        return f"{scheme}://{self.settings.endpoint}/{self.settings.bucket}/{object_name}"

    def generate_presigned_upload(
        self,
        object_name: str,
        *,
        content_type: str,
        expires_in_seconds: int = 900,
    ) -> tuple[str, str]:
        file_url = self._build_file_url(object_name)
        if not self.client:
            logger.warning(
                "MinIO client unavailable, presigned upload URL falls back to direct object URL. object_name=%s",
                object_name,
            )
            return file_url, file_url

        upload_url = self.client.presigned_put_object(
            bucket_name=self.settings.bucket,
            object_name=object_name,
            expires=timedelta(seconds=expires_in_seconds),
        )
        return upload_url, file_url

    def _build_file_url(self, object_name: str) -> str:
        scheme = "https" if self.settings.use_ssl else "http"
        return f"{scheme}://{self.settings.endpoint}/{self.settings.bucket}/{object_name}"
