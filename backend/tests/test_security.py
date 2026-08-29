"""Tests for the security hardening: headers, rate limiting, no info leaks."""

from __future__ import annotations


def test_security_headers_present(client):
    r = client.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "no-referrer"


def test_request_id_header_echoed(client):
    r = client.get("/api/health")
    assert r.headers.get("X-Request-ID")


def test_login_rate_limited_after_repeated_failures(client):
    client.post(
        "/api/auth/register",
        json={"email": "victim@example.com", "password": "password123"},
    )
    # limiter allows 10 failures/min; the 11th attempt should be blocked.
    codes = []
    for _ in range(12):
        r = client.post(
            "/api/auth/login",
            data={"username": "victim@example.com", "password": "WRONG"},
        )
        codes.append(r.status_code)
    assert 401 in codes
    assert 429 in codes
    assert codes[-1] == 429


def test_login_error_message_is_generic(client):
    # Same message whether the user exists or not (no enumeration via message).
    client.post(
        "/api/auth/register",
        json={"email": "real@example.com", "password": "password123"},
    )
    r_known = client.post(
        "/api/auth/login", data={"username": "real@example.com", "password": "nope"}
    )
    r_unknown = client.post(
        "/api/auth/login", data={"username": "nobody@example.com", "password": "nope"}
    )
    assert r_known.status_code == r_unknown.status_code == 401
    assert r_known.json()["detail"] == r_unknown.json()["detail"]
