import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base


@pytest.fixture(autouse=True)
def isolate_from_dotenv(monkeypatch):
    """Tests must not depend on the developer's .env: no webhook secret, demo mode on. Tests that need otherwise set their own."""
    monkeypatch.setattr("app.main.settings.bolna_webhook_secret", "")
    monkeypatch.setattr("app.main.settings.agriverify_demo_mode", True)


@pytest.fixture
def session():
    """An empty in-memory database, isolated per test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
