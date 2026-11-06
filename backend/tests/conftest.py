import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(BACKEND / 'test.db').as_posix()}")
os.environ["ANTHROPIC_API_KEY"] = os.environ.get("TEST_ANTHROPIC_API_KEY", "")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services.data_loader import load

    load()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db(client):
    from app.db import SessionLocal

    with SessionLocal() as session:
        yield session
