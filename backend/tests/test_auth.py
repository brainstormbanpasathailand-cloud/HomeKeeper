"""Authentication and session tests."""
from tests.conftest import auth_header


def test_register_and_me(client, register):
    token = register()
    resp = client.get("/api/v1/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"
    assert resp.json()["role"] == "customer"


def test_duplicate_email_rejected(client, register):
    register()
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "Password123", "full_name": "Dup"},
    )
    assert resp.status_code == 409


def test_login_wrong_password(client, register):
    register()
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_refresh_rotates_token(client, register):
    register()
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "Password123"},
    ).json()
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert resp.status_code == 200
    assert resp.json()["refresh_token"] != login["refresh_token"]


def test_protected_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_onboarding_requires_terms(client, register):
    token = register()
    resp = client.post(
        "/api/v1/auth/onboarding",
        headers=auth_header(token),
        json={"display_name": "Nick", "accept_tos": False, "accept_privacy": False},
    )
    assert resp.status_code == 400


def test_cannot_unlink_last_identity(client, register):
    token = register()
    identities = client.get("/api/v1/auth/identities", headers=auth_header(token)).json()
    resp = client.delete(f"/api/v1/auth/identities/{identities[0]['id']}", headers=auth_header(token))
    assert resp.status_code == 400
