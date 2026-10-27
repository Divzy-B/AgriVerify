from fastapi.testclient import TestClient

from app.main import app


def test_seeded_dashboard_and_analysis():
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["demo_mode"] is True
        summary = client.get("/api/v1/dashboard/summary")
        assert summary.status_code == 200
        assert summary.json()["total_registered_farms"] >= 3
        analysis = client.get("/api/v1/fields/TX-001/satellite-analysis")
        assert analysis.status_code == 200
        assert analysis.json()["is_demo_data"] is True


def test_voice_simulator_calls_same_claim_workflow():
    with TestClient(app) as client:
        response = client.post("/api/v1/voice/simulator", json={"farm_id":"TX-001", "crop_type":"Cotton", "planting_date":"2025-05-25", "language":"en"})
        assert response.status_code == 200
        assert response.json()["mode"] == "SIMULATION"
        assert response.json()["verification"]["status"] == "WITHIN_TOLERANCE"


def test_webhook_idempotency():
    payload = {"execution_id":"call-unique-1", "status":"completed", "agent_data":{"language":"en"}, "transcript":[]}
    with TestClient(app) as client:
        first = client.post("/api/v1/voice/webhooks/bolna", json=payload)
        second = client.post("/api/v1/voice/webhooks/bolna", json=payload)
        assert first.status_code == second.status_code == 200
        assert first.json()["session_id"] == second.json()["session_id"]
