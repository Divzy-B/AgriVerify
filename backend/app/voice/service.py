from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Claim, Farmer, Field, VoiceSession
from app.services.claims import create_claim, verify_claim
from app.services.registration import normalize_phone


def lookup_field(db: Session, farm_id: str) -> Field | None:
    return db.get(Field, farm_id.strip().upper())


def lookup_farmer(db: Session, phone_number: str) -> Farmer | None:
    """Find the farmer registered under the caller's phone number (any formatting). Raises ValueError for an invalid number."""
    return db.scalar(select(Farmer).where(Farmer.phone_number == normalize_phone(phone_number)))


def create_voice_claim(db: Session, *, farm_id: str, crop_type: str | None, planting_date, session_id: str | None = None, phone_number: str | None = None) -> Claim:
    field = lookup_field(db, farm_id)
    if not field:
        raise ValueError("Farm ID was not found.")
    # caller verification: when the caller's number is supplied, the field must belong to that number's farmer
    if phone_number is not None and field.farmer.phone_number != normalize_phone(phone_number):
        raise ValueError("This farm is not registered to the phone number you are calling from.")
    if crop_type and crop_type.strip().lower() != field.crop_type.lower():
        raise ValueError("The supplied crop does not match the field record; human review is required.")
    return create_claim(db, farmer_id=field.farmer_id, field_id=field.id, reported_planting_date=planting_date, idempotency_key=f"voice:{session_id}" if session_id else None)


def simulate_intake(db: Session, *, farm_id: str, crop_type: str, planting_date, language: str) -> tuple[VoiceSession, Claim, object]:
    field = lookup_field(db, farm_id)
    if not field:
        raise ValueError("Farm ID was not found.")
    session = VoiceSession(provider="simulator", provider_session_id=f"sim-{datetime.now(timezone.utc).timestamp():.0f}", farmer_id=field.farmer_id, language=language, status="COMPLETED", transcript=[
        {"speaker": "assistant", "text": "Welcome to AgriVerify. Please provide your farm ID."},
        {"speaker": "farmer", "text": farm_id},
        {"speaker": "farmer", "text": f"{crop_type}, planted {planting_date.isoformat()}"},
    ], ended_at=datetime.now(timezone.utc))
    db.add(session)
    db.flush()
    claim = create_voice_claim(db, farm_id=farm_id, crop_type=crop_type, planting_date=planting_date, session_id=session.id)
    session.claim_id = claim.id
    verification = verify_claim(db, claim)
    db.add(AuditLog(actor_type="simulator", actor_id=session.id, entity_type="voice_session", entity_id=session.id, action="voice.simulated", event_metadata={"claim_id": claim.id}))
    db.commit()
    db.refresh(session)
    return session, claim, verification


def process_webhook(db: Session, *, normalized: dict) -> VoiceSession:
    provider_session_id = normalized["provider_session_id"]
    if not provider_session_id:
        raise ValueError("Webhook payload has no execution or call identifier.")
    session = db.scalar(select(VoiceSession).where(VoiceSession.provider == "bolna", VoiceSession.provider_session_id == provider_session_id))
    if not session:
        session = VoiceSession(provider="bolna", provider_session_id=provider_session_id, language=normalized["language"])
        db.add(session)
        db.flush()  # materialize the generated ID before writing its audit entry
    session.status = normalized["status"]
    session.transcript = normalized["transcript"]
    if normalized["status"] in {"COMPLETED", "FAILED", "CANCELED"}:
        session.ended_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor_type="voice_provider", actor_id="bolna", entity_type="voice_session", entity_id=session.id, action="voice.webhook.processed", event_metadata={"provider_session_id": provider_session_id, "status": normalized["status"]}))
    db.commit()
    db.refresh(session)
    return session
