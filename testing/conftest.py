"""Test setup: isolated PostgreSQL+PostGIS database, AI providers disabled, no external network."""
import os
import sys

os.environ.setdefault("TEST_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/resq_ai_test")
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ["APP_ENV"] = "test"
os.environ["LLM_PROVIDER"] = "none"
os.environ["VISION_PROVIDER"] = "none"
os.environ["STT_PROVIDER"] = "none"
os.environ["ENABLE_OSM_LIVE_LOOKUP"] = "false"
os.environ["OSRM_BASE_URL"] = "http://127.0.0.1:9"  # closed port: routing must report UNAVAILABLE
os.environ["IOT_DEVICE_TOKEN"] = "test-device-token"
os.environ["UPLOAD_DIR"] = os.path.join(os.path.dirname(__file__), ".uploads")
os.environ["RATE_LIMIT_REPORTS_PER_MIN"] = "1000"
os.environ["TRANSLATION_PROVIDER"] = "none"  # tests patch translation explicitly; never call the internet

BACKEND = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND)

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _recreate_db():
    url = make_url(os.environ["DATABASE_URL"])
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        c.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def database():
    _recreate_db()
    from alembic import command
    from alembic.config import Config
    cfg = Config(os.path.join(BACKEND, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND, "alembic"))
    command.upgrade(cfg, "head")
    from app.db.seed_demo_data import seed
    seed()
    yield


@pytest.fixture(scope="session")
def client(database):
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "resq-demo-2026"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def auth(client):
    return {role: _login(client, f"{role.lower()}@resq.demo") for role in ("ADMIN", "HOSPITAL", "POLICE", "FIRE", "DISASTER")}


@pytest.fixture
def report(client):
    def _make(description, lat=None, lng=None, **extra):
        body = {"description": description, **extra}
        if lat is not None:
            body.update(latitude=lat, longitude=lng, location_source="DEVICE_GPS", location_accuracy_m=20)
        r = client.post("/api/v1/incidents", json=body)
        assert r.status_code == 201, r.text
        return r.json()
    return _make


@pytest.fixture
def unique_point():
    """Distinct coordinates per test so duplicate-merge logic does not join unrelated tests."""
    state = {"i": 0}
    def _next():
        state["i"] += 1
        import random
        return 12.80 + random.random() * 0.3, 77.40 + random.random() * 0.4
    return _next
