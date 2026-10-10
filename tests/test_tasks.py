def create_task(client, headers, title="Write the report", description="Quarterly numbers"):
    response = client.post("/api/tasks", json={"title": title, "description": description}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


# ---------- create / list / view ----------
def test_user_can_create_task_and_it_starts_pending(client, user_headers):
    task = create_task(client, user_headers)
    assert task["status"] == "Pending"
    assert task["owner"]["email"] == "alice@example.com"


def test_create_task_validates_title(client, user_headers):
    response = client.post("/api/tasks", json={"title": "ab"}, headers=user_headers)
    assert response.status_code == 422


def test_tasks_require_authentication(client):
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "No token"}).status_code == 401


def test_user_lists_only_own_tasks(client, user_headers, other_user_headers):
    create_task(client, user_headers, title="Alice task")
    create_task(client, other_user_headers, title="Bob task")
    response = client.get("/api/tasks", headers=user_headers)
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["Alice task"]


def test_admin_lists_all_tasks(client, user_headers, other_user_headers, admin_headers):
    create_task(client, user_headers, title="Alice task")
    create_task(client, other_user_headers, title="Bob task")
    response = client.get("/api/tasks", headers=admin_headers)
    assert {t["title"] for t in response.json()} == {"Alice task", "Bob task"}


def test_list_can_filter_by_status(client, user_headers, admin_headers):
    first = create_task(client, user_headers, title="First task")
    create_task(client, user_headers, title="Second task")
    client.patch(f"/api/tasks/{first['id']}/status", json={"status": "Testing"}, headers=admin_headers)
    response = client.get("/api/tasks", params={"status": "Testing"}, headers=admin_headers)
    assert [t["title"] for t in response.json()] == ["First task"]


def test_view_task_not_found_returns_404(client, user_headers):
    assert client.get("/api/tasks/9999", headers=user_headers).status_code == 404


def test_user_cannot_view_another_users_task(client, user_headers, other_user_headers):
    task = create_task(client, other_user_headers)
    assert client.get(f"/api/tasks/{task['id']}", headers=user_headers).status_code == 403


def test_admin_can_view_any_task(client, user_headers, admin_headers):
    task = create_task(client, user_headers)
    assert client.get(f"/api/tasks/{task['id']}", headers=admin_headers).status_code == 200


# ---------- update ----------
def test_user_can_edit_own_task(client, user_headers):
    task = create_task(client, user_headers)
    response = client.put(
        f"/api/tasks/{task['id']}", json={"title": "New title", "description": "New text"}, headers=user_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New title"
    assert response.json()["description"] == "New text"


def test_user_cannot_edit_another_users_task(client, user_headers, other_user_headers):
    task = create_task(client, other_user_headers)
    response = client.put(f"/api/tasks/{task['id']}", json={"title": "Hacked title"}, headers=user_headers)
    assert response.status_code == 403


def test_admin_can_edit_any_task(client, user_headers, admin_headers):
    task = create_task(client, user_headers)
    response = client.put(f"/api/tasks/{task['id']}", json={"title": "Edited by admin"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Edited by admin"
    assert response.json()["user_id"] == task["user_id"]  # the owner does not change


# ---------- status ----------
def test_user_cannot_update_status(client, user_headers):
    task = create_task(client, user_headers)
    response = client.patch(f"/api/tasks/{task['id']}/status", json={"status": "Completed"}, headers=user_headers)
    assert response.status_code == 403


def test_admin_can_update_status(client, user_headers, admin_headers):
    task = create_task(client, user_headers)
    response = client.patch(f"/api/tasks/{task['id']}/status", json={"status": "In Progress"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_status_must_be_one_of_the_allowed_values(client, user_headers, admin_headers):
    task = create_task(client, user_headers)
    response = client.patch(f"/api/tasks/{task['id']}/status", json={"status": "Done"}, headers=admin_headers)
    assert response.status_code == 422


def test_admin_status_update_on_missing_task_returns_404(client, admin_headers):
    response = client.patch("/api/tasks/9999/status", json={"status": "Testing"}, headers=admin_headers)
    assert response.status_code == 404
