import json
from pathlib import Path

import pytest
from conftest import ADMIN, user
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from launcher import dataio, db
from launcher.app import create_app

JAVA_EXPORT = (Path(__file__).parent / "fixtures" / "java-export.json").read_bytes()


def import_file(client, content, mode=None):
    data = {"mode": mode} if mode else None
    return client.post("/admin/data/import", headers=ADMIN, files={"importFile": ("data.json", content)}, data=data)


def exported(client):
    return client.get("/admin/data/export", headers=ADMIN).json()["links"]


@pytest.mark.parametrize(
    "value, expected",
    [
        ("CN=App01,OU=groups,OU=meta,DC=sherpa,DC=com", "App01"),
        ("cn=Launcher_Administrators,ou=groups", "Launcher_Administrators"),
        ("inum=1234,ou=apps,o=gluu", "1234"),
        ("PUBLIC", "PUBLIC"),
        (" App01 ", "App01"),
    ],
)
def test_role_name(value, expected):
    assert dataio.role_name(value) == expected


def test_import_java_export(client):
    response = import_file(client, JAVA_EXPORT)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "skip", "created": 3, "updated": 0, "skipped": 0, "deleted": 0}

    links = {item["display"]: item for item in exported(client)}
    assert [r["name"] for r in links["App01"]["roles"]] == ["App01", "Launcher_Administrators"]
    assert links["App01"]["icon"] == "fas fa-solid fa-cloud"
    assert links["No roles"]["roles"] == []
    assert [i["display"] for i in client.get("/api/links", headers=user("App01")).json()] == ["App01", "Identicum"]


def test_export_format_matches_java_version(client):
    import_file(client, JAVA_EXPORT)
    response = client.get("/admin/data/export", headers=ADMIN)
    assert response.headers["content-disposition"].startswith('attachment; filename="launcher-')
    links = response.json()["links"]
    assert list(links[0]) == ["id", "icon", "color", "target", "type", "display", "roles"]
    assert list(links[0]["roles"][0]) == ["id", "name"]
    assert [i["id"] for i in links] == sorted(i["id"] for i in links)


def test_round_trip(client):
    import_file(client, JAVA_EXPORT)
    first = exported(client)
    import_file(client, json.dumps({"links": first}), "replace")

    def strip_ids(links):
        return [{**i, "id": None, "roles": [r["name"] for r in i["roles"]]} for i in links]

    assert strip_ids(exported(client)) == strip_ids(first)


def test_skip_mode_keeps_existing_links(client, add_link):
    add_link("Old", "http://localhost/", ["X"])
    result = import_file(client, JAVA_EXPORT).json()
    assert (result["created"], result["skipped"]) == (2, 1)
    assert [i["display"] for i in exported(client) if i["target"] == "http://localhost/"] == ["Old"]


def test_update_mode_overwrites_existing_links(client, add_link):
    add_link("Old", "http://localhost/", ["X"])
    add_link("Untouched", "https://untouched", ["Y"])
    result = import_file(client, JAVA_EXPORT, "update").json()
    assert (result["created"], result["updated"]) == (2, 1)
    links = {i["target"]: i for i in exported(client)}
    assert links["http://localhost/"]["display"] == "App01"
    assert [r["name"] for r in links["http://localhost/"]["roles"]] == ["App01", "Launcher_Administrators"]
    assert "https://untouched" in links


def test_replace_mode_deletes_everything_first(client, add_link):
    add_link("Gone", "https://gone", ["X"])
    result = client.post("/admin/data/import?mode=replace", headers=ADMIN, files={"importFile": ("d.json", JAVA_EXPORT)}).json()
    assert (result["deleted"], result["created"]) == (1, 3)
    assert "https://gone" not in [i["target"] for i in exported(client)]


def test_raw_json_body(client):
    response = client.post(
        "/admin/data/import?mode=update", headers={**ADMIN, "Content-Type": "application/json"}, content=JAVA_EXPORT
    )
    assert response.json()["created"] == 3


def test_invalid_file_changes_nothing(client, add_link):
    add_link("Keep", "https://keep", ["X"])
    bad = json.dumps({"links": [{"display": "ok", "target": "https://ok"}, {"display": "no target"}, "nope"]})
    response = import_file(client, bad, "replace")
    assert response.status_code == 400
    errors = response.json()["errors"]
    assert len(errors) == 2 and "links[1] (no target): target" in errors[0]
    assert [i["display"] for i in exported(client)] == ["Keep"]

    assert import_file(client, b"{not json").status_code == 400
    assert import_file(client, b'{"other": []}').status_code == 400
    assert import_file(client, JAVA_EXPORT, "merge").status_code == 400


def test_initial_data_is_loaded_into_empty_database(engine, settings):
    Path(settings.initial_data_file).write_bytes(JAVA_EXPORT)
    with TestClient(create_app(settings)) as client:
        assert len(exported(client)) == 3
    # not loaded again once the database has links
    Path(settings.initial_data_file).write_text(json.dumps({"links": [{"display": "New", "target": "https://new"}]}))
    with TestClient(create_app(settings)) as client:
        assert len(exported(client)) == 3


def test_normalize_roles(engine):
    db.create_tables(engine)
    with engine.begin() as conn:
        link_id = conn.execute(db.link.insert().values(display="App", target="https://app")).inserted_primary_key[0]
        for name in ["CN=App01,OU=groups,DC=x", "App01", "PUBLIC", "CN=App02,OU=groups,DC=x"]:
            conn.execute(db.role.insert().values(name=name, link_id=link_id))

    with engine.begin() as conn:
        assert len(dataio.normalize_roles(conn, dry_run=True)) == 3
    with engine.connect() as conn:
        assert len(conn.execute(select(db.role)).all()) == 4

    with engine.begin() as conn:
        dataio.normalize_roles(conn)
    with engine.connect() as conn:
        assert sorted(conn.scalars(select(db.role.c.name))) == ["App01", "App02", "PUBLIC"]
        assert dataio.normalize_roles(conn, dry_run=True) == []


def test_works_with_schema_created_by_hibernate(engine, db_url, settings):
    """The Java version's tables (Hibernate DDL) are used without changes."""
    if db_url.get_backend_name() != "postgresql":
        pytest.skip("Hibernate DDL captured for PostgreSQL")
    with engine.begin() as conn:
        conn.execute(text(
            "create table link (id bigserial not null, color varchar(255), display varchar(255), icon varchar(255), "
            "target varchar(255), type varchar(255), primary key (id))"
        ))
        conn.execute(text("create table role (id bigserial not null, name varchar(255) not null, link_id int8, primary key (id))"))
        conn.execute(text("alter table role add constraint fk_role_link foreign key (link_id) references link"))
        conn.execute(text("insert into link (display, target, type) values ('Legacy', 'https://legacy', 'html')"))
        conn.execute(text("insert into role (name, link_id) select 'PUBLIC', id from link"))
    with TestClient(create_app(settings)) as client:
        import_file(client, JAVA_EXPORT)
        assert [i["display"] for i in client.get("/api/links", headers=user()).json()] == ["Identicum", "Legacy"]


def test_targets_are_matched_exactly(client, add_link):
    add_link("Upper", "https://APP", ["X"])
    content = json.dumps({"links": [{"display": "lower", "target": "https://app", "roles": [{"name": "PUBLIC"}]}]})
    assert import_file(client, content).json()["created"] == 1
