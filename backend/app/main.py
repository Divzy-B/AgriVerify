import logging
import secrets
from contextlib import asynccontextmanager
from datetime import date
from io import BytesIO

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db import Base, SessionLocal, engine, get_db
from app.models import Claim, Farmer, Field, SatelliteObservation, Verification, VoiceSession
from app.satellite.earth_engine import EarthEngineUnavailable, fetch_sentinel2_observations
from app.schemas import (ClaimCreate, ClaimRead, FarmerCreate, FarmerRead, FieldCreate, FieldRead, RegistrationCreate, RegistrationRead, ReviewerNoteUpdate, SatelliteAnalysisRead, VerificationRead, VoiceFarmerLookup, VoiceHumanReview, VoiceSimulationInput, VoiceToolInput)
from app.services.claims import create_claim, store_earth_engine_observations, verify_claim
from app.services.data import seed_demo_data
from app.services.date_normalization import AmbiguousDateError, normalize_confirmed_date
from app.services.registration import DuplicateFarmer, register_farm
from app.services.reports import build_verification_pdf
from app.verification.engine import BaselineGreenupEstimator
from app.voice.providers.bolna import BolnaVoiceProvider
from app.voice.service import create_voice_claim, lookup_farmer, lookup_field, process_webhook, simulate_intake

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("agriverify")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if settings.agriverify_demo_mode:
            seed_demo_data(db)
            for claim in db.scalars(select(Claim).where(Claim.status == "PENDING")).all():
                verify_claim(db, claim)
    yield


app = FastAPI(title="AgriVerify API", version="0.1.0", description="Voice-powered crop intelligence and verification API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False, allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type", "X-API-Key", "X-Webhook-Secret", "Idempotency-Key"])


def dashboard_auth(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid dashboard API key required.")


def voice_tool_auth(x_webhook_secret: str | None = Header(default=None)) -> None:
    """Guards the voice tool endpoints and the webhook. Open only when no secret is configured (local development)."""
    if settings.bolna_webhook_secret and not secrets.compare_digest(x_webhook_secret or "", settings.bolna_webhook_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Webhook secret mismatch.")


def get_claim_or_404(db: Session, claim_id: str) -> Claim:
    claim = db.scalar(select(Claim).options(joinedload(Claim.field), joinedload(Claim.verifications)).where(Claim.id == claim_id))
    if not claim:
        raise HTTPException(404, "Claim not found.")
    return claim


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "demo_mode": settings.agriverify_demo_mode, "voice_provider": settings.voice_provider, "voice_configured": settings.bolna_configured, "earth_engine_configured": settings.earth_engine_configured}


@app.get("/api/v1/dashboard/summary", dependencies=[Depends(dashboard_auth)])
def dashboard_summary(db: Session = Depends(get_db)):
    rows = list(db.scalars(select(Claim)))
    counts = {key: sum(1 for row in rows if row.status == key) for key in ("WITHIN_TOLERANCE", "REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE", "PENDING", "HUMAN_REVIEW")}
    recent = list(db.scalars(select(Claim).order_by(Claim.submitted_at.desc()).limit(6)))
    voices = db.scalar(select(func.count()).select_from(VoiceSession)) or 0
    return {"total_registered_farms": db.scalar(select(func.count()).select_from(Field)) or 0, "total_submitted_claims": len(rows), "claims_within_review_tolerance": counts["WITHIN_TOLERANCE"], "claims_requiring_investigation": counts["REVIEW_REQUIRED"], "claims_insufficient_satellite_evidence": counts["INSUFFICIENT_EVIDENCE"], "pending_human_reviews": counts["PENDING"] + counts["HUMAN_REVIEW"] + counts["REVIEW_REQUIRED"], "voice_interactions": voices, "status_distribution": counts, "recent_claims": [{"id": c.id, "field_id": c.field_id, "status": c.status, "submitted_at": c.submitted_at} for c in recent]}


@app.get("/api/v1/farmers", response_model=list[FarmerRead], dependencies=[Depends(dashboard_auth)])
def list_farmers(db: Session = Depends(get_db)):
    return list(db.scalars(select(Farmer).order_by(Farmer.name)))


@app.post("/api/v1/farmers", response_model=FarmerRead, status_code=201, dependencies=[Depends(dashboard_auth)])
def add_farmer(payload: FarmerCreate, db: Session = Depends(get_db)):
    farmer = Farmer(**payload.model_dump())
    db.add(farmer); db.commit(); db.refresh(farmer)
    return farmer


@app.get("/api/v1/farmers/{farmer_id}", response_model=FarmerRead, dependencies=[Depends(dashboard_auth)])
def get_farmer(farmer_id: str, db: Session = Depends(get_db)):
    farmer = db.get(Farmer, farmer_id)
    if not farmer: raise HTTPException(404, "Farmer not found.")
    return farmer


@app.get("/api/v1/fields", response_model=list[FieldRead], dependencies=[Depends(dashboard_auth)])
def list_fields(search: str | None = None, db: Session = Depends(get_db)):
    query = select(Field).order_by(Field.id)
    if search: query = query.where(Field.id.contains(search.upper()) | Field.name.ilike(f"%{search}%"))
    return list(db.scalars(query))


@app.post("/api/v1/fields", response_model=FieldRead, status_code=201, dependencies=[Depends(dashboard_auth)])
def add_field(payload: FieldCreate, db: Session = Depends(get_db)):
    if not db.get(Farmer, payload.farmer_id): raise HTTPException(404, "Farmer not found.")
    field = Field(**payload.model_dump()); db.add(field); db.commit(); db.refresh(field)
    return field


@app.get("/api/v1/fields/{field_id}", response_model=FieldRead, dependencies=[Depends(dashboard_auth)])
def get_field(field_id: str, db: Session = Depends(get_db)):
    field = db.get(Field, field_id.upper())
    if not field: raise HTTPException(404, "Field not found.")
    return field


@app.get("/api/v1/fields/{field_id}/satellite-analysis", response_model=SatelliteAnalysisRead, dependencies=[Depends(dashboard_auth)])
def satellite_analysis(field_id: str, db: Session = Depends(get_db)):
    field = db.get(Field, field_id.upper())
    if not field: raise HTTPException(404, "Field not found.")
    observations = list(db.scalars(select(SatelliteObservation).where(SatelliteObservation.field_id == field.id).order_by(SatelliteObservation.acquisition_date)))
    if not observations and not settings.agriverify_demo_mode:
        try:
            real = fetch_sentinel2_observations(boundary_geojson=field.boundary_geojson, start=date.today().replace(month=1, day=1), end=date.today(), settings=settings)
            store_earth_engine_observations(db, field.id, real)
            observations = list(db.scalars(select(SatelliteObservation).where(SatelliteObservation.field_id == field.id).order_by(SatelliteObservation.acquisition_date)))
        except EarthEngineUnavailable as exc:
            return SatelliteAnalysisRead(field_id=field.id, satellite_data_source="COPERNICUS/S2_SR_HARMONIZED", analysis_mode="NOT_CONFIGURED", acquisition_dates=[], observations=[], estimated_planting_window=None, estimator_version=BaselineGreenupEstimator.version, evidence_quality="INSUFFICIENT_EVIDENCE", limitations=[str(exc)], processing_status="NOT_CONFIGURED", is_demo_data=False)
    estimate = BaselineGreenupEstimator().estimate(observations)
    demo = bool(observations and all(item.is_demo_data for item in observations))
    return SatelliteAnalysisRead(field_id=field.id, satellite_data_source="SYNTHETIC_DEMO_SERIES" if demo else "COPERNICUS/S2_SR_HARMONIZED", analysis_mode="DEMO" if demo else "EARTH_ENGINE", acquisition_dates=[item.acquisition_date for item in observations], observations=observations, estimated_planting_window={"start": estimate.window_start, "end": estimate.window_end} if estimate.window_start else None, estimator_version=BaselineGreenupEstimator.version, evidence_quality=estimate.evidence_quality, limitations=estimate.limitations, processing_status="COMPLETE" if estimate.estimated_date else "INSUFFICIENT_EVIDENCE", is_demo_data=demo)


@app.post("/api/v1/registrations", response_model=RegistrationRead, status_code=201, dependencies=[Depends(dashboard_auth)])
def register_farm_and_field(payload: RegistrationCreate, db: Session = Depends(get_db)):
    try:
        farmer, field = register_farm(db, **payload.model_dump())
    except DuplicateFarmer as exc: raise HTTPException(409, str(exc)) from exc
    except LookupError as exc: raise HTTPException(404, str(exc)) from exc
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    return RegistrationRead(farmer=farmer, field=field, demo_mode=settings.agriverify_demo_mode)


@app.get("/api/v1/claims", response_model=list[ClaimRead], dependencies=[Depends(dashboard_auth)])
def list_claims(q: str | None = None, status_filter: str | None = Query(default=None, alias="status"), limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    query = select(Claim).order_by(Claim.submitted_at.desc()).limit(limit).offset(offset)
    if status_filter: query = query.where(Claim.status == status_filter)
    if q: query = query.where(Claim.field_id.contains(q.upper()) | Claim.farmer_id.contains(q.upper()))
    return list(db.scalars(query))


@app.post("/api/v1/claims", response_model=ClaimRead, status_code=201, dependencies=[Depends(dashboard_auth)])
def add_claim(payload: ClaimCreate, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db)):
    try:
        return create_claim(db, **payload.model_dump(exclude={"idempotency_key"}), idempotency_key=payload.idempotency_key or idempotency_key)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc


@app.get("/api/v1/claims/{claim_id}", response_model=ClaimRead, dependencies=[Depends(dashboard_auth)])
def get_claim(claim_id: str, db: Session = Depends(get_db)):
    return get_claim_or_404(db, claim_id)


@app.post("/api/v1/claims/{claim_id}/verify", response_model=VerificationRead, dependencies=[Depends(dashboard_auth)])
def run_verification(claim_id: str, db: Session = Depends(get_db)):
    return verify_claim(db, get_claim_or_404(db, claim_id))


@app.patch("/api/v1/claims/{claim_id}/review", response_model=ClaimRead, dependencies=[Depends(dashboard_auth)])
def add_reviewer_note(claim_id: str, payload: ReviewerNoteUpdate, db: Session = Depends(get_db)):
    claim = get_claim_or_404(db, claim_id); claim.reviewer_notes = payload.reviewer_notes
    if payload.status: claim.status = payload.status
    db.commit(); db.refresh(claim); return claim


@app.get("/api/v1/verifications/{verification_id}", response_model=VerificationRead, dependencies=[Depends(dashboard_auth)])
def get_verification(verification_id: str, db: Session = Depends(get_db)):
    item = db.get(Verification, verification_id)
    if not item: raise HTTPException(404, "Verification not found.")
    return item


@app.get("/api/v1/voice/sessions", dependencies=[Depends(dashboard_auth)])
def list_voice_sessions(db: Session = Depends(get_db)):
    return list(db.scalars(select(VoiceSession).order_by(VoiceSession.started_at.desc())))


@app.get("/api/v1/voice/sessions/{session_id}", dependencies=[Depends(dashboard_auth)])
def get_voice_session(session_id: str, db: Session = Depends(get_db)):
    item = db.get(VoiceSession, session_id)
    if not item: raise HTTPException(404, "Voice session not found.")
    return item


@app.post("/api/v1/voice/tools/lookup-farmer", dependencies=[Depends(voice_tool_auth)])
def voice_lookup_farmer(payload: VoiceFarmerLookup, db: Session = Depends(get_db)):
    try:
        farmer = lookup_farmer(db, payload.phone_number)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    if not farmer: raise HTTPException(404, "No farmer is registered with this phone number.")
    fields = [{"farm_id": f.id, "name": f.name, "crop_type": f.crop_type, "area_hectares": f.area_hectares} for f in farmer.fields]
    return {"farmer_name": farmer.name, "language": farmer.preferred_language, "fields": fields,
            "message": "Confirm the caller's name. With one field, confirm it; with several, ask which one the claim is for." if fields else "This farmer has no registered field. Offer a human reviewer."}


@app.post("/api/v1/voice/tools/lookup-field", dependencies=[Depends(voice_tool_auth)])
def voice_lookup_field(payload: VoiceToolInput, db: Session = Depends(get_db)):
    field = lookup_field(db, payload.farm_id)
    if not field: raise HTTPException(404, "Farm ID not found.")
    return {"farm_id": field.id, "crop_type": field.crop_type, "farmer_id": field.farmer_id, "message": "Field located. Confirm the details with the caller."}


@app.post("/api/v1/voice/tools/create-claim", dependencies=[Depends(voice_tool_auth)])
def voice_create_claim(payload: VoiceToolInput, db: Session = Depends(get_db)):
    if not payload.planting_date: raise HTTPException(422, "planting_date is required after caller confirmation.")
    if not payload.phone_number: raise HTTPException(422, "phone_number (the number the caller is calling from) is required.")
    if not payload.session_id: raise HTTPException(422, "session_id is required so a repeated request does not create a second claim.")
    try:
        planting_date = normalize_confirmed_date(payload.planting_date)
    except AmbiguousDateError as exc: raise HTTPException(422, str(exc)) from exc
    try:
        claim = create_voice_claim(db, farm_id=payload.farm_id, crop_type=payload.crop_type, planting_date=planting_date, session_id=payload.session_id, phone_number=payload.phone_number)
        return {"claim_id": claim.id, "status": claim.status}
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/voice/tools/run-verification", dependencies=[Depends(voice_tool_auth)])
def voice_run_verification(payload: VoiceToolInput, db: Session = Depends(get_db)):
    if not payload.session_id: raise HTTPException(422, "session_id must be supplied for idempotent voice verification.")
    claim = db.scalar(select(Claim).where(Claim.idempotency_key == f"voice:{payload.session_id}"))
    if not claim: raise HTTPException(404, "No claim exists for this voice session.")
    verification = verify_claim(db, claim)
    return {"claim_id": claim.id, "verification_id": verification.id, "status": verification.status, "evidence_quality": verification.evidence_quality, "message": verification.evidence_summary}


@app.post("/api/v1/voice/simulator", dependencies=[Depends(dashboard_auth)])
def run_voice_simulator(payload: VoiceSimulationInput, db: Session = Depends(get_db)):
    try:
        session, claim, verification = simulate_intake(db, **payload.model_dump())
        return {"mode": "SIMULATION", "session_id": session.id, "claim_id": claim.id, "verification": VerificationRead.model_validate(verification)}
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc


@app.post("/api/v1/voice/webhooks/{provider}", dependencies=[Depends(voice_tool_auth)])
async def voice_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    if provider != "bolna": raise HTTPException(404, "Voice provider not supported.")
    payload = await request.json()
    try:
        session = process_webhook(db, normalized=BolnaVoiceProvider(settings).normalize_event(payload))
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    return {"accepted": True, "session_id": session.id}


@app.post("/api/v1/voice/tools/request-human-review", dependencies=[Depends(voice_tool_auth)])
def request_human_review(claim_id: str | None = None, body: VoiceHumanReview | None = None, db: Session = Depends(get_db)):
    claim_id = claim_id or (body.claim_id if body else None)  # query string or JSON body, whichever the tool can send
    if not claim_id: raise HTTPException(422, "claim_id is required (query parameter or JSON body).")
    claim = get_claim_or_404(db, claim_id); claim.status = "HUMAN_REVIEW"; db.commit()
    return {"claim_id": claim.id, "status": claim.status, "message": "A human insurance reviewer has been requested."}


@app.get("/api/v1/reports/{claim_id}/pdf", dependencies=[Depends(dashboard_auth)])
def verification_report(claim_id: str, db: Session = Depends(get_db)):
    claim = get_claim_or_404(db, claim_id)
    verification = db.scalar(select(Verification).where(Verification.claim_id == claim.id).order_by(Verification.generated_at.desc()))
    if not verification: raise HTTPException(409, "Verify this claim before generating a report.")
    observations = list(db.scalars(select(SatelliteObservation).where(SatelliteObservation.field_id == claim.field_id).order_by(SatelliteObservation.acquisition_date)))
    pdf = build_verification_pdf(claim=claim, verification=verification, observations=observations)
    return StreamingResponse(BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="agriverify-{claim.id}.pdf"'})
