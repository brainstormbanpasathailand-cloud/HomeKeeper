"""End-to-end job lifecycle, quotation, health record, warranty, review."""
from tests.conftest import auth_header


def _seed_category(db_session):
    from app.models.catalog import ServiceCategory

    cat = ServiceCategory(slug="plumber", name_th="ช่างประปา", name_en="Plumber", sort_order=1)
    db_session.add(cat)
    db_session.commit()
    return cat.id


def _make_role(db_session, email, role):
    from app.models.user import User

    u = db_session.query(User).filter(User.email == email).first()
    u.role = role
    db_session.commit()
    return u.id


def test_full_job_lifecycle_generates_health_record(client, register, db_session):
    category_id = _seed_category(db_session)

    customer = register(email="customer@example.com")
    register(email="tech@example.com")
    register(email="admin@example.com")

    tech_id = _make_role(db_session, "tech@example.com", "technician")
    _make_role(db_session, "admin@example.com", "super_admin")

    admin_login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Password123"}).json()["access_token"]
    tech_login = client.post("/api/v1/auth/login", json={"email": "tech@example.com", "password": "Password123"}).json()["access_token"]

    # Customer creates a job.
    job = client.post(
        "/api/v1/jobs",
        headers=auth_header(customer),
        json={"service_category_id": category_id, "title": "ท่อรั่ว", "urgency": "today", "photos": ["http://img/leak.jpg"]},
    ).json()
    assert job["status"] == "requested"

    # Admin assigns the technician.
    assigned = client.post(
        f"/api/v1/admin/jobs/{job['id']}/assign",
        headers=auth_header(admin_login),
        json={"technician_id": tech_id},
    )
    assert assigned.status_code == 200
    assert assigned.json()["status"] == "assigned"

    # Technician accepts.
    resp = client.post(f"/api/v1/jobs/{job['id']}/respond", headers=auth_header(tech_login), json={"accept": True})
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    # Move through workflow.
    for st in ["traveling", "arrived", "inspecting"]:
        r = client.post(f"/api/v1/jobs/{job['id']}/status", headers=auth_header(tech_login), json={"status": st})
        assert r.status_code == 200, r.text

    # Technician quotes.
    quote = client.post(
        f"/api/v1/jobs/{job['id']}/quotations",
        headers=auth_header(tech_login),
        json={"labor_cost": 500, "parts": [{"part_name": "ข้อต่อ", "quantity": 2, "unit_price": 50}]},
    )
    assert quote.status_code == 201, quote.text
    quotation_id = quote.json()["id"]
    assert quote.json()["total"] == 600

    # Customer approves the quotation.
    dec = client.post(
        f"/api/v1/quotations/{quotation_id}/decision",
        headers=auth_header(customer),
        json={"decision": "approve"},
    )
    assert dec.status_code == 200
    assert dec.json()["status"] == "approved"

    # Technician works and completes.
    client.post(f"/api/v1/jobs/{job['id']}/media", headers=auth_header(tech_login), json={"kind": "before", "url": "http://img/before.jpg"})
    r = client.post(f"/api/v1/jobs/{job['id']}/status", headers=auth_header(tech_login), json={"status": "in_progress"})
    assert r.status_code == 200, r.text
    client.post(f"/api/v1/jobs/{job['id']}/media", headers=auth_header(tech_login), json={"kind": "after", "url": "http://img/after.jpg"})
    r = client.post(f"/api/v1/jobs/{job['id']}/status", headers=auth_header(tech_login), json={"status": "completed"})
    assert r.status_code == 200, r.text

    # Health record auto-generated.
    records = client.get("/api/v1/health-records", headers=auth_header(customer)).json()
    assert len(records) == 1
    rec = records[0]
    assert rec["job_id"] == job["id"]
    assert rec["before_photos"] == ["http://img/before.jpg"]
    assert rec["after_photos"] == ["http://img/after.jpg"]
    assert rec["warranty_end"] is not None
    # The single quoted part must appear once, not double-counted (a part row
    # carries both job_id and quotation_id).
    assert len(rec["parts_used"]) == 1

    # Warranty claim.
    claim = client.post(
        "/api/v1/warranty-claims",
        headers=auth_header(customer),
        json={"original_job_id": job["id"], "reason": "รั่วอีก"},
    )
    assert claim.status_code == 201, claim.text

    # Review.
    review = client.post(
        f"/api/v1/jobs/{job['id']}/review",
        headers=auth_header(customer),
        json={"rating_quality": 5, "rating_value": 4, "comment": "ดีมาก"},
    )
    assert review.status_code == 201, review.text
    assert review.json()["overall_rating"] == 4.5


def test_technician_cannot_start_before_quote_approved(client, register, db_session):
    category_id = _seed_category(db_session)
    customer = register(email="c2@example.com")
    register(email="t2@example.com")
    register(email="a2@example.com")
    tech_id = _make_role(db_session, "t2@example.com", "technician")
    _make_role(db_session, "a2@example.com", "super_admin")
    admin = client.post("/api/v1/auth/login", json={"email": "a2@example.com", "password": "Password123"}).json()["access_token"]
    tech = client.post("/api/v1/auth/login", json={"email": "t2@example.com", "password": "Password123"}).json()["access_token"]

    job = client.post("/api/v1/jobs", headers=auth_header(customer), json={"service_category_id": category_id, "title": "x", "photos": ["http://img/x.jpg"]}).json()
    client.post(f"/api/v1/admin/jobs/{job['id']}/assign", headers=auth_header(admin), json={"technician_id": tech_id})
    client.post(f"/api/v1/jobs/{job['id']}/respond", headers=auth_header(tech), json={"accept": True})
    client.post(f"/api/v1/jobs/{job['id']}/status", headers=auth_header(tech), json={"status": "traveling"})
    client.post(f"/api/v1/jobs/{job['id']}/status", headers=auth_header(tech), json={"status": "arrived"})
    # Jump straight to in_progress without an approved quotation.
    r = client.post(f"/api/v1/jobs/{job['id']}/status", headers=auth_header(tech), json={"status": "in_progress"})
    assert r.status_code == 409


def test_idempotent_job_creation(client, register, db_session):
    category_id = _seed_category(db_session)
    customer = register(email="c3@example.com")
    headers = auth_header(customer)
    headers["Idempotency-Key"] = "abc-123"
    body = {"service_category_id": category_id, "title": "dup", "photos": ["http://img/d.jpg"]}
    j1 = client.post("/api/v1/jobs", headers=headers, json=body).json()
    j2 = client.post("/api/v1/jobs", headers=headers, json=body).json()
    assert j1["id"] == j2["id"]


def test_job_requires_at_least_one_photo(client, register, db_session):
    category_id = _seed_category(db_session)
    customer = register(email="c4@example.com")
    # No photos → rejected.
    r = client.post("/api/v1/jobs", headers=auth_header(customer), json={"service_category_id": category_id, "title": "no photo"})
    assert r.status_code == 422
    # Eleven photos → rejected (max 10).
    r2 = client.post(
        "/api/v1/jobs",
        headers=auth_header(customer),
        json={"service_category_id": category_id, "title": "too many", "photos": [f"http://img/{i}.jpg" for i in range(11)]},
    )
    assert r2.status_code == 422
