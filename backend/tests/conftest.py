import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base


@pytest.fixture(autouse=True)
def no_webhook_secret(monkeypatch):
    """Tests must not depend on the developer's .env; tests that need a secret set their own."""
    monkeypatch.setattr("app.main.settings.bolna_webhook_secret", "")


@pytest.fixture
def session():
    """An empty in-memory database, isolated per test."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
