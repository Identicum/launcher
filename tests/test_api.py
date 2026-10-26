from conftest import ADMIN, user

from launcher.auth import user_from_headers


def test_roles_header_is_split_on_pipe():
    parsed = user_from_headers({"IPAx-USERNAME": "jdoe", "IPAx-ROLES": " App01 | App02||App01 "}, "Admins")
    assert parsed.roles == ("App01", "App02")
    assert not parsed.is_admin
    assert user_from_headers({"IPAx-USERNAME": "jdoe", "IPAx-ROLES": "Admins"}, "Admins").is_admin
    assert user_from_headers({"IPAx-ROLES": "Admins"}, "Admins") is None


def test_health_needs_no_user(client):
    assert client.get("/health").json() == {"status": "UP"}


def test_requests_without_ipax_headers_are_rejected(client):
    assert client.get("/api/links").status_code == 401
    assert client.get("/api/me", headers={"IPAx-USERNAME": " "}).status_code == 401


def test_me(client):
    assert client.get("/api/me", headers=user("App01")).json() == {"username": "jdoe", "roles": ["App01"], "admin": False}
    assert client.get("/api/me", headers=ADMIN).json()["admin"] is True


def test_admin_endpoints_need_admin_role(client):
    for method, path in [
        ("get", "/api/admin/links"),
        ("post", "/api/admin/links"),
        ("get", "/api/admin/links/1"),
        ("put", "/api/admin/links/1"),
        ("delete", "/api/admin/links/1"),
        ("get", "/admin/data/export"),
        ("post", "/admin/data/import"),
    ]:
        assert client.request(method, path, headers=user("launcher_administrators")).status_code == 403, path


def test_logout_redirects_to_ipax(client):
    response = client.get("/logout", headers=user(), follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/private/logout"


def test_visibility(client, add_link):
    add_link("Public", "https://public", ["PUBLIC"])
    add_link("App01", "https://app01", ["App01"])
    add_link("Both", "https://both", ["App01", "App02"])
    add_link("Hidden", "https://hidden", [])

    def visible(roles):
        return [item["display"] for item in client.get("/api/links", headers=user(roles)).json()]

    assert visible("") == ["Public"]
    assert visible("App01") == ["App01", "Both", "Public"]
    assert visible("App02|Other") == ["Both", "Public"]
    assert visible("app01") == ["Public"]  # case-sensitive


def test_search_is_compatible_with_java_version(client, add_link):
    add_link("Identicum Site", "https://identicum.com", ["PUBLIC"], icon="fas fa-info", color="#666666")
    add_link("100% Other", "https://other", ["PUBLIC"])
    add_link("Secret", "https://secret", ["App01"])

    response = client.get("/links/search", params={"query": "IDENTI"}, headers=user())
    assert response.json() == [
        {"display": "Identicum Site", "color": "#666666", "icon": "fas fa-info", "target": "https://identicum.com", "type": "html"}
    ]
    assert [i["display"] for i in client.get("/links/search", params={"query": "%"}, headers=user()).json()] == ["100% Other"]
    assert client.get("/links/search", params={"query": "secret"}, headers=user()).json() == []


def test_admin_crud(client, add_link):
    created = add_link(" App ", "https://app", ["B", "A", "A", " "], icon="fas fa-cloud", color="")
    assert created["display"] == "App"
    assert created["roles"] == ["A", "B"]
    assert created["color"] is None
    assert created["type"] == "html"
    link_id = created["id"]

    response = client.put(
        f"/api/admin/links/{link_id}", headers=ADMIN, json={"display": "App 2", "target": "https://app2", "roles": ["C"]}
    )
    assert response.status_code == 200
    assert client.get(f"/api/admin/links/{link_id}", headers=ADMIN).json()["roles"] == ["C"]
    assert [i["display"] for i in client.get("/api/admin/links", headers=ADMIN).json()] == ["App 2"]

    assert client.delete(f"/api/admin/links/{link_id}", headers=ADMIN).status_code == 204
    assert client.get(f"/api/admin/links/{link_id}", headers=ADMIN).status_code == 404
    assert client.delete(f"/api/admin/links/{link_id}", headers=ADMIN).status_code == 404
    assert client.put(f"/api/admin/links/{link_id}", headers=ADMIN, json={"display": "x", "target": "y"}).status_code == 404


def test_link_validation(client):
    def create(**fields):
        return client.post("/api/admin/links", headers=ADMIN, json={"display": "x", "target": "https://x", **fields})

    assert create(target="JavaScript:alert(1)").status_code == 422
    assert create(target="data:text/html,x").status_code == 422
    assert create(display=" ").status_code == 422
    assert create(color="red;background:url(x)").status_code == 422
    assert create(target="x" * 256).status_code == 422
    assert create(color="rgb(10, 20, 30)", target="rdp://host").status_code == 201


def test_cross_site_writes_are_rejected(client):
    body = {"display": "x", "target": "https://x"}
    cross_site = {**ADMIN, "Origin": "https://evil.example", "Sec-Fetch-Site": "cross-site"}
    assert client.post("/api/admin/links", headers=cross_site, json=body).status_code == 403
    assert client.post("/api/admin/links", headers={**ADMIN, "Origin": "https://evil.example"}, json=body).status_code == 403
    same_origin = {**ADMIN, "Origin": "http://testserver", "Sec-Fetch-Site": "same-origin"}
    assert client.post("/api/admin/links", headers=same_origin, json=body).status_code == 201
