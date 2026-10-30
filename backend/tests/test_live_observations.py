from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.models import Claim, Farmer, Field, SatelliteObservation
from app.satellite.earth_engine import EarthEngineUnavailable
from app.services import claims as claims_service

BOUNDARY = {"type": "Polygon", "coordinates": [[[-101.86, 33.57], [-101.85, 33.57], [-101.85, 33.58], [-101.86, 33.58], [-101.86, 33.57]]]}


def rows():
    series = [("2025-05-01", .12, 9), ("2025-05-08", .13, 12), ("2025-05-16", .15, 8), ("2025-05-23", .18, 11), ("2025-06-02", .24, 10), ("2025-06-10", .31, 7), ("2025-06-18", .42, 6)]
    out = [{"date": d, "ndvi": n, "savi": n * .9, "cloud_coverage": c} for d, n, c in series]
    out.append({"date": "2025-05-08", "ndvi": .99, "savi": .9, "cloud_coverage": 50})  # second, cloudier scene on the same date
    return out


@pytest.fixture
def db(session):
    session.add_all([Farmer(id="F1", name="Test Farmer"), Field(id="FLD-1", farmer_id="F1", name="Test", crop_type="Cotton", boundary_geojson=BOUNDARY, latitude=33.575, longitude=-101.855, area_hectares=5)])
    session.commit()
    return session


def live(monkeypatch, fetch, **overrides):
    # a huge age limit by default so the fixed 2025 dates below do not age out; the age test sets its own
    settings = Settings(agriverify_demo_mode=False, earth_engine_project="test-project", **{"max_planting_age_days": 100_000, **overrides})
    monkeypatch.setattr(claims_service, "get_settings", lambda: settings)
    monkeypatch.setattr(claims_service, "fetch_sentinel2_observations", fetch)


def claim_for(db, reported):
    return claims_service.create_claim(db, farmer_id="F1", field_id="FLD-1", reported_planting_date=reported)


def test_verify_fetches_window_and_stores_one_row_per_date(db, monkeypatch):
    calls = []

    def fetch(**kwargs):
        calls.append(kwargs)
        return rows()

    live(monkeypatch, fetch)
    claim = claim_for(db, date(2025, 5, 25))
    verification = claims_service.verify_claim(db, claim)

    assert verification.status == "WITHIN_TOLERANCE"
    assert len(calls) == 1
    assert calls[0]["start"] == date(2025, 4, 25) and calls[0]["end"] == date(2025, 8, 9)  # -30 / +75 days (Aug 8), end exclusive
    stored = list(db.scalars(select(SatelliteObservation)))
    assert len(stored) == 7  # duplicate-date scene collapsed
    assert all(not o.is_demo_data for o in stored)
    assert next(o for o in stored if o.acquisition_date == date(2025, 5, 8)).ndvi == .13  # the clearer scene won

    claims_service.verify_claim(db, claim)
    assert len(calls) == 1  # enough observations now, no second fetch


def test_tolerance_setting_is_used(db, monkeypatch):
    # estimated window is May 19-29, so June 1 is 3 days outside it
    live(monkeypatch, lambda **kwargs: rows(), verification_tolerance_days=2)
    claim = claim_for(db, date(2025, 6, 1))
    strict = claims_service.verify_claim(db, claim)
    assert (strict.status, strict.discrepancy_days) == ("REVIEW_REQUIRED", 3)

    live(monkeypatch, lambda **kwargs: rows(), verification_tolerance_days=7)
    assert claims_service.verify_claim(db, claim).status == "WITHIN_TOLERANCE"


def test_future_planting_date_is_rejected(db, monkeypatch):
    live(monkeypatch, None)
    with pytest.raises(ValueError, match="in the future"):
        claim_for(db, date.today() + timedelta(days=1))


def test_old_planting_date_is_rejected_unless_limit_allows_it(db, monkeypatch):
    old = date.today() - timedelta(days=600)
    live(monkeypatch, None, max_planting_age_days=548)  # the default limit
    with pytest.raises(ValueError, match="more than 548 days ago"):
        claim_for(db, old)
    live(monkeypatch, None, max_planting_age_days=1000)
    assert claim_for(db, old).reported_planting_date == old


def test_second_claim_for_same_field_and_year_is_rejected(db, monkeypatch):
    live(monkeypatch, None)
    first = claim_for(db, date(2025, 5, 25))
    with pytest.raises(ValueError, match=f"already has a claim \\({first.id}\\)"):
        claim_for(db, date(2025, 6, 10))
    assert claim_for(db, date(2026, 3, 1)).reported_planting_date == date(2026, 3, 1)  # a different year is a different season


def test_retried_voice_claim_returns_same_claim_not_a_duplicate_error(db, monkeypatch):
    live(monkeypatch, None)
    args = dict(farmer_id="F1", field_id="FLD-1", reported_planting_date=date(2025, 5, 25), idempotency_key="voice:abc")
    assert claims_service.create_claim(db, **args).id == claims_service.create_claim(db, **args).id


def test_demo_mode_allows_old_and_repeated_claims(db, monkeypatch):
    monkeypatch.setattr(claims_service, "get_settings", lambda: Settings(agriverify_demo_mode=True))
    claim_for(db, date(2020, 1, 1))
    claim_for(db, date(2020, 1, 1))  # demos re-run the same intake
    with pytest.raises(ValueError, match="in the future"):  # but the future-date rule always applies
        claim_for(db, date.today() + timedelta(days=1))


def test_fetch_failure_is_reported_not_faked(db, monkeypatch):
    def fetch(**kwargs):
        raise EarthEngineUnavailable("boom")

    live(monkeypatch, fetch)
    verification = claims_service.verify_claim(db, claim_for(db, date(2025, 5, 25)))

    assert verification.status == "INSUFFICIENT_EVIDENCE"
    assert verification.limitations[0] == "Satellite data could not be retrieved: boom"
    assert db.scalar(select(SatelliteObservation)) is None


def test_demo_mode_never_calls_earth_engine(db, monkeypatch):
    def fetch(**kwargs):
        raise AssertionError("Earth Engine must not be called in demo mode")

    monkeypatch.setattr(claims_service, "get_settings", lambda: Settings(agriverify_demo_mode=True))
    monkeypatch.setattr(claims_service, "fetch_sentinel2_observations", fetch)
    assert claims_service.verify_claim(db, claim_for(db, date(2025, 5, 25))).status == "INSUFFICIENT_EVIDENCE"


def test_future_planting_date_is_explained_without_fetching(db, monkeypatch):
    def fetch(**kwargs):
        raise AssertionError("nothing to fetch for a future date")

    live(monkeypatch, fetch)
    # create_claim now rejects future dates, so insert directly to exercise verify_claim's own guard (e.g. legacy rows)
    claim = Claim(farmer_id="F1", field_id="FLD-1", reported_planting_date=date.today() + timedelta(days=60), status="PENDING")
    db.add(claim)
    db.commit()
    verification = claims_service.verify_claim(db, claim)
    assert "in the future" in verification.limitations[0]
