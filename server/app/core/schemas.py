import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

# --- Project ---
class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)

class ProjectOut(BaseModel):
    project_id: uuid.UUID
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}

# --- Task ---
class TaskCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(..., max_length=255)
    requester: str = Field(..., max_length=128)
    asset_type: Literal["sfx", "ui", "ambience_loop"]
    semantic_scene: str = Field(..., max_length=64)
    play_mode: Literal["one_shot", "loop"]
    tags: list[str] | None = None
    notes: str | None = None
    priority: int = 0

class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    asset_type: Literal["sfx", "ui", "ambience_loop"] | None = None
    semantic_scene: str | None = Field(None, max_length=64)
    play_mode: Literal["one_shot", "loop"] | None = None
    tags: list[str] | None = None
    notes: str | None = None
    priority: int | None = None

class TaskOut(BaseModel):
    task_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    requester: str
    asset_type: str
    semantic_scene: str
    play_mode: str
    tags: list[str] | None
    notes: str | None
    priority: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class TaskListOut(BaseModel):
    items: list[TaskOut]
    total: int
