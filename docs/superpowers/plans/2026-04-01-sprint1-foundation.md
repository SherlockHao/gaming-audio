# Sprint 1: Foundation & Rule Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the project skeleton, database, Task CRUD API, rule engine framework, async task queue, file storage, frontend scaffold, and test infrastructure — everything needed for M1 milestone.

**Architecture:** Modular monolith with Python/FastAPI backend (8 module directories), PostgreSQL + Redis + MinIO via Docker Compose, Celery workers for async tasks, Next.js 14 frontend with Ant Design 5. All modules share a single database and communicate via function calls (sync) or Celery tasks (async).

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Celery, Redis, MinIO, PostgreSQL 16, Next.js 14, TypeScript, Ant Design 5, pnpm, pytest, Jest

---

## File Structure

### Backend (`server/`)

```
server/
├── pyproject.toml                    # Project config, dependencies
├── Dockerfile                        # Backend container
├── alembic.ini                       # Alembic config
├── alembic/
│   ├── env.py                        # Migration environment
│   └── versions/                     # Migration scripts
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app factory
│   ├── config.py                     # Settings via pydantic-settings
│   ├── database.py                   # SQLAlchemy engine + session
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py                 # All SQLAlchemy ORM models (12 tables)
│   │   ├── schemas.py                # Pydantic request/response schemas
│   │   ├── deps.py                   # FastAPI dependencies (db session, etc)
│   │   └── state_machine.py          # Task state machine definition
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── task/
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Task CRUD routes
│   │   │   └── service.py            # Task business logic
│   │   ├── rule/
│   │   │   ├── __init__.py
│   │   │   ├── router.py             # Rule CRUD routes
│   │   │   ├── service.py            # Rule resolution logic
│   │   │   └── engine.py             # 4-tier rule engine
│   │   ├── intent/
│   │   │   └── __init__.py
│   │   ├── audio_pipeline/
│   │   │   └── __init__.py
│   │   ├── wwise/
│   │   │   └── __init__.py
│   │   ├── ue_binding/
│   │   │   └── __init__.py
│   │   ├── qa/
│   │   │   └── __init__.py
│   │   └── audit/
│   │       ├── __init__.py
│   │       ├── router.py             # Audit log query routes
│   │       └── service.py            # Audit log write helpers
│   └── worker/
│       ├── __init__.py
│       └── celery_app.py             # Celery app configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # pytest fixtures (test db, client)
│   ├── test_health.py                # Health check test
│   ├── test_task_crud.py             # Task CRUD tests
│   ├── test_rule_engine.py           # Rule engine tests
│   └── test_state_machine.py         # State machine tests
```

### Frontend (`web/`)

```
web/
├── package.json
├── tsconfig.json
├── next.config.ts
├── .env.local.example
├── src/
│   ├── app/
│   │   ├── layout.tsx                # Root layout with Ant Design provider
│   │   ├── page.tsx                  # Redirect to /tasks
│   │   ├── tasks/
│   │   │   └── page.tsx              # Task list page (placeholder)
│   │   └── admin/
│   │       └── page.tsx              # Admin page (placeholder)
│   ├── lib/
│   │   ├── api.ts                    # API client (fetch wrapper)
│   │   └── types.ts                  # Shared TypeScript types
│   └── components/
│       └── providers.tsx             # AntD + QueryClient providers
```

### Infrastructure

```
docker-compose.yml                    # PostgreSQL + Redis + MinIO
.env.example                          # Environment variable template
```

---

## Task 1: Docker Compose & Environment Setup

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.env`
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
venv/

# Node
node_modules/
.next/
web/.next/

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# MinIO data
minio_data/
```

- [ ] **Step 2: Create .env.example**

```env
# PostgreSQL
POSTGRES_USER=gaming_audio
POSTGRES_PASSWORD=gaming_audio_dev
POSTGRES_DB=gaming_audio
DATABASE_URL=postgresql+asyncpg://gaming_audio:gaming_audio_dev@localhost:5432/gaming_audio

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=gaming-audio

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-gaming_audio}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gaming_audio_dev}
      POSTGRES_DB: ${POSTGRES_DB:-gaming_audio}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gaming_audio"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
  minio_data:
```

- [ ] **Step 4: Copy .env.example to .env and start services**

Run: `cp .env.example .env && docker compose up -d`
Expected: All 3 services start and pass health checks.

Run: `docker compose ps`
Expected: postgres, redis, minio all show "healthy" or "running"

- [ ] **Step 5: Commit**

```bash
git add .gitignore .env.example docker-compose.yml
git commit -m "feat: add Docker Compose with PostgreSQL, Redis, and MinIO"
```

---

## Task 2: Backend Project Skeleton

**Files:**
- Create: `server/pyproject.toml`
- Create: `server/app/__init__.py`
- Create: `server/app/main.py`
- Create: `server/app/config.py`
- Create: `server/app/database.py`
- Create: `server/app/core/__init__.py`
- Create: `server/app/core/deps.py`
- Create: module `__init__.py` files (8 modules)
- Create: `server/app/worker/__init__.py`
- Create: `server/app/worker/celery_app.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "gaming-audio-server"
version = "0.1.0"
description = "AI Game Audio Production & Integration System"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "celery[redis]>=5.4.0",
    "redis>=5.0.0",
    "minio>=7.2.0",
    "structlog>=24.0.0",
    "python-multipart>=0.0.9",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.7.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100
```

- [ ] **Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://gaming_audio:gaming_audio_dev@localhost:5432/gaming_audio"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "gaming-audio"
    minio_secure: bool = False

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 3: Create database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        yield session
```

- [ ] **Step 4: Create deps.py**

```python
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

DBSession = Annotated[AsyncSession, Depends(get_db)]
```

- [ ] **Step 5: Create main.py with health check**

```python
from fastapi import FastAPI

from app.modules.task.router import router as task_router
from app.modules.rule.router import router as rule_router
from app.modules.audit.router import router as audit_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Game Audio System",
        version="0.1.0",
        docs_url="/docs",
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    app.include_router(task_router, prefix="/api/v1")
    app.include_router(rule_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")

    return app


app = create_app()
```

- [ ] **Step 6: Create celery_app.py**

```python
from celery import Celery

from app.config import settings

celery_app = Celery(
    "gaming_audio",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

- [ ] **Step 7: Create all module __init__.py files**

Create empty `__init__.py` in each of these directories:
- `server/app/__init__.py`
- `server/app/core/__init__.py`
- `server/app/modules/__init__.py`
- `server/app/modules/task/__init__.py`
- `server/app/modules/rule/__init__.py`
- `server/app/modules/intent/__init__.py`
- `server/app/modules/audio_pipeline/__init__.py`
- `server/app/modules/wwise/__init__.py`
- `server/app/modules/ue_binding/__init__.py`
- `server/app/modules/qa/__init__.py`
- `server/app/modules/audit/__init__.py`
- `server/app/worker/__init__.py`
- `server/tests/__init__.py`

Also create placeholder routers so main.py can import them:

`server/app/modules/task/router.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["tasks"])
```

`server/app/modules/rule/router.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["rules"])
```

`server/app/modules/audit/router.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["audit"])
```

- [ ] **Step 8: Install dependencies and verify server starts**

Run: `cd server && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: All dependencies install successfully.

Run: `cd server && uvicorn app.main:app --host 0.0.0.0 --port 8000 &` then `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

- [ ] **Step 9: Commit**

```bash
git add server/
git commit -m "feat: add backend project skeleton with FastAPI, Celery, and 8 module directories"
```

---

## Task 3: Database Models (12 Tables)

**Files:**
- Create: `server/app/core/models.py`

- [ ] **Step 1: Create all 12 SQLAlchemy ORM models**

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    style_bible: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    tasks: Mapped[list["Task"]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_tasks_project_status", "project_id", "status"),
        Index("idx_tasks_requester", "requester"),
        Index("idx_tasks_created", "created_at"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requester: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    semantic_scene: Mapped[str] = mapped_column(String(64), nullable=False)
    play_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Draft")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    project: Mapped["Project"] = relationship(back_populates="tasks")
    input_assets: Mapped[list["InputAssetRef"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    intent_spec: Mapped["AudioIntentSpec | None"] = relationship(back_populates="task", uselist=False)


class InputAssetRef(Base):
    __tablename__ = "input_asset_refs"
    __table_args__ = (Index("idx_input_assets_task", "task_id"),)

    input_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    asset_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    asset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    task: Mapped["Task"] = relationship(back_populates="input_assets")


class AudioIntentSpec(Base):
    __tablename__ = "audio_intent_specs"
    __table_args__ = (Index("idx_intent_task", "task_id"),)

    intent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    semantic_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intensity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    material_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timing_points: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    loop_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    variation_count: Mapped[int] = mapped_column(SmallInteger, default=3)
    design_pattern: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category_rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("category_rules.rule_id"), nullable=True)
    wwise_template_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("wwise_templates.template_id"), nullable=True)
    ue_binding_strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    unresolved_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    task: Mapped["Task"] = relationship(back_populates="intent_spec")


class CandidateAudio(Base):
    __tablename__ = "candidate_audios"
    __table_args__ = (
        Index("idx_candidates_task", "task_id"),
        Index("idx_candidates_task_stage", "task_id", "stage"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    generation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[str] = mapped_column(String(16), nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class QcReport(Base):
    __tablename__ = "qc_reports"
    __table_args__ = (
        Index("idx_qc_task", "task_id"),
        Index("idx_qc_candidate", "candidate_id"),
    )

    qc_report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidate_audios.candidate_id"), nullable=False)
    peak_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    loudness_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    spectrum_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    head_tail_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    format_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    qc_status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class WwiseObjectManifest(Base):
    __tablename__ = "wwise_object_manifests"
    __table_args__ = (Index("idx_wwise_manifest_task", "task_id"),)

    manifest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    object_entries: Mapped[dict] = mapped_column(JSONB, nullable=False)
    import_status: Mapped[str] = mapped_column(String(16), nullable=False)
    build_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class BindingManifest(Base):
    __tablename__ = "binding_manifests"
    __table_args__ = (Index("idx_binding_manifest_task", "task_id"),)

    binding_manifest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    bindings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    unresolved_bindings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class QaIssue(Base):
    __tablename__ = "qa_issues"
    __table_args__ = (
        Index("idx_qa_task", "task_id"),
        Index("idx_qa_project_type", "project_id", "issue_type"),
        Index("idx_qa_status", "resolution_status"),
    )

    qa_issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tasks.task_id"), nullable=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    timestamp_sec: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    related_actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_skill: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_event: Mapped[str | None] = mapped_column(String(256), nullable=True)
    root_cause_guess: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_refs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class CategoryRule(Base):
    __tablename__ = "category_rules"
    __table_args__ = (Index("idx_rules_project_category", "project_id", "category", "is_active"),)

    rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_level: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class WwiseTemplate(Base):
    __tablename__ = "wwise_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.project_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    template_type: Mapped[str] = mapped_column(String(32), nullable=False)
    template_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_task", "task_id", "created_at"),
        Index("idx_audit_project_action", "project_id", "action", "created_at"),
    )

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    old_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class ReviewRecord(Base):
    __tablename__ = "review_records"
    __table_args__ = (Index("idx_review_task", "task_id"),)

    review_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    review_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class RollbackPoint(Base):
    __tablename__ = "rollback_points"
    __table_args__ = (Index("idx_rollback_task", "task_id", "created_at"),)

    rollback_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    snapshot_type: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)
```

- [ ] **Step 2: Commit**

```bash
git add server/app/core/models.py
git commit -m "feat: add 12 SQLAlchemy ORM models for all core tables"
```

---

## Task 4: Alembic Migrations

**Files:**
- Create: `server/alembic.ini`
- Create: `server/alembic/env.py`
- Generate: `server/alembic/versions/001_initial.py` (auto-generated)

- [ ] **Step 1: Create alembic.ini**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+asyncpg://gaming_audio:gaming_audio_dev@localhost:5432/gaming_audio

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create alembic/env.py**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Generate and run initial migration**

Run: `cd server && alembic revision --autogenerate -m "initial schema with 12 tables"`
Expected: Migration file created in `alembic/versions/`

Run: `cd server && alembic upgrade head`
Expected: All 12 tables created in PostgreSQL.

Verify: `docker exec -it $(docker ps -q -f name=postgres) psql -U gaming_audio -c "\dt"`
Expected: Lists all 12 tables.

- [ ] **Step 4: Commit**

```bash
git add server/alembic.ini server/alembic/
git commit -m "feat: add Alembic migrations for initial 12-table schema"
```

---

## Task 5: Pydantic Schemas & Task CRUD API

**Files:**
- Create: `server/app/core/schemas.py`
- Create: `server/app/modules/task/service.py`
- Modify: `server/app/modules/task/router.py`

- [ ] **Step 1: Create Pydantic schemas**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# --- Shared ---

class APIResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: dict | list | None = None


# --- Project ---

class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255)

class ProjectOut(BaseModel):
    project_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Task ---

VALID_ASSET_TYPES = {"sfx", "ui", "ambience_loop"}
VALID_PLAY_MODES = {"one_shot", "loop"}

class TaskCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(..., max_length=255)
    requester: str = Field(..., max_length=128)
    asset_type: str = Field(..., max_length=32)
    semantic_scene: str = Field(..., max_length=64)
    play_mode: str = Field(..., max_length=16)
    tags: list[str] | None = None
    notes: str | None = None
    priority: int = 0

class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    asset_type: str | None = Field(None, max_length=32)
    semantic_scene: str | None = Field(None, max_length=64)
    play_mode: str | None = Field(None, max_length=16)
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
```

- [ ] **Step 2: Create task service**

```python
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Task
from app.core.schemas import VALID_ASSET_TYPES, VALID_PLAY_MODES, TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, data: TaskCreate) -> Task:
        if data.asset_type not in VALID_ASSET_TYPES:
            raise ValueError(f"Invalid asset_type: {data.asset_type}. Must be one of {VALID_ASSET_TYPES}")
        if data.play_mode not in VALID_PLAY_MODES:
            raise ValueError(f"Invalid play_mode: {data.play_mode}. Must be one of {VALID_PLAY_MODES}")

        task = Task(
            project_id=data.project_id,
            title=data.title,
            requester=data.requester,
            asset_type=data.asset_type,
            semantic_scene=data.semantic_scene,
            play_mode=data.play_mode,
            tags=data.tags,
            notes=data.notes,
            priority=data.priority,
            status="Draft",
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: uuid.UUID) -> Task | None:
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        return result.scalar_one_or_none()

    async def list_tasks(
        self,
        project_id: uuid.UUID | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Task], int]:
        query = select(Task)
        count_query = select(func.count()).select_from(Task)

        if project_id:
            query = query.where(Task.project_id == project_id)
            count_query = count_query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)

        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        tasks = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return tasks, total

    async def update_task(self, task_id: uuid.UUID, data: TaskUpdate) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.status != "Draft":
            raise ValueError("Can only edit tasks in Draft status")

        update_data = data.model_dump(exclude_unset=True)
        if "asset_type" in update_data and update_data["asset_type"] not in VALID_ASSET_TYPES:
            raise ValueError(f"Invalid asset_type: {update_data['asset_type']}")
        if "play_mode" in update_data and update_data["play_mode"] not in VALID_PLAY_MODES:
            raise ValueError(f"Invalid play_mode: {update_data['play_mode']}")

        for key, value in update_data.items():
            setattr(task, key, value)

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def submit_task(self, task_id: uuid.UUID) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.status != "Draft":
            raise ValueError("Can only submit tasks in Draft status")
        task.status = "Submitted"
        await self.db.commit()
        await self.db.refresh(task)
        return task
```

- [ ] **Step 3: Implement task router**

```python
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.core.deps import DBSession
from app.core.schemas import TaskCreate, TaskListOut, TaskOut, TaskUpdate
from app.modules.task.service import TaskService

router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(data: TaskCreate, db: DBSession):
    svc = TaskService(db)
    try:
        task = await svc.create_task(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return task


@router.get("/tasks", response_model=TaskListOut)
async def list_tasks(
    db: DBSession,
    project_id: uuid.UUID | None = None,
    status: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    svc = TaskService(db)
    tasks, total = await svc.list_tasks(project_id=project_id, status=status, offset=offset, limit=limit)
    return TaskListOut(items=tasks, total=total)


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, db: DBSession):
    svc = TaskService(db)
    task = await svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: uuid.UUID, data: TaskUpdate, db: DBSession):
    svc = TaskService(db)
    try:
        task = await svc.update_task(task_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/submit", response_model=TaskOut)
async def submit_task(task_id: uuid.UUID, db: DBSession):
    svc = TaskService(db)
    try:
        task = await svc.submit_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

- [ ] **Step 4: Commit**

```bash
git add server/app/core/schemas.py server/app/modules/task/
git commit -m "feat: add Task CRUD API with service layer and Pydantic schemas"
```

---

## Task 6: Rule Engine Framework

**Files:**
- Create: `server/app/modules/rule/engine.py`
- Create: `server/app/modules/rule/service.py`
- Modify: `server/app/modules/rule/router.py`

- [ ] **Step 1: Create rule engine with 4-tier priority**

```python
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AuditLog, CategoryRule


class RuleEngine:
    """4-tier rule resolution: Task Override > Category > Template > Project."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_rule_field(
        self,
        project_id: uuid.UUID,
        category: str,
        field_name: str,
        task_overrides: dict | None = None,
    ) -> tuple[Any, str]:
        """Resolve a rule field value using 4-tier priority.

        Returns (value, source_level) where source_level is one of:
        'task_override', 'category', 'template', 'project', or 'unresolved'.
        """
        # Tier 1: Task Override
        if task_overrides and field_name in task_overrides:
            return task_overrides[field_name], "task_override"

        # Tier 2: Category Level Rule
        cat_rule = await self._find_active_rule(project_id, category, "category")
        if cat_rule and field_name in cat_rule.rule_body:
            return cat_rule.rule_body[field_name], "category"

        # Tier 3: Template Level Rule
        tpl_rule = await self._find_active_rule(project_id, category, "template")
        if tpl_rule and field_name in tpl_rule.rule_body:
            return tpl_rule.rule_body[field_name], "template"

        # Tier 4: Project Level Rule
        proj_rule = await self._find_active_rule(project_id, category, "project")
        if proj_rule and field_name in proj_rule.rule_body:
            return proj_rule.rule_body[field_name], "project"

        return None, "unresolved"

    async def resolve_all_fields(
        self,
        project_id: uuid.UUID,
        category: str,
        field_names: list[str],
        task_overrides: dict | None = None,
    ) -> dict[str, tuple[Any, str]]:
        """Resolve multiple fields at once."""
        results = {}
        for field_name in field_names:
            value, source = await self.resolve_rule_field(
                project_id, category, field_name, task_overrides
            )
            results[field_name] = (value, source)
        return results

    async def get_category_rule_body(
        self, project_id: uuid.UUID, category: str
    ) -> dict | None:
        """Get the full rule body for a category."""
        rule = await self._find_active_rule(project_id, category, "category")
        return rule.rule_body if rule else None

    async def _find_active_rule(
        self, project_id: uuid.UUID, category: str, level: str
    ) -> CategoryRule | None:
        result = await self.db.execute(
            select(CategoryRule).where(
                CategoryRule.project_id == project_id,
                CategoryRule.category == category,
                CategoryRule.rule_level == level,
                CategoryRule.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def log_conflict(
        self,
        project_id: uuid.UUID,
        task_id: uuid.UUID | None,
        field_name: str,
        winning_source: str,
        losing_source: str,
    ) -> None:
        """Record a rule conflict to the audit log."""
        log = AuditLog(
            task_id=task_id,
            project_id=project_id,
            actor="system:rule_engine",
            action="rule_conflict",
            detail={
                "field": field_name,
                "winning_source": winning_source,
                "losing_source": losing_source,
            },
        )
        self.db.add(log)
        await self.db.flush()
```

- [ ] **Step 2: Create rule service with CRUD**

```python
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import CategoryRule, WwiseTemplate


class RuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Category Rules ---

    async def create_category_rule(
        self,
        project_id: uuid.UUID,
        category: str,
        rule_level: str,
        rule_body: dict,
    ) -> CategoryRule:
        rule = CategoryRule(
            project_id=project_id,
            category=category,
            rule_level=rule_level,
            rule_body=rule_body,
            version=1,
            is_active=True,
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_category_rule(self, rule_id: uuid.UUID) -> CategoryRule | None:
        result = await self.db.execute(
            select(CategoryRule).where(CategoryRule.rule_id == rule_id)
        )
        return result.scalar_one_or_none()

    async def list_category_rules(
        self, project_id: uuid.UUID, category: str | None = None
    ) -> list[CategoryRule]:
        query = select(CategoryRule).where(
            CategoryRule.project_id == project_id,
            CategoryRule.is_active == True,
        )
        if category:
            query = query.where(CategoryRule.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_category_rule(
        self, rule_id: uuid.UUID, rule_body: dict
    ) -> CategoryRule | None:
        old_rule = await self.get_category_rule(rule_id)
        if not old_rule:
            return None
        # Deactivate old version
        old_rule.is_active = False
        # Create new version
        new_rule = CategoryRule(
            project_id=old_rule.project_id,
            category=old_rule.category,
            rule_level=old_rule.rule_level,
            rule_body=rule_body,
            version=old_rule.version + 1,
            is_active=True,
        )
        self.db.add(new_rule)
        await self.db.commit()
        await self.db.refresh(new_rule)
        return new_rule

    # --- Wwise Templates ---

    async def create_wwise_template(
        self,
        project_id: uuid.UUID,
        name: str,
        template_type: str,
        template_body: dict,
    ) -> WwiseTemplate:
        template = WwiseTemplate(
            project_id=project_id,
            name=name,
            template_type=template_type,
            template_body=template_body,
            version=1,
            is_active=True,
        )
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def list_wwise_templates(self, project_id: uuid.UUID) -> list[WwiseTemplate]:
        result = await self.db.execute(
            select(WwiseTemplate).where(
                WwiseTemplate.project_id == project_id,
                WwiseTemplate.is_active == True,
            )
        )
        return list(result.scalars().all())
```

- [ ] **Step 3: Implement rule router**

```python
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.deps import DBSession
from app.modules.rule.service import RuleService

router = APIRouter(tags=["rules"])


class CategoryRuleCreate(BaseModel):
    project_id: uuid.UUID
    category: str
    rule_level: str = "category"
    rule_body: dict


class CategoryRuleOut(BaseModel):
    rule_id: uuid.UUID
    project_id: uuid.UUID
    category: str
    rule_level: str
    rule_body: dict
    version: int
    is_active: bool

    model_config = {"from_attributes": True}


class WwiseTemplateCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    template_type: str
    template_body: dict


class WwiseTemplateOut(BaseModel):
    template_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    template_type: str
    template_body: dict
    version: int
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/rules/categories", response_model=CategoryRuleOut, status_code=201)
async def create_category_rule(data: CategoryRuleCreate, db: DBSession):
    svc = RuleService(db)
    rule = await svc.create_category_rule(
        project_id=data.project_id,
        category=data.category,
        rule_level=data.rule_level,
        rule_body=data.rule_body,
    )
    return rule


@router.get("/rules/categories", response_model=list[CategoryRuleOut])
async def list_category_rules(
    db: DBSession,
    project_id: uuid.UUID = Query(...),
    category: str | None = None,
):
    svc = RuleService(db)
    return await svc.list_category_rules(project_id, category)


@router.put("/rules/categories/{rule_id}", response_model=CategoryRuleOut)
async def update_category_rule(rule_id: uuid.UUID, data: dict, db: DBSession):
    svc = RuleService(db)
    rule = await svc.update_category_rule(rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/rules/wwise-templates", response_model=WwiseTemplateOut, status_code=201)
async def create_wwise_template(data: WwiseTemplateCreate, db: DBSession):
    svc = RuleService(db)
    template = await svc.create_wwise_template(
        project_id=data.project_id,
        name=data.name,
        template_type=data.template_type,
        template_body=data.template_body,
    )
    return template


@router.get("/rules/wwise-templates", response_model=list[WwiseTemplateOut])
async def list_wwise_templates(db: DBSession, project_id: uuid.UUID = Query(...)):
    svc = RuleService(db)
    return await svc.list_wwise_templates(project_id)
```

- [ ] **Step 4: Commit**

```bash
git add server/app/modules/rule/
git commit -m "feat: add rule engine with 4-tier priority and CRUD API"
```

---

## Task 7: Task State Machine

**Files:**
- Create: `server/app/core/state_machine.py`

- [ ] **Step 1: Define the complete task state machine**

```python
TASK_STATES = [
    "Draft",
    "Submitted",
    "SpecGenerated",
    "SpecReviewPending",
    "AudioGenerated",
    "AudioGenerationFailed",
    "QCReady",
    "QCFailed",
    "WwiseImported",
    "WwiseImportFailed",
    "BankBuilt",
    "BankBuildFailed",
    "UEBound",
    "UEBindFailed",
    "BindingReviewPending",
    "QARun",
    "ReviewPending",
    "Approved",
    "Rejected",
    "RolledBack",
]

# (trigger_name, source_state, dest_state)
TASK_TRANSITIONS = [
    ("submit", "Draft", "Submitted"),
    ("spec_ok", "Submitted", "SpecGenerated"),
    ("spec_review", "Submitted", "SpecReviewPending"),
    ("spec_confirmed", "SpecReviewPending", "SpecGenerated"),
    ("audio_ok", "SpecGenerated", "AudioGenerated"),
    ("audio_fail", "SpecGenerated", "AudioGenerationFailed"),
    ("qc_pass", "AudioGenerated", "QCReady"),
    ("qc_fail", "AudioGenerated", "QCFailed"),
    ("wwise_ok", "QCReady", "WwiseImported"),
    ("wwise_fail", "QCReady", "WwiseImportFailed"),
    ("bank_ok", "WwiseImported", "BankBuilt"),
    ("bank_fail", "WwiseImported", "BankBuildFailed"),
    ("ue_ok", "BankBuilt", "UEBound"),
    ("ue_fail", "BankBuilt", "UEBindFailed"),
    ("ue_review", "BankBuilt", "BindingReviewPending"),
    ("binding_confirmed", "BindingReviewPending", "UEBound"),
    ("qa_done", "UEBound", "QARun"),
    ("review_ready", "QARun", "ReviewPending"),
    ("approve", "ReviewPending", "Approved"),
    ("reject", "ReviewPending", "Rejected"),
    ("rollback", "Rejected", "RolledBack"),
    # Retry paths
    ("retry_audio", "AudioGenerationFailed", "SpecGenerated"),
    ("retry_qc", "QCFailed", "AudioGenerated"),
    ("retry_wwise", "WwiseImportFailed", "QCReady"),
    ("retry_bank", "BankBuildFailed", "WwiseImported"),
    ("retry_ue", "UEBindFailed", "BankBuilt"),
]

# Build a lookup: {(trigger, source): dest}
_TRANSITION_MAP: dict[tuple[str, str], str] = {
    (t[0], t[1]): t[2] for t in TASK_TRANSITIONS
}


class InvalidTransition(Exception):
    pass


def transition_task(current_state: str, trigger: str) -> str:
    """Apply a trigger to the current state and return the new state.

    Raises InvalidTransition if the trigger is not valid for the current state.
    """
    key = (trigger, current_state)
    if key not in _TRANSITION_MAP:
        valid = [t[0] for t in TASK_TRANSITIONS if t[1] == current_state]
        raise InvalidTransition(
            f"Cannot apply '{trigger}' to state '{current_state}'. "
            f"Valid triggers: {valid}"
        )
    return _TRANSITION_MAP[key]


def get_valid_triggers(current_state: str) -> list[str]:
    """Return list of valid trigger names for the given state."""
    return [t[0] for t in TASK_TRANSITIONS if t[1] == current_state]
```

- [ ] **Step 2: Commit**

```bash
git add server/app/core/state_machine.py
git commit -m "feat: add task state machine with 20 states and transition logic"
```

---

## Task 8: Audit Log Service

**Files:**
- Create: `server/app/modules/audit/service.py`
- Modify: `server/app/modules/audit/router.py`

- [ ] **Step 1: Create audit service**

```python
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        actor: str,
        action: str,
        task_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        old_state: str | None = None,
        new_state: str | None = None,
        detail: dict | None = None,
        error_context: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            task_id=task_id,
            project_id=project_id,
            actor=actor,
            action=action,
            old_state=old_state,
            new_state=new_state,
            detail=detail,
            error_context=error_context,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_task_logs(
        self, task_id: uuid.UUID, limit: int = 50
    ) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.task_id == task_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
```

- [ ] **Step 2: Implement audit router**

```python
import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.deps import DBSession
from app.modules.audit.service import AuditService

router = APIRouter(tags=["audit"])


class AuditLogOut(BaseModel):
    log_id: int
    task_id: uuid.UUID | None
    project_id: uuid.UUID | None
    actor: str
    action: str
    old_state: str | None
    new_state: str | None
    detail: dict | None
    error_context: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/tasks/{task_id}/audit-log", response_model=list[AuditLogOut])
async def get_task_audit_log(
    task_id: uuid.UUID,
    db: DBSession,
    limit: int = Query(50, ge=1, le=200),
):
    svc = AuditService(db)
    logs = await svc.get_task_logs(task_id, limit)
    return logs
```

- [ ] **Step 3: Commit**

```bash
git add server/app/modules/audit/
git commit -m "feat: add audit log service and query API"
```

---

## Task 9: Test Infrastructure & Core Tests

**Files:**
- Create: `server/tests/conftest.py`
- Create: `server/tests/test_health.py`
- Create: `server/tests/test_task_crud.py`
- Create: `server/tests/test_rule_engine.py`
- Create: `server/tests/test_state_machine.py`

- [ ] **Step 1: Create conftest.py with test fixtures**

```python
import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.models import Base, Project
from app.database import get_db
from app.main import create_app

TEST_DB_URL = "postgresql+asyncpg://gaming_audio:gaming_audio_dev@localhost:5432/gaming_audio_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session():
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession):
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_project(db_session: AsyncSession) -> Project:
    project = Project(name="Test Action Game")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project
```

- [ ] **Step 2: Create health check test**

```python
import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Create task CRUD tests**

```python
import pytest


@pytest.mark.asyncio
async def test_create_task(client, test_project):
    response = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Boss Slam Attack",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
        "tags": ["heavy", "melee"],
        "priority": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Boss Slam Attack"
    assert data["status"] == "Draft"
    assert data["asset_type"] == "sfx"


@pytest.mark.asyncio
async def test_create_task_invalid_asset_type(client, test_project):
    response = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "VO Task",
        "requester": "planner_zhang",
        "asset_type": "vo",
        "semantic_scene": "NPC",
        "play_mode": "one_shot",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_tasks(client, test_project):
    # Create two tasks
    for title in ["Task A", "Task B"]:
        await client.post("/api/v1/tasks", json={
            "project_id": str(test_project.project_id),
            "title": title,
            "requester": "planner_zhang",
            "asset_type": "sfx",
            "semantic_scene": "Boss",
            "play_mode": "one_shot",
        })

    response = await client.get("/api/v1/tasks", params={"project_id": str(test_project.project_id)})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_get_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Get Test",
        "requester": "planner_zhang",
        "asset_type": "ui",
        "semantic_scene": "SystemUI",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]

    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Test"


@pytest.mark.asyncio
async def test_update_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Update Test",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]

    response = await client.patch(f"/api/v1/tasks/{task_id}", json={
        "title": "Updated Title",
        "priority": 5,
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["priority"] == 5


@pytest.mark.asyncio
async def test_submit_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Submit Test",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]

    response = await client.post(f"/api/v1/tasks/{task_id}/submit")
    assert response.status_code == 200
    assert response.json()["status"] == "Submitted"


@pytest.mark.asyncio
async def test_cannot_edit_submitted_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Lock Test",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")

    response = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "New Title"})
    assert response.status_code == 400
```

- [ ] **Step 4: Create state machine tests**

```python
import pytest

from app.core.state_machine import InvalidTransition, get_valid_triggers, transition_task


def test_draft_to_submitted():
    assert transition_task("Draft", "submit") == "Submitted"


def test_submitted_to_spec_generated():
    assert transition_task("Submitted", "spec_ok") == "SpecGenerated"


def test_submitted_to_spec_review_pending():
    assert transition_task("Submitted", "spec_review") == "SpecReviewPending"


def test_full_happy_path():
    state = "Draft"
    triggers = ["submit", "spec_ok", "audio_ok", "qc_pass", "wwise_ok", "bank_ok", "ue_ok", "qa_done", "review_ready", "approve"]
    for trigger in triggers:
        state = transition_task(state, trigger)
    assert state == "Approved"


def test_retry_paths():
    assert transition_task("AudioGenerationFailed", "retry_audio") == "SpecGenerated"
    assert transition_task("QCFailed", "retry_qc") == "AudioGenerated"
    assert transition_task("WwiseImportFailed", "retry_wwise") == "QCReady"


def test_invalid_transition_raises():
    with pytest.raises(InvalidTransition):
        transition_task("Draft", "approve")


def test_get_valid_triggers_draft():
    triggers = get_valid_triggers("Draft")
    assert triggers == ["submit"]


def test_get_valid_triggers_submitted():
    triggers = get_valid_triggers("Submitted")
    assert set(triggers) == {"spec_ok", "spec_review"}
```

- [ ] **Step 5: Create rule engine tests**

```python
import pytest

from app.core.models import CategoryRule
from app.modules.rule.engine import RuleEngine


@pytest.mark.asyncio
async def test_resolve_from_category_rule(db_session, test_project):
    rule = CategoryRule(
        project_id=test_project.project_id,
        category="sfx",
        rule_level="category",
        rule_body={"target_lufs": -18, "true_peak_limit": -1.0},
        version=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(
        test_project.project_id, "sfx", "target_lufs"
    )
    assert value == -18
    assert source == "category"


@pytest.mark.asyncio
async def test_task_override_takes_priority(db_session, test_project):
    rule = CategoryRule(
        project_id=test_project.project_id,
        category="sfx",
        rule_level="category",
        rule_body={"target_lufs": -18},
        version=1,
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(
        test_project.project_id, "sfx", "target_lufs",
        task_overrides={"target_lufs": -14},
    )
    assert value == -14
    assert source == "task_override"


@pytest.mark.asyncio
async def test_unresolved_field(db_session, test_project):
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(
        test_project.project_id, "sfx", "nonexistent_field"
    )
    assert value is None
    assert source == "unresolved"
```

- [ ] **Step 6: Create test database and run all tests**

Run: `docker exec -it $(docker ps -q -f name=postgres) psql -U gaming_audio -c "CREATE DATABASE gaming_audio_test;"`
Expected: `CREATE DATABASE`

Run: `cd server && pytest tests/ -v`
Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add server/tests/
git commit -m "feat: add test infrastructure with conftest, health, CRUD, state machine, and rule engine tests"
```

---

## Task 10: Frontend Project Skeleton

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/next.config.ts`
- Create: `web/.env.local.example`
- Create: `web/src/app/layout.tsx`
- Create: `web/src/app/page.tsx`
- Create: `web/src/app/tasks/page.tsx`
- Create: `web/src/app/admin/page.tsx`
- Create: `web/src/lib/api.ts`
- Create: `web/src/lib/types.ts`
- Create: `web/src/components/providers.tsx`

- [ ] **Step 1: Initialize Next.js project**

Run: `cd /Users/yiya_workstation/Documents/gaming-audio && npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-pnpm --no-turbopack`
Expected: Next.js project created in `web/` directory.

- [ ] **Step 2: Install Ant Design and dependencies**

Run: `cd web && pnpm add antd @ant-design/nextjs-registry @tanstack/react-query zustand`
Expected: Dependencies installed.

- [ ] **Step 3: Create providers.tsx**

```tsx
"use client";

import { AntdRegistry } from "@ant-design/nextjs-registry";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import React, { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <AntdRegistry>
        <ConfigProvider
          theme={{
            token: {
              colorPrimary: "#1677ff",
            },
          }}
        >
          {children}
        </ConfigProvider>
      </AntdRegistry>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 4: Create root layout.tsx**

```tsx
import { Providers } from "@/components/providers";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Game Audio System",
  description: "AI-powered game audio production and integration",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 5: Create placeholder pages**

`web/src/app/page.tsx`:
```tsx
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/tasks");
}
```

`web/src/app/tasks/page.tsx`:
```tsx
import { Typography } from "antd";

export default function TasksPage() {
  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={2}>Task List</Typography.Title>
      <Typography.Text type="secondary">Coming in Sprint 3</Typography.Text>
    </div>
  );
}
```

`web/src/app/admin/page.tsx`:
```tsx
import { Typography } from "antd";

export default function AdminPage() {
  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={2}>Admin - Rule Configuration</Typography.Title>
      <Typography.Text type="secondary">Coming in Sprint 2</Typography.Text>
    </div>
  );
}
```

- [ ] **Step 6: Create API client and types**

`web/src/lib/api.ts`:
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}
```

`web/src/lib/types.ts`:
```typescript
export interface Task {
  task_id: string;
  project_id: string;
  title: string;
  requester: string;
  asset_type: "sfx" | "ui" | "ambience_loop";
  semantic_scene: string;
  play_mode: "one_shot" | "loop";
  tags: string[] | null;
  notes: string | null;
  priority: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
}

export interface CategoryRule {
  rule_id: string;
  project_id: string;
  category: string;
  rule_level: string;
  rule_body: Record<string, unknown>;
  version: number;
  is_active: boolean;
}
```

- [ ] **Step 7: Create .env.local.example**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

- [ ] **Step 8: Verify frontend starts**

Run: `cd web && pnpm dev &` then open `http://localhost:3000`
Expected: Redirects to `/tasks` and shows "Task List" placeholder page.

- [ ] **Step 9: Commit**

```bash
git add web/
git commit -m "feat: add Next.js 14 frontend skeleton with Ant Design, TanStack Query, and placeholder pages"
```

---

## Task 11: Project-Level CRUD (Seed Helper)

**Files:**
- Modify: `server/app/modules/task/router.py` (add project routes)
- Modify: `server/app/modules/task/service.py` (add project service)

- [ ] **Step 1: Add project creation to task service**

Add to `server/app/modules/task/service.py`:

```python
from app.core.models import Project
from app.core.schemas import ProjectCreate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, data: ProjectCreate) -> Project:
        project = Project(name=data.name)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def list_projects(self) -> list[Project]:
        result = await self.db.execute(select(Project))
        return list(result.scalars().all())
```

- [ ] **Step 2: Add project routes to task router**

Add to `server/app/modules/task/router.py`:

```python
from app.core.schemas import ProjectCreate, ProjectOut
from app.modules.task.service import ProjectService


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate, db: DBSession):
    svc = ProjectService(db)
    return await svc.create_project(data)


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(db: DBSession):
    svc = ProjectService(db)
    return await svc.list_projects()
```

- [ ] **Step 3: Commit**

```bash
git add server/app/modules/task/
git commit -m "feat: add Project CRUD endpoints"
```

---

## Task 12: Final Sprint 1 Integration Verification

- [ ] **Step 1: Ensure Docker services are running**

Run: `docker compose up -d && docker compose ps`
Expected: All 3 services healthy.

- [ ] **Step 2: Run all backend tests**

Run: `cd server && pytest tests/ -v --tb=short`
Expected: All tests pass (health, CRUD, state machine, rule engine).

- [ ] **Step 3: Verify backend API manually**

Run: `cd server && uvicorn app.main:app --port 8000 &`

Create project:
Run: `curl -s -X POST http://localhost:8000/api/v1/projects -H 'Content-Type: application/json' -d '{"name": "Action Game Demo"}' | python -m json.tool`
Expected: Returns project with project_id.

Create task (use the project_id from above):
Run: `curl -s -X POST http://localhost:8000/api/v1/tasks -H 'Content-Type: application/json' -d '{"project_id": "<PROJECT_ID>", "title": "Boss Slam", "requester": "planner", "asset_type": "sfx", "semantic_scene": "Boss", "play_mode": "one_shot"}' | python -m json.tool`
Expected: Returns task with task_id and status "Draft".

- [ ] **Step 4: Verify frontend starts and renders**

Run: `cd web && pnpm dev`
Expected: http://localhost:3000 shows tasks page.

- [ ] **Step 5: Final commit with all integration verified**

```bash
git add -A
git commit -m "feat: Sprint 1 complete - foundation with backend, frontend, DB, rules, tests"
git push origin main
```
