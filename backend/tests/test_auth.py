"""Tests for authentication and access control."""

from __future__ import annotations

from tests.conftest import register_and_login


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_register_success(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "bob@example.com", "password": "supersecret"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "bob@example.com"
    assert "id" in body
    # password / hash must never be returned
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "supersecret"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 409


def test_register_rejects_short_password(client):
    r = client.post(
        "/api/auth/register", json={"email": "x@example.com", "password": "short"}
    )
    assert r.status_code == 422


def test_register_rejects_bad_email(client):
    r = client.post(
        "/api/auth/register", json={"email": "not-an-email", "password": "password123"}
    )
    assert r.status_code == 422


def test_email_is_normalized_lowercase(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "Mixed@Example.com", "password": "password123"},
    )
    assert r.status_code == 201
    # login with different casing works because email is normalized
    r = client.post(
        "/api/auth/login",
        data={"username": "mixed@example.com", "password": "password123"},
    )
    assert r.status_code == 200


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "carol@example.com", "password": "password123"},
    )
    r = client.post(
        "/api/auth/login",
        data={"username": "carol@example.com", "password": "WRONG"},
    )
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post(
        "/api/auth/login",
        data={"username": "ghost@example.com", "password": "password123"},
    )
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_current_user(client):
    token = register_and_login(client, email="dave@example.com")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "dave@example.com"


def test_invalid_token_rejected(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage.token.here"})
    assert r.status_code == 401
