"""Technician onboarding: document upload, apply, admin review."""
from tests.conftest import auth_header

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def _make_admin(db_session, email):
    from app.models.user import User

    u = db_session.query(User).filter(User.email == email).first()
    u.role = "super_admin"
    db_session.commit()
    return u


def _seed_category(db_session, slug="electrician"):
    from app.models.catalog import ServiceCategory

    c = ServiceCategory(slug=slug, name_th="ช่างไฟฟ้า", name_en="Electrician", sort_order=1)
    db_session.add(c)
    db_session.commit()
    return c.id


def test_upload_returns_url(client, register):
    token = register(email="up@example.com")
    resp = client.post(
        "/api/v1/uploads",
        headers=auth_header(token),
        files={"file": ("id.png", PNG, "image/png")},
    )
    assert resp.status_code == 201, resp.text
    assert "/media/" in resp.json()["url"]


def test_upload_rejects_bad_type(client, register):
    token = register(email="up2@example.com")
    resp = client.post(
        "/api/v1/uploads",
        headers=auth_header(token),
        files={"file": ("x.exe", b"MZ", "application/x-msdownload")},
    )
    assert resp.status_code == 400


def test_apply_with_documents_and_certificate_then_approve(client, register, db_session):
    category_id = _seed_category(db_session)
    applicant = register(email="tech@example.com")

    resp = client.post(
        "/api/v1/technicians/apply",
        headers=auth_header(applicant),
        json={
            "legal_name": "สมชาย ช่างดี",
            "national_id_or_passport": "1234567890123",
            "profile_photo": "http://img/profile.jpg",
            "identity_document_front": "http://img/id-front.jpg",
            "identity_document_back": "http://img/id-back.jpg",
            "selfie_with_document": "http://img/selfie.jpg",
            "categories": [
                {"service_category_id": category_id, "skill_level": "expert", "min_call_fee": 500, "accepts_emergency": True}
            ],
            "certificates": [
                {"certificate_type": "ช่างไฟฟ้าภายในอาคาร", "issuer": "กรมพัฒนาฝีมือแรงงาน", "certificate_number": "EL-001", "document_url": "http://img/cert.jpg"}
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    profile_id = resp.json()["id"]

    register(email="admin@example.com")
    _make_admin(db_session, "admin@example.com")
    admin = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Password123"}).json()["access_token"]

    # Admin sees the pending applicant and can inspect documents + certificates.
    pending = client.get("/api/v1/technicians/pending", headers=auth_header(admin)).json()
    assert any(p["id"] == profile_id for p in pending)

    detail = client.get(f"/api/v1/technicians/{profile_id}", headers=auth_header(admin))
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["identity_document_front"] == "http://img/id-front.jpg"
    assert body["selfie_with_document"] == "http://img/selfie.jpg"
    assert len(body["certificates"]) == 1
    assert body["certificates"][0]["certificate_type"] == "ช่างไฟฟ้าภายในอาคาร"
    assert len(body["categories"]) == 1
    assert float(body["categories"][0]["min_call_fee"]) == 500

    # Approve → applicant becomes a technician.
    approve = client.post(f"/api/v1/technicians/{profile_id}/review", headers=auth_header(admin), json={"approve": True})
    assert approve.status_code == 200
    me = client.get("/api/v1/auth/me", headers=auth_header(applicant)).json()
    assert me["role"] == "technician"


def test_only_admin_can_view_detail(client, register, db_session):
    _seed_category(db_session)
    applicant = register(email="t2@example.com")
    pid = client.post(
        "/api/v1/technicians/apply",
        headers=auth_header(applicant),
        json={"legal_name": "x", "category_ids": []},
    ).json()["id"]
    other = register(email="nosy@example.com")
    assert client.get(f"/api/v1/technicians/{pid}", headers=auth_header(other)).status_code == 403
