"""Role-based access control tests."""
from tests.conftest import auth_header


def test_customer_cannot_access_admin_dashboard(client, register):
    token = register(email="cust@example.com")
    assert client.get("/api/v1/admin/dashboard", headers=auth_header(token)).status_code == 403


def test_customer_cannot_create_category(client, register):
    token = register(email="cust2@example.com")
    resp = client.post(
        "/api/v1/service-categories",
        headers=auth_header(token),
        json={"slug": "x", "name_th": "x"},
    )
    assert resp.status_code == 403


def test_admin_can_manage_categories(client, register, db_session):
    register(email="adm@example.com")
    from app.models.user import User

    u = db_session.query(User).filter(User.email == "adm@example.com").first()
    u.role = "super_admin"
    db_session.commit()
    token = client.post("/api/v1/auth/login", json={"email": "adm@example.com", "password": "Password123"}).json()["access_token"]
    resp = client.post(
        "/api/v1/service-categories",
        headers=auth_header(token),
        json={"slug": "electrician", "name_th": "ช่างไฟฟ้า", "name_en": "Electrician"},
    )
    assert resp.status_code == 201
    listing = client.get("/api/v1/service-categories").json()
    assert any(c["slug"] == "electrician" for c in listing)
