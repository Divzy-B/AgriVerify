import uuid
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.registration import register_farm
from app.voice.service import create_voice_claim, process_webhook

TOOLS = "/api/v1/voice/tools"


def unique_phone():
    return "+1555" + str(uuid.uuid4().int)[:7]  # the API tests share one database file


def register(client, name, phone, field_name="North plot"):
    response = client.post("/api/v1/registrations", json={"name": name, "phone_number": phone, "crop_type": "Cotton", "field_name": field_name, "latitude": 33.58, "longitude": -101.85, "area_hectares": 8})
    assert response.status_code == 201
    return response.json()


def test_lookup_farmer_by_phone_in_any_formatting():
    phone = unique_phone()
    with TestClient(app) as client:
        reg = register(client, "Asha Rao", phone)
        spoken = f"{phone[:2]} ({phone[2:5]}) {phone[5:8]}-{phone[8:]}"  # how a caller id might be formatted
        found = client.post(f"{TOOLS}/lookup-farmer", json={"phone_number": spoken})
        assert found.status_code == 200
        body = found.json()
        assert body["farmer_name"] == "Asha Rao" and body["language"] == "en"
        assert body["fields"] == [{"farm_id": reg["field"]["id"], "name": "North plot", "crop_type": "Cotton", "area_hectares": 8}]

        assert client.post(f"{TOOLS}/lookup-farmer", json={"phone_number": "+442071234567"}).status_code == 404
        assert client.post(f"{TOOLS}/lookup-farmer", json={"phone_number": "12"}).status_code == 422


def test_lookup_farmer_lists_only_that_farmers_fields():
    phone = unique_phone()
    with TestClient(app) as client:
        first = register(client, "Multi Field", phone, "First plot")
        client.post("/api/v1/registrations", json={"farmer_id": first["farmer"]["id"], "crop_type": "Maize", "field_name": "Second plot", "latitude": 33.6, "longitude": -101.9, "area_hectares": 2})
        register(client, "Someone Else", unique_phone(), "Not yours")
        fields = client.post(f"{TOOLS}/lookup-farmer", json={"phone_number": phone}).json()["fields"]
        assert sorted(f["name"] for f in fields) == ["First plot", "Second plot"]


def test_create_claim_only_for_the_callers_own_field():
    phone_a, phone_b = unique_phone(), unique_phone()
    with TestClient(app) as client:
        a, b = register(client, "Farmer A", phone_a), register(client, "Farmer B", phone_b)
        body = {"farm_id": a["field"]["id"], "crop_type": "Cotton", "planting_date": "2025-05-25", "session_id": uuid.uuid4().hex}

        assert client.post(f"{TOOLS}/create-claim", json=body).status_code == 422  # no caller number
        stolen = client.post(f"{TOOLS}/create-claim", json={**body, "phone_number": phone_b})  # B calling about A's field
        assert stolen.status_code == 422 and "not registered to the phone number" in stolen.json()["detail"]

        created = client.post(f"{TOOLS}/create-claim", json={**body, "phone_number": phone_a})
        assert created.status_code == 200
        verified = client.post(f"{TOOLS}/run-verification", json={"farm_id": a["field"]["id"], "session_id": body["session_id"]})
        assert verified.status_code == 200 and verified.json()["claim_id"] == created.json()["claim_id"]
        assert b["field"]["id"] != a["field"]["id"]


def test_create_claim_parses_spoken_dates_and_refuses_ambiguous_ones():
    phone = unique_phone()
    with TestClient(app) as client:
        field = register(client, "Date Farmer", phone)["field"]["id"]

        def claim(planting_date, session_id=uuid.uuid4):
            body = {"farm_id": field, "phone_number": phone, "planting_date": planting_date}
            if session_id: body["session_id"] = uuid.uuid4().hex
            return client.post(f"{TOOLS}/create-claim", json=body)

        assert claim("25 May 2025").status_code == 200
        assert "planting year" in claim("May 25").json()["detail"]
        assert "day/month or month/day" in claim("05/06/2025").json()["detail"]
        missing = claim("2025-05-25", session_id=None)
        assert missing.status_code == 422 and "session_id" in missing.json()["detail"]


def test_human_review_accepts_the_claim_id_in_the_query_or_the_json_body():
    phone = unique_phone()
    with TestClient(app) as client:
        field = register(client, "Review Farmer", phone)["field"]["id"]
        claim_id = client.post(f"{TOOLS}/create-claim", json={"farm_id": field, "phone_number": phone, "planting_date": "2025-05-25", "session_id": uuid.uuid4().hex}).json()["claim_id"]

        by_body = client.post(f"{TOOLS}/request-human-review", json={"claim_id": claim_id})
        assert by_body.status_code == 200 and by_body.json()["status"] == "HUMAN_REVIEW"
        assert client.post(f"{TOOLS}/request-human-review?claim_id={claim_id}").status_code == 200
        assert client.post(f"{TOOLS}/request-human-review").status_code == 422  # neither given
        assert client.post(f"{TOOLS}/request-human-review", json={"claim_id": "missing"}).status_code == 404


def _farmer_and_field(session, phone):
    return register_farm(session, farmer_id=None, name="Link Farmer", phone_number=phone, preferred_language="en", crop_type="Cotton",
                         field_name="Plot", latitude=33.5, longitude=-101.8, area_hectares=5)


def _webhook(call_id):
    return {"provider_session_id": call_id, "status": "COMPLETED", "transcript": [], "language": "en"}


def test_voice_session_is_linked_when_the_webhook_arrives_after_the_claim(session):
    farmer, field = _farmer_and_field(session, "+15550001111")
    claim = create_voice_claim(session, farm_id=field.id, crop_type="Cotton", planting_date=date.today() - timedelta(days=60), session_id="call-1", phone_number="+15550001111")
    voice = process_webhook(session, normalized=_webhook("call-1"))
    assert voice.claim_id == claim.id and voice.farmer_id == farmer.id


def test_voice_session_is_linked_when_the_claim_arrives_after_the_webhook(session):
    farmer, field = _farmer_and_field(session, "+15550002222")
    voice = process_webhook(session, normalized=_webhook("call-2"))  # e.g. a status event mid-call
    assert voice.claim_id is None
    claim = create_voice_claim(session, farm_id=field.id, crop_type="Cotton", planting_date=date.today() - timedelta(days=60), session_id="call-2", phone_number="+15550002222")
    session.refresh(voice)
    assert voice.claim_id == claim.id and voice.farmer_id == farmer.id


def test_unrelated_call_stays_unlinked(session):
    _farmer_and_field(session, "+15550003333")
    assert process_webhook(session, normalized=_webhook("call-other")).claim_id is None


@pytest.mark.parametrize("method,path,body", [
    ("post", f"{TOOLS}/lookup-farmer", {"phone_number": "+15550000000"}),
    ("post", f"{TOOLS}/lookup-field", {"farm_id": "NOPE"}),
    ("post", f"{TOOLS}/create-claim", {"farm_id": "NOPE", "planting_date": "2025-05-25", "phone_number": "+15550000000"}),
    ("post", f"{TOOLS}/run-verification", {"farm_id": "NOPE", "session_id": "none"}),
    ("post", f"{TOOLS}/request-human-review?claim_id=none", None),
    ("post", "/api/v1/voice/webhooks/bolna", {}),
])
def test_voice_endpoints_require_the_secret_when_one_is_set(monkeypatch, method, path, body):
    monkeypatch.setattr("app.main.settings.bolna_webhook_secret", "s3cret")
    with TestClient(app) as client:
        send = lambda headers: getattr(client, method)(path, json=body, headers=headers)
        assert send({}).status_code == 401
        assert send({"X-Webhook-Secret": "wrong"}).status_code == 401
        assert send({"X-Webhook-Secret": "s3cret"}).status_code != 401
