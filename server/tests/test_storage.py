import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_ensure_bucket_creates_when_not_exists():
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = False

    with patch("app.core.storage.get_minio_client", return_value=mock_client):
        from app.core.storage import ensure_bucket
        await ensure_bucket()

    mock_client.bucket_exists.assert_called_once()
    mock_client.make_bucket.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_bucket_skips_when_exists():
    mock_client = MagicMock()
    mock_client.bucket_exists.return_value = True

    with patch("app.core.storage.get_minio_client", return_value=mock_client):
        from app.core.storage import ensure_bucket
        await ensure_bucket()

    mock_client.bucket_exists.assert_called_once()
    mock_client.make_bucket.assert_not_called()


@pytest.mark.asyncio
async def test_upload_file_returns_path():
    mock_client = MagicMock()

    with patch("app.core.storage.get_minio_client", return_value=mock_client):
        from app.core.storage import upload_file
        result = await upload_file("/tmp/test.wav", "audio/test.wav", "audio/wav")

    mock_client.fput_object.assert_called_once()
    assert "test.wav" in result


@pytest.mark.asyncio
async def test_download_file_calls_fget():
    mock_client = MagicMock()

    with patch("app.core.storage.get_minio_client", return_value=mock_client):
        from app.core.storage import download_file
        await download_file("audio/test.wav", "/tmp/out.wav")

    mock_client.fget_object.assert_called_once()
