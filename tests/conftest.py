"""Tests run on SQLite by default. Set TEST_DB_URL to run them against another database, e.g.
TEST_DB_URL=postgresql+psycopg://launcherusr:launcherpwd@localhost:5432/launcherdb
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from launcher import db
from launcher.app import create_app
from launcher.config import Settings

ADMIN = {"IPAx-USERNAME": "admin", "IPAx-ROLES": "Launcher_Administrators|App01"}


def user(roles: str = "", username: str = "jdoe") -> dict:
    return {"IPAx-USERNAME": username, "IPAx-ROLES": roles}


@pytest.fixture
def db_url(tmp_path):
    return make_url(os.environ.get("TEST_DB_URL") or f"sqlite:///{tmp_path}/launcher.db")


@pytest.fixture
def engine(db_url):
    engine = db.make_engine(db_url)
    db.metadata.drop_all(engine)
    yield engine
    db.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def settings(db_url, tmp_path):
    return Settings(db_url=db_url, admin_role="Launcher_Administrators", initial_data_file=str(tmp_path / "data.json"))


@pytest.fixture
def client(engine, settings):
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def add_link(client):
    def add(display, target, roles, **fields):
        response = client.post(
            "/api/admin/links", headers=ADMIN, json={"display": display, "target": target, "roles": roles, **fields}
        )
        assert response.status_code == 201, response.text
        return response.json()

    return add
