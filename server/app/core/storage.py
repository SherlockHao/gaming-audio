from minio import Minio
from app.config import settings


def get_minio_client() -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


async def ensure_bucket():
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_file(file_path: str, object_name: str, content_type: str = "application/octet-stream") -> str:
    client = get_minio_client()
    client.fput_object(settings.minio_bucket, object_name, file_path, content_type=content_type)
    return f"{settings.minio_bucket}/{object_name}"


def download_file(object_name: str, file_path: str) -> None:
    client = get_minio_client()
    client.fget_object(settings.minio_bucket, object_name, file_path)


def get_presigned_url(object_name: str, expires_hours: int = 1) -> str:
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(settings.minio_bucket, object_name, expires=timedelta(hours=expires_hours))
