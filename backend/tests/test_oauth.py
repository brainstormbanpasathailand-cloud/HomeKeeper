"""OAuth callback tests with a mocked provider (never hits the network)."""
import pytest

from app.services import oauth as oauth_service
from app.services.oauth import NormalizedProfile


@pytest.fixture()
def mock_google(monkeypatch):
    def fake_exchange(provider, code, expected_nonce=None):
        return NormalizedProfile(
            provider="google",
            provider_user_id="google-sub-123",
            email="social@example.com",
            email_verified=True,
            name="Social User",
            avatar="http://img/avatar.png",
        )

    monkeypatch.setattr(oauth_service, "exchange_and_verify", fake_exchange)
    monkeypatch.setattr("app.api.routes.oauth.oauth_service.exchange_and_verify", fake_exchange)


def _start_state(client):
    # We can't call the real Google start (no client id), so sign a state directly.
    from app.services.auth import sign_oauth_state

    return sign_oauth_state("google", "test-nonce")


def test_oauth_callback_creates_user(client, mock_google):
    state = _start_state(client)
    resp = client.post(
        "/api/v1/auth/oauth/google/callback",
        json={"code": "auth-code", "state": state},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["email"] == "social@example.com"


def test_oauth_callback_reuses_identity(client, mock_google):
    state = _start_state(client)
    r1 = client.post("/api/v1/auth/oauth/google/callback", json={"code": "c", "state": state})
    r2 = client.post("/api/v1/auth/oauth/google/callback", json={"code": "c", "state": _start_state(client)})
    t1 = r1.json()["access_token"]
    t2 = r2.json()["access_token"]
    id1 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {t1}"}).json()["id"]
    id2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {t2}"}).json()["id"]
    assert id1 == id2  # same HomeKeeper user, not a duplicate


def test_oauth_invalid_state_rejected(client, mock_google):
    resp = client.post(
        "/api/v1/auth/oauth/google/callback",
        json={"code": "c", "state": "tampered"},
    )
    assert resp.status_code == 400
