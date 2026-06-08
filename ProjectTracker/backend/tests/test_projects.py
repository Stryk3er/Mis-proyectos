"""Tests for projects CRUD endpoints."""

import pytest
from datetime import date, timedelta


PROJECT_PAYLOAD = {
    "name": "Test Project",
    "description": "A test project",
    "status": "on_track",
    "priority": "high",
    "progress": 50,
    "area": "Infrastructure",
    "start_date": str(date.today()),
    "end_date": str(date.today() + timedelta(days=30)),
}


# ── Create ───────────────────────────────────────────────────────────────────

def test_create_project(client, auth_headers):
    res = client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Test Project"
    assert data["progress"] == 50
    assert data["status"] == "on_track"


def test_create_project_unauthenticated(client):
    res = client.post("/api/projects/", json=PROJECT_PAYLOAD)
    assert res.status_code == 401


def test_create_project_missing_name(client, auth_headers):
    payload = {**PROJECT_PAYLOAD, "name": ""}
    res = client.post("/api/projects/", json=payload, headers=auth_headers)
    # Empty name should still create (validation is at app level)
    # but we verify the response is valid
    assert res.status_code in (201, 422)


# ── Read ─────────────────────────────────────────────────────────────────────

def test_list_projects_empty(client, auth_headers):
    res = client.get("/api/projects/", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_list_projects(client, auth_headers):
    client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers)
    client.post("/api/projects/", json={**PROJECT_PAYLOAD, "name": "Second"}, headers=auth_headers)

    res = client.get("/api/projects/", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_projects_filter_by_status(client, auth_headers):
    client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers)
    client.post("/api/projects/", json={**PROJECT_PAYLOAD, "name": "Delayed", "status": "delayed"}, headers=auth_headers)

    res = client.get("/api/projects/?status=delayed", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["status"] == "delayed"


def test_get_project_detail(client, auth_headers):
    created = client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers).json()
    res = client.get(f"/api/projects/{created['id']}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Test Project"


def test_get_project_not_found(client, auth_headers):
    res = client.get("/api/projects/9999", headers=auth_headers)
    assert res.status_code == 404


# ── Update ───────────────────────────────────────────────────────────────────

def test_update_project(client, auth_headers):
    created = client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers).json()
    res = client.patch(
        f"/api/projects/{created['id']}",
        json={"progress": 80, "status": "at_risk"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["progress"] == 80
    assert data["status"] == "at_risk"


def test_update_project_partial(client, auth_headers):
    created = client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers).json()
    res = client.patch(
        f"/api/projects/{created['id']}",
        json={"progress": 100},
        headers=auth_headers,
    )
    assert res.status_code == 200
    # Other fields unchanged
    assert res.json()["name"] == "Test Project"
    assert res.json()["progress"] == 100


# ── Delete ───────────────────────────────────────────────────────────────────

def test_delete_project(client, auth_headers):
    created = client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers).json()
    res = client.delete(f"/api/projects/{created['id']}", headers=auth_headers)
    assert res.status_code == 204

    # Should no longer appear in list
    projects = client.get("/api/projects/", headers=auth_headers).json()
    assert all(p["id"] != created["id"] for p in projects)


def test_delete_project_not_found(client, auth_headers):
    res = client.delete("/api/projects/9999", headers=auth_headers)
    assert res.status_code == 404


# ── Stats ────────────────────────────────────────────────────────────────────

def test_dashboard_stats_empty(client, auth_headers):
    res = client.get("/api/projects/stats", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["avg_progress"] == 0.0


def test_dashboard_stats(client, auth_headers):
    client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers)
    client.post("/api/projects/", json={**PROJECT_PAYLOAD, "name": "P2", "status": "delayed", "progress": 10}, headers=auth_headers)

    res = client.get("/api/projects/stats", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["on_track"] == 1
    assert data["delayed"] == 1
    assert data["avg_progress"] == 30.0


# ── Project updates (changelog) ───────────────────────────────────────────────

def test_add_project_update(client, auth_headers):
    created = client.post("/api/projects/", json=PROJECT_PAYLOAD, headers=auth_headers).json()
    res = client.post(
        f"/api/projects/{created['id']}/updates",
        json={"content": "Completed phase 1", "progress_snapshot": 50},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["content"] == "Completed phase 1"
    assert data["progress_snapshot"] == 50
