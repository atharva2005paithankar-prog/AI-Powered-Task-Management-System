PASSWORD = "Passw0rd!"

REGISTER = {"name": "Asha Patil", "email": "asha@example.com", "password": PASSWORD}


def test_register_creates_user_without_exposing_password(client):
    response = client.post("/api/auth/register", json=REGISTER)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "asha@example.com"
    assert body["role"] == "user"
    assert "password" not in body


def test_register_cannot_choose_admin_role(client):
    response = client.post("/api/auth/register", json={**REGISTER, "role": "admin"})
    assert response.status_code == 201
    assert response.json()["role"] == "user"  # the extra "role" field is ignored


def test_register_duplicate_email_returns_409(client):
    client.post("/api/auth/register", json=REGISTER)
    response = client.post("/api/auth/register", json={**REGISTER, "email": "ASHA@example.com"})
    assert response.status_code == 409


def test_register_validates_input(client):
    assert client.post("/api/auth/register", json={**REGISTER, "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={**REGISTER, "email": "not-an-email"}).status_code == 422
    assert client.post("/api/auth/register", json={"name": "A"}).status_code == 422


def test_login_returns_jwt_token(client):
    client.post("/api/auth/register", json=REGISTER)
    response = client.post("/api/auth/login", json={"email": "asha@example.com", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "asha@example.com"


def test_login_with_wrong_password_returns_401(client):
    client.post("/api/auth/register", json=REGISTER)
    response = client.post("/api/auth/login", json={"email": "asha@example.com", "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_with_unknown_email_returns_same_401(client):
    response = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_a_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_returns_current_user(client, user_headers):
    response = client.get("/api/auth/me", headers=user_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"
