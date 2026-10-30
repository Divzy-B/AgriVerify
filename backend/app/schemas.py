from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FarmerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone_number: str | None = Field(default=None, max_length=32)
    preferred_language: Literal["en", "hi", "mr"] = "en"


class FarmerRead(ORMModel):
    id: str
    name: str
    preferred_language: str
    created_at: datetime


class FieldCreate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9-]{3,64}$")
    farmer_id: str
    name: str = Field(min_length=2, max_length=160)
    crop_type: str = Field(min_length=2, max_length=80)
    boundary_geojson: dict[str, Any]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    area_hectares: float = Field(gt=0)

    @field_validator("boundary_geojson")
    @classmethod
    def geometry_is_polygon(cls, value: dict[str, Any]) -> dict[str, Any]:
        geometry_type = value.get("type")
        coordinates = value.get("coordinates")
        if geometry_type not in {"Polygon", "MultiPolygon"} or not isinstance(coordinates, list) or not coordinates:
            raise ValueError("boundary_geojson must be a non-empty Polygon or MultiPolygon geometry")
        return value


class FieldRead(ORMModel):
    id: str
    farmer_id: str
    name: str
    crop_type: str
    boundary_geojson: dict[str, Any]
    latitude: float
    longitude: float
    area_hectares: float
    created_at: datetime


class RegistrationCreate(BaseModel):
    """Register a field from a centre point and area. Give farmer_id to add a field to an existing farmer, otherwise name and phone_number."""
    farmer_id: str | None = None
    name: str | None = Field(default=None, min_length=2, max_length=160)
    phone_number: str | None = Field(default=None, max_length=32)
    preferred_language: Literal["en", "hi", "mr"] = "en"
    crop_type: str = Field(min_length=2, max_length=80)
    field_name: str = Field(min_length=2, max_length=160)
    latitude: float = Field(ge=-85, le=85)
    longitude: float = Field(ge=-180, le=180)
    area_hectares: float = Field(gt=0, le=1000)

    @model_validator(mode="after")
    def new_farmer_needs_name_and_phone(self):
        if not self.farmer_id and not (self.name and self.phone_number):
            raise ValueError("name and phone_number are required unless farmer_id is given")
        return self


class RegistrationRead(BaseModel):
    farmer: FarmerRead
    field: FieldRead
    demo_mode: bool


class ClaimCreate(BaseModel):
    farmer_id: str
    field_id: str
    reported_planting_date: date
    idempotency_key: str | None = Field(default=None, max_length=120)


class ClaimRead(ORMModel):
    id: str
    farmer_id: str
    field_id: str
    reported_planting_date: date
    status: str
    submitted_at: datetime
    reviewer_notes: str | None = None


class ReviewerNoteUpdate(BaseModel):
    reviewer_notes: str = Field(min_length=1, max_length=4000)
    status: Literal["PENDING", "WITHIN_TOLERANCE", "REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE", "HUMAN_REVIEW"] | None = None


class ObservationRead(ORMModel):
    acquisition_date: date
    data_source: str
    ndvi: float | None
    additional_indices: dict[str, float]
    cloud_coverage: float | None
    quality_flags: list[str]
    is_demo_data: bool


class SatelliteAnalysisRead(BaseModel):
    field_id: str
    satellite_data_source: str
    analysis_mode: Literal["DEMO", "EARTH_ENGINE", "NOT_CONFIGURED"]
    acquisition_dates: list[date]
    observations: list[ObservationRead]
    estimated_planting_window: dict[str, date] | None
    estimator_version: str
    evidence_quality: str
    limitations: list[str]
    processing_status: Literal["COMPLETE", "INSUFFICIENT_EVIDENCE", "NOT_CONFIGURED"]
    is_demo_data: bool


class VerificationRead(ORMModel):
    id: str
    claim_id: str
    estimated_planting_date: date | None
    estimated_window_start: date | None
    estimated_window_end: date | None
    discrepancy_days: int | None
    evidence_quality: str
    status: str
    estimator_version: str
    policy_version: str
    evidence_summary: str
    limitations: list[str]
    generated_at: datetime


class VoiceToolInput(BaseModel):
    farm_id: str
    crop_type: str | None = None
    planting_date: date | None = None
    language: Literal["en", "hi", "mr"] = "en"
    session_id: str | None = None


class VoiceSimulationInput(BaseModel):
    farm_id: str
    crop_type: str
    planting_date: date
    language: Literal["en", "hi", "mr"] = "en"

