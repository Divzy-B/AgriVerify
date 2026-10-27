import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def uuid_id() -> str:
    return str(uuid.uuid4())


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Farmer(Timestamped, Base):
    __tablename__ = "farmers"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_id)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    fields: Mapped[list["Field"]] = relationship(back_populates="farmer")
    claims: Mapped[list["Claim"]] = relationship(back_populates="farmer")


class Field(Timestamped, Base):
    __tablename__ = "fields"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(80), nullable=False)
    boundary_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    area_hectares: Mapped[float] = mapped_column(Float, nullable=False)
    farmer: Mapped[Farmer] = relationship(back_populates="fields")
    claims: Mapped[list["Claim"]] = relationship(back_populates="field")
    observations: Mapped[list["SatelliteObservation"]] = relationship(back_populates="field", cascade="all, delete-orphan")


class Claim(Timestamped, Base):
    __tablename__ = "claims"
    __table_args__ = (Index("ix_claim_status_submitted", "status", "submitted_at"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_id)
    farmer_id: Mapped[str] = mapped_column(ForeignKey("farmers.id", ondelete="RESTRICT"), index=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id", ondelete="RESTRICT"), index=True)
    reported_planting_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="PENDING", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    farmer: Mapped[Farmer] = relationship(back_populates="claims")
    field: Mapped[Field] = relationship(back_populates="claims")
    verifications: Mapped[list["Verification"]] = relationship(back_populates="claim", cascade="all, delete-orphan")
    voice_sessions: Mapped[list["VoiceSession"]] = relationship(back_populates="claim")


class SatelliteObservation(Base):
    __tablename__ = "satellite_observations"
    __table_args__ = (UniqueConstraint("field_id", "acquisition_date", "data_source", name="uq_observation_date_source"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_id)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"), index=True)
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    additional_indices: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    cloud_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_flags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    source_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    field: Mapped[Field] = relationship(back_populates="observations")


class Verification(Base):
    __tablename__ = "verifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_id)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    estimated_planting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_window_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_window_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    discrepancy_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evidence_quality: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    estimator_version: Mapped[str] = mapped_column(String(80), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    claim: Mapped[Claim] = relationship(back_populates="verifications")


class VoiceSession(Base):
    __tablename__ = "voice_sessions"
    __table_args__ = (UniqueConstraint("provider", "provider_session_id", name="uq_voice_provider_session"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_id)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    farmer_id: Mapped[str | None] = mapped_column(ForeignKey("farmers.id"), nullable=True)
    claim_id: Mapped[str | None] = mapped_column(ForeignKey("claims.id"), nullable=True)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="IN_PROGRESS", nullable=False)
    transcript: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim: Mapped[Claim | None] = relationship(back_populates="voice_sessions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uuid_id)
    actor_type: Mapped[str] = mapped_column(String(60), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
