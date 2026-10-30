import math
import re
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import AuditLog, Farmer, Field
from app.services.registration import DuplicateFarmer, normalize_phone, register_farm, square_polygon

FARM = dict(preferred_language="en", crop_type="Cotton", field_name="North plot", latitude=33.5779, longitude=-101.8552, area_hectares=12.5)


def register(db, **overrides):
    return register_farm(db, **{**dict(farmer_id=None, name="Asha Rao", phone_number="+91 98765-43210", **FARM), **overrides})


@pytest.mark.parametrize("latitude,area", [(33.58, 1), (33.58, 42.6), (60.0, 42.6), (-20.0, 5)])
def test_square_has_the_requested_area_and_is_centred(latitude, area):
    ring = square_polygon(latitude, 10.0, area)["coordinates"][0]
    lons, lats = [p[0] for p in ring], [p[1] for p in ring]
    width = (max(lons) - min(lons)) * 111_320 * math.cos(math.radians(latitude))
    height = (max(lats) - min(lats)) * 111_320
    assert width * height == pytest.approx(area * 10_000, rel=1e-6)
    assert (max(lons) + min(lons)) / 2 == pytest.approx(10.0) and (max(lats) + min(lats)) / 2 == pytest.approx(latitude)
    assert ring[0] == ring[-1]  # closed ring


def test_phone_normalisation():
    assert normalize_phone(" +1 (806) 555-0100 ") == "+18065550100"
    assert normalize_phone("919876543210") == normalize_phone("+91 98765 43210") == "+919876543210"  # with or without the +
    for bad in ["", "123", "abc", "+1234567890123456"]:
        with pytest.raises(ValueError, match="valid phone number"):
            normalize_phone(bad)


def test_registers_new_farmer_and_field(session):
    farmer, field = register(session)
    assert farmer.phone_number == "+919876543210" and farmer.name == "Asha Rao"
    assert re.fullmatch(r"FLD-[0-9A-F]{6}", field.id) and field.farmer_id == farmer.id
    assert field.boundary_geojson["type"] == "Polygon" and field.area_hectares == 12.5
    log = session.scalar(select(AuditLog).where(AuditLog.action == "farm.registered"))
    assert log.entity_id == field.id and log.event_metadata == {"farmer_id": farmer.id}


def test_duplicate_phone_is_refused_and_creates_nothing(session):
    first, _ = register(session)
    with pytest.raises(DuplicateFarmer, match="already registered \\(Asha Rao\\)"):
        register(session, name="Someone Else", phone_number="91 (98765) 43210")  # same number, no +, different formatting
    assert len(list(session.scalars(select(Farmer)))) == 1 and len(list(session.scalars(select(Field)))) == 1


def test_second_field_for_existing_farmer(session):
    farmer, first = register(session)
    same, second = register(session, farmer_id=farmer.id, name=None, phone_number=None, field_name="South plot")
    assert same.id == farmer.id and second.id != first.id and second.farmer_id == farmer.id


def test_unknown_farmer_and_bad_phone(session):
    with pytest.raises(LookupError):
        register(session, farmer_id="nope", name=None, phone_number=None)
    with pytest.raises(ValueError, match="valid phone number"):
        register(session, phone_number="12")
    assert session.scalar(select(Field)) is None  # nothing half-created


def test_registration_endpoint():
    phone = "+1555" + str(uuid.uuid4().int)[:7]  # the API tests share one database file
    body = {**FARM, "name": "Api Farmer", "phone_number": phone}
    with TestClient(app) as client:
        created = client.post("/api/v1/registrations", json=body)
        assert created.status_code == 201
        payload = created.json()
        assert payload["demo_mode"] is True and payload["farmer"]["name"] == "Api Farmer"
        field = client.get(f"/api/v1/fields/{payload['field']['id']}").json()
        assert field["boundary_geojson"]["type"] == "Polygon"

        assert client.post("/api/v1/registrations", json=body).status_code == 409  # same phone again
        assert client.post("/api/v1/registrations", json={**FARM}).status_code == 422  # no farmer, name or phone
        assert client.post("/api/v1/registrations", json={**FARM, "farmer_id": "missing"}).status_code == 404
        assert client.post("/api/v1/registrations", json={**body, "area_hectares": 5000}).status_code == 422
