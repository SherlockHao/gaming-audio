import uuid
import hashlib
import tempfile
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from app.core.deps import DBSession
from app.core.models import InputAssetRef, Task
from app.core.storage import upload_file

router = APIRouter(tags=["upload"])

class InputAssetOut(BaseModel):
    input_asset_id: uuid.UUID
    task_id: uuid.UUID
    asset_kind: str
    asset_path: str
    checksum: str | None
    model_config = {"from_attributes": True}

ALLOWED_KINDS = {"video", "animation", "ui_recording", "vfx_preview", "path_ref"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

@router.post("/tasks/{task_id}/upload", response_model=InputAssetOut, status_code=201)
async def upload_asset(
    task_id: uuid.UUID,
    db: DBSession,
    file: UploadFile = File(...),
    asset_kind: str = Form(default="video"),
):
    if asset_kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=400, detail=f"Invalid asset_kind. Must be one of {ALLOWED_KINDS}")

    # Verify task exists and is in Draft/Submitted status
    result = await db.execute(select(Task).where(Task.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status not in ("Draft", "Submitted"):
        raise HTTPException(status_code=400, detail="Can only upload assets for Draft or Submitted tasks")

    # Save to temp file and compute checksum
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename or "upload")
    sha256 = hashlib.sha256()
    total_size = 0

    try:
        with open(tmp_path, "wb") as f:
            while chunk := await file.read(8192):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large (max 500MB)")
                sha256.update(chunk)
                f.write(chunk)

        checksum = sha256.hexdigest()

        # Upload to MinIO
        object_name = f"{task.project_id}/{task_id}/{file.filename or 'upload'}"
        content_type = file.content_type or "application/octet-stream"
        asset_path = await upload_file(tmp_path, object_name, content_type)

    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if os.path.exists(tmp_dir):
            os.rmdir(tmp_dir)

    # Create InputAssetRef record
    asset_ref = InputAssetRef(
        task_id=task_id,
        asset_kind=asset_kind,
        asset_path=asset_path,
        checksum=checksum,
    )
    db.add(asset_ref)
    await db.commit()
    await db.refresh(asset_ref)

    return asset_ref
