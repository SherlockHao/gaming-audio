import asyncio
from datetime import timedelta
from minio import Minio
from app.config import settings


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


async def ensure_bucket() -> None:
    def _ensure():
        client = get_minio_client()
        if not client.bucket_exists(settings.minio_bucket):
            client.make_bucket(settings.minio_bucket)
    await asyncio.to_thread(_ensure)


async def upload_file(file_path: str, object_name: str, content_type: str = "application/octet-stream") -> str:
    def _upload():
        client = get_minio_client()
        client.fput_object(settings.minio_bucket, object_name, file_path, content_type=content_type)
        return f"{settings.minio_bucket}/{object_name}"
    return await asyncio.to_thread(_upload)


async def download_file(object_name: str, file_path: str) -> None:
    def _download():
        client = get_minio_client()
        client.fget_object(settings.minio_bucket, object_name, file_path)
    await asyncio.to_thread(_download)


async def get_presigned_url(object_name: str, expires_hours: int = 1) -> str:
    def _presign():
        client = get_minio_client()
        return client.presigned_get_object(settings.minio_bucket, object_name, expires=timedelta(hours=expires_hours))
    return await asyncio.to_thread(_presign)
