"""Tests for authentication endpoints."""

import pytest


def test_login_success(client, admin_user):
    res = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "testpass123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, admin_user):
    res = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post(
        "/api/auth/login",
        data={"username": "nobody@test.com", "password": "pass"},
    )
    assert res.status_code == 401


def test_get_me(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"


def test_get_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_list_users(client, auth_headers, admin_user):
    res = client.get("/api/auth/users", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1
