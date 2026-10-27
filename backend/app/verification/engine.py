from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean


@dataclass(frozen=True)
class PlantingEstimate:
    estimated_date: date | None
    window_start: date | None
    window_end: date | None
    evidence_quality: str
    limitations: list[str]
    summary: str


class BaselineGreenupEstimator:
    """A transparent baseline: green-up supports a planting *window*, never an exact event."""

    version = "baseline-greenup-window-v1"

    def estimate(self, observations) -> PlantingEstimate:
        usable = [o for o in sorted(observations, key=lambda x: x.acquisition_date) if o.ndvi is not None and (o.cloud_coverage is None or o.cloud_coverage <= 35)]
        if len(usable) < 4:
            return PlantingEstimate(None, None, None, "INSUFFICIENT_EVIDENCE", ["Fewer than four usable cloud-screened observations are available."], "Satellite observation density is inadequate for a planting-window estimate.")

        baseline = mean(float(o.ndvi) for o in usable[: min(3, len(usable))])
        threshold = baseline + 0.08
        greenup = next((o for o in usable[2:] if float(o.ndvi) >= threshold), None)
        if greenup is None:
            return PlantingEstimate(None, None, None, "WEAK_EVIDENCE", ["No sustained NDVI transition exceeded the baseline threshold."], "Observations do not show a sufficiently clear green-up transition.")

        # Cotton emergence can lag planting; apply an intentionally broad 4–14 day lag.
        start = greenup.acquisition_date - timedelta(days=14)
        end = greenup.acquisition_date - timedelta(days=4)
        midpoint = start + timedelta(days=5)
        quality = "STRONG_EVIDENCE" if len(usable) >= 6 and all((o.cloud_coverage or 0) <= 20 for o in usable) else "MODERATE_EVIDENCE"
        return PlantingEstimate(
            midpoint, start, end, quality,
            ["Green-up is an indirect proxy; crop emergence, irrigation, prior vegetation, and observation cadence can shift the inferred interval."],
            f"A cloud-screened NDVI rise was observed on {greenup.acquisition_date.isoformat()}; applying the documented emergence-lag interval yields a probable planting window.",
        )


@dataclass(frozen=True)
class VerificationDecision:
    status: str
    discrepancy_days: int | None
    summary: str


class VerificationEngine:
    version = "review-policy-v1"

    def __init__(self, tolerance_days: int = 7):
        self.tolerance_days = tolerance_days

    def evaluate(self, reported: date, estimate: PlantingEstimate) -> VerificationDecision:
        if estimate.estimated_date is None or estimate.window_start is None or estimate.window_end is None:
            return VerificationDecision("INSUFFICIENT_EVIDENCE", None, "No determination is made because the available satellite observations do not support a planting-window estimate.")
        if estimate.window_start <= reported <= estimate.window_end:
            return VerificationDecision("WITHIN_TOLERANCE", 0, "The reported date falls within the satellite-derived planting window. Human review remains available.")
        nearest = estimate.window_start if reported < estimate.window_start else estimate.window_end
        gap = abs((reported - nearest).days)
        status = "WITHIN_TOLERANCE" if gap <= self.tolerance_days else "REVIEW_REQUIRED"
        return VerificationDecision(status, gap, f"The reported date is {gap} day(s) from the nearest boundary of the estimated planting interval; the illustrative review tolerance is {self.tolerance_days} day(s).")
