"""Tests for task CRUD and per-owner isolation."""

from __future__ import annotations

from tests.conftest import register_and_login


def _make_task(client, headers, **over):
    payload = {"title": "Write report", "priority": "high"}
    payload.update(over)
    return client.post("/api/tasks", json=payload, headers=headers)


def test_tasks_require_auth(client):
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "x"}).status_code == 401


def test_create_task(client, auth_headers):
    r = _make_task(client, auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Write report"
    assert body["status"] == "todo"       # default
    assert body["priority"] == "high"
    assert "owner_id" in body


def test_create_task_requires_title(client, auth_headers):
    r = client.post("/api/tasks", json={"title": ""}, headers=auth_headers)
    assert r.status_code == 422


def test_list_only_returns_own_tasks(client):
    t1 = register_and_login(client, email="owner1@example.com")
    t2 = register_and_login(client, email="owner2@example.com")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    _make_task(client, h1, title="alice task")
    _make_task(client, h2, title="bob task")

    r1 = client.get("/api/tasks", headers=h1)
    assert [t["title"] for t in r1.json()] == ["alice task"]
    r2 = client.get("/api/tasks", headers=h2)
    assert [t["title"] for t in r2.json()] == ["bob task"]


def test_cannot_read_others_task(client):
    t1 = register_and_login(client, email="a@example.com")
    t2 = register_and_login(client, email="b@example.com")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    task_id = _make_task(client, h1).json()["id"]
    # other user gets 404, not 403 (no existence leak)
    assert client.get(f"/api/tasks/{task_id}", headers=h2).status_code == 404


def test_cannot_update_or_delete_others_task(client):
    t1 = register_and_login(client, email="c@example.com")
    t2 = register_and_login(client, email="d@example.com")
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    task_id = _make_task(client, h1).json()["id"]
    assert client.patch(f"/api/tasks/{task_id}", json={"title": "hax"}, headers=h2).status_code == 404
    assert client.delete(f"/api/tasks/{task_id}", headers=h2).status_code == 404
    # original owner's task is untouched
    assert client.get(f"/api/tasks/{task_id}", headers=h1).json()["title"] == "Write report"


def test_update_task_partial(client, auth_headers):
    task_id = _make_task(client, auth_headers).json()["id"]
    r = client.patch(
        f"/api/tasks/{task_id}", json={"status": "in_progress"}, headers=auth_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "in_progress"
    assert body["title"] == "Write report"  # unchanged


def test_delete_task(client, auth_headers):
    task_id = _make_task(client, auth_headers).json()["id"]
    assert client.delete(f"/api/tasks/{task_id}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/tasks/{task_id}", headers=auth_headers).status_code == 404


def test_filter_by_status(client, auth_headers):
    _make_task(client, auth_headers, title="todo one")
    tid = _make_task(client, auth_headers, title="done one").json()["id"]
    client.patch(f"/api/tasks/{tid}", json={"status": "done"}, headers=auth_headers)

    r = client.get("/api/tasks?status=done", headers=auth_headers)
    assert [t["title"] for t in r.json()] == ["done one"]


def test_invalid_status_value_rejected(client, auth_headers):
    r = client.post(
        "/api/tasks", json={"title": "x", "status": "bogus"}, headers=auth_headers
    )
    assert r.status_code == 422


def test_get_missing_task_404(client, auth_headers):
    assert client.get("/api/tasks/99999", headers=auth_headers).status_code == 404
