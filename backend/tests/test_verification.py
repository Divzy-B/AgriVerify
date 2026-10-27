from datetime import date

import pytest

from app.satellite.indices import clear_sentinel_qa60, ndvi
from app.services.date_normalization import AmbiguousDateError, normalize_confirmed_date
from app.verification.engine import BaselineGreenupEstimator, VerificationEngine


class Observation:
    def __init__(self, day, value, cloud=10):
        self.acquisition_date = date.fromisoformat(day)
        self.ndvi = value
        self.cloud_coverage = cloud


def series():
    return [Observation("2025-05-01", .12), Observation("2025-05-08", .13), Observation("2025-05-16", .15), Observation("2025-05-23", .18), Observation("2025-06-02", .24), Observation("2025-06-10", .31)]


def test_ndvi_and_cloud_masking():
    assert ndvi(.8, .2) == pytest.approx(.6)
    assert ndvi(.0, .0) is None
    assert clear_sentinel_qa60(0)
    assert not clear_sentinel_qa60(1 << 10)
    assert not clear_sentinel_qa60(1 << 11)


def test_date_normalization_requires_year():
    assert normalize_confirmed_date("May 25, 2025") == date(2025, 5, 25)
    with pytest.raises(AmbiguousDateError):
        normalize_confirmed_date("May 25")


def test_greenup_estimate_creates_interval_not_exact_planting_observation():
    estimate = BaselineGreenupEstimator().estimate(series())
    assert estimate.window_start == date(2025, 5, 19)
    assert estimate.window_end == date(2025, 5, 29)
    assert estimate.estimated_date == date(2025, 5, 24)
    assert estimate.evidence_quality == "STRONG_EVIDENCE"


def test_verification_uses_interval_and_tolerance():
    estimate = BaselineGreenupEstimator().estimate(series())
    engine = VerificationEngine(tolerance_days=7)
    assert engine.evaluate(date(2025, 5, 25), estimate).status == "WITHIN_TOLERANCE"
    assert engine.evaluate(date(2025, 6, 12), estimate).status == "REVIEW_REQUIRED"


def test_insufficient_observations_never_create_date_decision():
    estimate = BaselineGreenupEstimator().estimate(series()[:2])
    assert estimate.evidence_quality == "INSUFFICIENT_EVIDENCE"
    assert VerificationEngine().evaluate(date(2025, 5, 25), estimate).status == "INSUFFICIENT_EVIDENCE"

