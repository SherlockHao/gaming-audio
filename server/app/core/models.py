import uuid
from datetime import datetime, timezone
from sqlalchemy import (BigInteger, Boolean, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text)
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

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    style_bible: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requester: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    semantic_scene: Mapped[str] = mapped_column(String(64), nullable=False)
    play_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="Draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_tasks_project_id_status", "project_id", "status"),
        Index("ix_tasks_requester", "requester"),
        Index("ix_tasks_created_at", "created_at"),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    input_assets: Mapped[list["InputAssetRef"]] = relationship(
        "InputAssetRef", back_populates="task", cascade="all, delete-orphan"
    )
    intent_spec: Mapped["AudioIntentSpec | None"] = relationship(
        "AudioIntentSpec", back_populates="task", uselist=False
    )


class InputAssetRef(Base):
    __tablename__ = "input_asset_refs"

    input_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False
    )
    asset_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    asset_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_input_asset_refs_task_id", "task_id"),
    )

    task: Mapped["Task"] = relationship("Task", back_populates="input_assets")


class AudioIntentSpec(Base):
    __tablename__ = "audio_intent_specs"

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), unique=True, nullable=False
    )
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    semantic_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intensity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    material_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timing_points: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    loop_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    variation_count: Mapped[int] = mapped_column(SmallInteger, default=3, nullable=False)
    design_pattern: Mapped[str | None] = mapped_column(String(64), nullable=True)
    category_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("category_rules.rule_id"), nullable=True
    )
    wwise_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wwise_templates.template_id"), nullable=True
    )
    ue_binding_strategy: Mapped[str | None] = mapped_column(String(32), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    unresolved_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="intent_spec")
    category_rule: Mapped["CategoryRule | None"] = relationship("CategoryRule")
    wwise_template: Mapped["WwiseTemplate | None"] = relationship("WwiseTemplate")


class CandidateAudio(Base):
    __tablename__ = "candidate_audios"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=False
    )
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    generation_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stage: Mapped[str] = mapped_column(String(16), nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_candidate_audios_task_id", "task_id"),
        Index("ix_candidate_audios_task_id_stage", "task_id", "stage"),
    )


class QcReport(Base):
    __tablename__ = "qc_reports"

    qc_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidate_audios.candidate_id"), nullable=False
    )
    peak_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    loudness_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    spectrum_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    head_tail_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    format_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    qc_status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_qc_reports_task_id", "task_id"),
        Index("ix_qc_reports_candidate_id", "candidate_id"),
    )


class WwiseObjectManifest(Base):
    __tablename__ = "wwise_object_manifests"

    manifest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=False
    )
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    object_entries: Mapped[dict] = mapped_column(JSONB, nullable=False)
    import_status: Mapped[str] = mapped_column(String(16), nullable=False)
    build_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_wwise_object_manifests_task_id", "task_id"),
    )


class BindingManifest(Base):
    __tablename__ = "binding_manifests"

    binding_manifest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=False
    )
    version: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    bindings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    unresolved_bindings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_binding_manifests_task_id", "task_id"),
    )


class QaIssue(Base):
    __tablename__ = "qa_issues"

    qa_issue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False
    )
    timestamp_sec: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    related_actor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_skill: Mapped[str | None] = mapped_column(String(128), nullable=True)
    related_event: Mapped[str | None] = mapped_column(String(256), nullable=True)
    root_cause_guess: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_refs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolution_status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_qa_issues_task_id", "task_id"),
        Index("ix_qa_issues_project_id_issue_type", "project_id", "issue_type"),
        Index("ix_qa_issues_resolution_status", "resolution_status"),
    )


class CategoryRule(Base):
    __tablename__ = "category_rules"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_level: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_category_rules_project_id_category_is_active", "project_id", "category", "is_active"),
    )


class WwiseTemplate(Base):
    __tablename__ = "wwise_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    template_type: Mapped[str] = mapped_column(String(32), nullable=False)
    template_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    old_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_audit_logs_task_id_created_at", "task_id", "created_at"),
        Index("ix_audit_logs_project_id_action_created_at", "project_id", "action", "created_at"),
    )


class ReviewRecord(Base):
    __tablename__ = "review_records"

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=False
    )
    review_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_review_records_task_id", "task_id"),
    )


class RollbackPoint(Base):
    __tablename__ = "rollback_points"

    rollback_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=False
    )
    snapshot_type: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_rollback_points_task_id_created_at", "task_id", "created_at"),
    )
