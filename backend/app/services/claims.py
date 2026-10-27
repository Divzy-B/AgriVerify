from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Claim, Field, SatelliteObservation, Verification
from app.verification.engine import BaselineGreenupEstimator, VerificationEngine


def create_claim(db: Session, *, farmer_id: str, field_id: str, reported_planting_date: date, idempotency_key: str | None = None) -> Claim:
    if idempotency_key:
        existing = db.scalar(select(Claim).where(Claim.idempotency_key == idempotency_key))
        if existing:
            return existing
    field = db.get(Field, field_id)
    if not field or field.farmer_id != farmer_id:
        raise ValueError("The field does not belong to the supplied farmer.")
    claim = Claim(farmer_id=farmer_id, field_id=field_id, reported_planting_date=reported_planting_date, status="PENDING", idempotency_key=idempotency_key)
    db.add(claim)
    db.flush()
    db.add(AuditLog(actor_type="voice_tool" if idempotency_key else "dashboard_user", actor_id=None, entity_type="claim", entity_id=claim.id, action="claim.created", event_metadata={"field_id": field_id}))
    db.commit()
    db.refresh(claim)
    return claim


def verify_claim(db: Session, claim: Claim) -> Verification:
    observations = list(db.scalars(select(SatelliteObservation).where(SatelliteObservation.field_id == claim.field_id).order_by(SatelliteObservation.acquisition_date)))
    estimate = BaselineGreenupEstimator().estimate(observations)
    decision = VerificationEngine().evaluate(claim.reported_planting_date, estimate)
    verification = Verification(
        claim_id=claim.id, estimated_planting_date=estimate.estimated_date, estimated_window_start=estimate.window_start,
        estimated_window_end=estimate.window_end, discrepancy_days=decision.discrepancy_days, evidence_quality=estimate.evidence_quality,
        status=decision.status, estimator_version=BaselineGreenupEstimator.version, policy_version=VerificationEngine.version,
        evidence_summary=f"{estimate.summary} {decision.summary}", limitations=estimate.limitations,
    )
    claim.status = decision.status
    db.add_all([verification, AuditLog(actor_type="system", actor_id="verification-engine", entity_type="claim", entity_id=claim.id, action="claim.verified", event_metadata={"status": decision.status, "estimator": BaselineGreenupEstimator.version})])
    db.commit()
    db.refresh(verification)
    return verification

