from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Claim, Farmer, Field, SatelliteObservation


def _square(lon: float, lat: float, size: float = 0.006) -> dict:
    return {"type": "Polygon", "coordinates": [[[lon-size, lat-size], [lon+size, lat-size], [lon+size, lat+size], [lon-size, lat+size], [lon-size, lat-size]]]}


DEMO_FIELDS = [
    {"id": "TX-001", "farmer": ("F-ALMA", "Alma Torres", "en"), "name": "Torres Cotton South", "lat": 33.5779, "lon": -101.8552, "area": 42.6, "claim_date": date(2025, 5, 25), "ndvi": [("2025-05-01", .12, 9), ("2025-05-08", .13, 12), ("2025-05-16", .15, 8), ("2025-05-23", .18, 11), ("2025-06-02", .24, 10), ("2025-06-10", .31, 7), ("2025-06-18", .42, 6)]},
    {"id": "TX-002", "farmer": ("F-NORA", "Nora Bennett", "en"), "name": "Bennett Cotton East", "lat": 32.7767, "lon": -96.7970, "area": 31.2, "claim_date": date(2025, 7, 4), "ndvi": [("2025-05-01", .11, 7), ("2025-05-09", .12, 10), ("2025-05-17", .14, 9), ("2025-05-25", .17, 12), ("2025-06-03", .26, 10), ("2025-06-11", .34, 9), ("2025-06-19", .43, 8)]},
    {"id": "TX-003", "farmer": ("F-DEV", "Dev Shah", "hi"), "name": "Shah Cotton North", "lat": 35.2220, "lon": -101.8313, "area": 18.5, "claim_date": date(2025, 5, 31), "ndvi": [("2025-06-04", .17, 58)]},
]


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(Field.id).limit(1)):
        return
    for item in DEMO_FIELDS:
        farmer_id, farmer_name, language = item["farmer"]
        farmer = Farmer(id=farmer_id, name=farmer_name, phone_number=None, preferred_language=language)
        field = Field(id=item["id"], farmer_id=farmer_id, name=item["name"], crop_type="Cotton", boundary_geojson=_square(item["lon"], item["lat"]), latitude=item["lat"], longitude=item["lon"], area_hectares=item["area"])
        db.add_all([farmer, field])
        for observed, ndvi, cloud in item["ndvi"]:
            db.add(SatelliteObservation(
                field_id=item["id"], acquisition_date=date.fromisoformat(observed), data_source="SYNTHETIC_DEMO_SERIES",
                ndvi=ndvi, additional_indices={"savi": round(ndvi * 0.92, 3)}, cloud_coverage=cloud,
                quality_flags=["SYNTHETIC_DEMO"], source_metadata={"provenance": "AgriVerify offline demonstration dataset"}, is_demo_data=True,
            ))
        db.add(Claim(id=f"CLM-{item['id']}", farmer_id=farmer_id, field_id=item["id"], reported_planting_date=item["claim_date"], status="PENDING", idempotency_key=f"seed-{item['id']}"))
    db.commit()

