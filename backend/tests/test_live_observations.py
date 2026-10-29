from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db import Base
from app.models import Farmer, Field, SatelliteObservation
from app.satellite.earth_engine import EarthEngineUnavailable
from app.services import claims as claims_service

BOUNDARY = {"type": "Polygon", "coordinates": [[[-101.86, 33.57], [-101.85, 33.57], [-101.85, 33.58], [-101.86, 33.58], [-101.86, 33.57]]]}


def rows():
    series = [("2025-05-01", .12, 9), ("2025-05-08", .13, 12), ("2025-05-16", .15, 8), ("2025-05-23", .18, 11), ("2025-06-02", .24, 10), ("2025-06-10", .31, 7), ("2025-06-18", .42, 6)]
    out = [{"date": d, "ndvi": n, "savi": n * .9, "cloud_coverage": c} for d, n, c in series]
    out.append({"date": "2025-05-08", "ndvi": .99, "savi": .9, "cloud_coverage": 50})  # second, cloudier scene on the same date
    return out


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([Farmer(id="F1", name="Test Farmer"), Field(id="FLD-1", farmer_id="F1", name="Test", crop_type="Cotton", boundary_geojson=BOUNDARY, latitude=33.575, longitude=-101.855, area_hectares=5)])
        session.commit()
        yield session


def live(monkeypatch, fetch):
    monkeypatch.setattr(claims_service, "get_settings", lambda: Settings(agriverify_demo_mode=False, earth_engine_project="test-project"))
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
    verification = claims_service.verify_claim(db, claim_for(db, date.today() + timedelta(days=60)))
    assert "in the future" in verification.limitations[0]
