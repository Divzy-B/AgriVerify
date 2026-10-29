from dataclasses import replace
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import AuditLog, Claim, Field, SatelliteObservation, Verification
from app.satellite.earth_engine import EarthEngineUnavailable, fetch_sentinel2_observations
from app.verification.engine import BaselineGreenupEstimator, VerificationEngine

EARTH_ENGINE_SOURCE = "COPERNICUS/S2_SR_HARMONIZED"
LOOKBACK_DAYS = 30  # imagery before the reported date, to establish the pre-emergence baseline
LOOKAHEAD_DAYS = 75  # imagery after it, to catch the green-up
MIN_OBSERVATIONS = 4  # matches the estimator's minimum; fewer in the window triggers a fetch


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


def store_earth_engine_observations(db: Session, field_id: str, rows: list[dict], skip_dates: frozenset[date] = frozenset()) -> None:
    """Persist Earth Engine rows, one per date (best cloud cover wins: two scenes can share a date)."""
    best: dict[date, dict] = {}
    for item in rows:
        observed = date.fromisoformat(item["date"])
        if observed in skip_dates:
            continue
        cloud = item.get("cloud_coverage")
        if observed not in best or (cloud if cloud is not None else 100) < (best[observed].get("cloud_coverage") if best[observed].get("cloud_coverage") is not None else 100):
            best[observed] = item
    for observed, item in best.items():
        db.add(SatelliteObservation(
            field_id=field_id, acquisition_date=observed, data_source=EARTH_ENGINE_SOURCE, ndvi=item["ndvi"],
            additional_indices={"savi": item["savi"]} if item.get("savi") is not None else {},
            cloud_coverage=item.get("cloud_coverage"), quality_flags=[], source_metadata={"collection": EARTH_ENGINE_SOURCE}, is_demo_data=False,
        ))
    db.commit()


def ensure_observations(db: Session, claim: Claim) -> str | None:
    """Fetch real imagery around the reported date when the field lacks it. Returns an error message, or None.

    Demo mode never calls Earth Engine. A failed fetch is reported, never replaced with fake data.
    """
    if get_settings().agriverify_demo_mode:
        return None
    start = claim.reported_planting_date - timedelta(days=LOOKBACK_DAYS)
    end = min(claim.reported_planting_date + timedelta(days=LOOKAHEAD_DAYS), date.today())
    if start > end:
        return "The reported planting date is in the future, so no satellite imagery exists for it yet."
    have = {row.acquisition_date for row in db.scalars(select(SatelliteObservation).where(
        SatelliteObservation.field_id == claim.field_id, SatelliteObservation.is_demo_data.is_(False),
        SatelliteObservation.acquisition_date >= start, SatelliteObservation.acquisition_date <= end))}
    if len(have) >= MIN_OBSERVATIONS:
        return None
    try:
        # ponytail: refetches the whole window whenever it is thin; per-date incremental fetch if quota matters
        rows = fetch_sentinel2_observations(boundary_geojson=claim.field.boundary_geojson, start=start, end=end + timedelta(days=1), settings=get_settings())
    except EarthEngineUnavailable as exc:
        return f"Satellite data could not be retrieved: {exc}"
    store_earth_engine_observations(db, claim.field_id, rows, skip_dates=frozenset(have))
    return None


def verify_claim(db: Session, claim: Claim) -> Verification:
    fetch_error = ensure_observations(db, claim)
    observations = list(db.scalars(select(SatelliteObservation).where(SatelliteObservation.field_id == claim.field_id).order_by(SatelliteObservation.acquisition_date)))
    estimate = BaselineGreenupEstimator().estimate(observations)
    if fetch_error:
        estimate = replace(estimate, limitations=[fetch_error, *estimate.limitations])
    decision = VerificationEngine(tolerance_days=get_settings().verification_tolerance_days).evaluate(claim.reported_planting_date, estimate)
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
