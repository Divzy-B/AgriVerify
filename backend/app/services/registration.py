import math
import re
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog, Farmer, Field

METRES_PER_DEGREE = 111_320  # length of one degree of latitude


class DuplicateFarmer(ValueError):
    pass


def normalize_phone(raw: str) -> str:
    """Store as '+' and digits so '+91 98765 43210' and '919876543210' are the same farmer.

    Requires 8-15 digits (E.164 maximum is 15). The country code must be included: a number entered without one
    cannot be told apart from a different country's number.
    """
    digits = re.sub(r"\D", "", raw)
    if not 8 <= len(digits) <= 15:
        raise ValueError("Enter a valid phone number with 8 to 15 digits, including the country code.")
    return "+" + digits


def square_polygon(latitude: float, longitude: float, area_hectares: float) -> dict:
    """Axis-aligned square of the given area centred on a point (WGS 84 GeoJSON Polygon).

    ponytail: real plots are not squares; replace with a drawn or surveyed boundary before real use.
    """
    side = math.sqrt(area_hectares * 10_000)  # metres
    half_lat = side / 2 / METRES_PER_DEGREE
    half_lon = side / 2 / (METRES_PER_DEGREE * math.cos(math.radians(latitude)))
    west, east, south, north = longitude - half_lon, longitude + half_lon, latitude - half_lat, latitude + half_lat
    return {"type": "Polygon", "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]]}


def new_field_id(db: Session) -> str:
    while True:
        field_id = f"FLD-{secrets.token_hex(3).upper()}"
        if not db.get(Field, field_id):
            return field_id


def register_farm(db: Session, *, farmer_id: str | None, name: str | None, phone_number: str | None, preferred_language: str,
                  crop_type: str, field_name: str, latitude: float, longitude: float, area_hectares: float) -> tuple[Farmer, Field]:
    """Create a field (and a farmer, unless farmer_id names an existing one) in one transaction."""
    if farmer_id:
        farmer = db.get(Farmer, farmer_id)
        if not farmer:
            raise LookupError("Farmer not found.")
    else:
        phone = normalize_phone(phone_number or "")
        existing = db.scalar(select(Farmer).where(Farmer.phone_number == phone))
        if existing:
            raise DuplicateFarmer(f"A farmer with this phone number is already registered ({existing.name}). Choose them from the farmer list to add another field.")
        farmer = Farmer(name=(name or "").strip(), phone_number=phone, preferred_language=preferred_language)
        db.add(farmer)
        db.flush()
    field = Field(id=new_field_id(db), farmer_id=farmer.id, name=field_name.strip(), crop_type=crop_type.strip(), boundary_geojson=square_polygon(latitude, longitude, area_hectares),
                  latitude=latitude, longitude=longitude, area_hectares=area_hectares)
    db.add(field)
    db.add(AuditLog(actor_type="dashboard_user", actor_id=None, entity_type="field", entity_id=field.id, action="farm.registered", event_metadata={"farmer_id": farmer.id}))
    db.commit()
    db.refresh(farmer)
    db.refresh(field)
    return farmer, field
