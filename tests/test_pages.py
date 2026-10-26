from conftest import ADMIN, user
from sqlalchemy import insert

from launcher import db

HTML = {"Accept": "text/html"}


def test_launcher_shows_only_visible_links(client, add_link):
    add_link("Public <b>App</b>", "https://public", ["PUBLIC"], icon="fas fa-info", color="#ED5151")
    add_link("Secret", "https://secret", ["App01"])
    page = client.get("/", headers={**HTML, **user()})
    assert page.status_code == 200
    assert "Public &lt;b&gt;App&lt;/b&gt;" in page.text
    assert 'href="https://public"' in page.text
    assert "--tile-color: #ED5151" in page.text
    assert "Secret" not in page.text
    assert "Manage links" not in page.text
    assert "Secret" in client.get("/menu", headers={**HTML, **user("App01")}).text


def test_launcher_neutralizes_unsafe_legacy_values(client, engine):
    with engine.begin() as conn:
        link_id = conn.execute(
            insert(db.link).values(display="Legacy", target="javascript:alert(1)", color="red;background:url(x)")
        ).inserted_primary_key[0]
        conn.execute(insert(db.role).values(name="PUBLIC", link_id=link_id))
    page = client.get("/", headers={**HTML, **user()}).text
    assert 'href="#"' in page and 'href="javascript:' not in page
    assert "--tile-color: var(--tile-default)" in page


def test_empty_launcher(client):
    page = client.get("/", headers={**HTML, **user()}).text
    assert "No applications yet" in page
    assert "Add links" in client.get("/", headers={**HTML, **ADMIN}).text


def test_admin_page(client):
    page = client.get("/admin", headers={**HTML, **ADMIN})
    assert page.status_code == 200
    assert "Manage links" in page.text
    assert 'data-public-role="PUBLIC"' in page.text
    assert client.get("/admin/links", headers=ADMIN, follow_redirects=False).headers["location"] == "/admin"


def test_html_error_pages(client):
    denied = client.get("/admin", headers={**HTML, **user("App01")})
    assert denied.status_code == 403 and "Access denied" in denied.text
    anonymous = client.get("/", headers=HTML)
    assert anonymous.status_code == 401 and "through IPAx" in anonymous.text
    missing = client.get("/nope", headers={**HTML, **user()})
    assert missing.status_code == 404 and "Page not found" in missing.text
    # APIs keep answering JSON
    assert client.get("/api/links", headers=HTML).json()["detail"].startswith("Missing IPAx-USERNAME")


def test_security_headers_and_static_files(client):
    page = client.get("/", headers={**HTML, **user()})
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert page.headers["x-content-type-options"] == "nosniff"
    for path in ["app.css", "admin.js", "vendor/bootstrap/bootstrap.min.css", "vendor/fontawesome/icons.json"]:
        assert client.get(f"/static/{path}").status_code == 200, path
    assert "gzip" in client.get("/static/app.css", headers={"Accept-Encoding": "gzip"}).headers["content-encoding"]
