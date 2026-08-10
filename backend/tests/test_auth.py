def test_register_creates_user(client):
    resp = client.post("/api/auth/register", json={
        "name": "Alice", "email": "alice_test@example.com", "password": "SecurePass123!",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "alice_test@example.com"
    assert "access_token" in body


def test_register_duplicate_email_rejected(client):
    payload = {"name": "Bob", "email": "bob_test@example.com", "password": "SecurePass123!"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


def test_login_success(client):
    payload = {"name": "Carol", "email": "carol_test@example.com", "password": "SecurePass123!"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_invalid_password_rejected(client):
    payload = {"name": "Dave", "email": "dave_test@example.com", "password": "SecurePass123!"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/login", json={"email": payload["email"], "password": "WrongPassword"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client, registered_user_token):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {registered_user_token}"})
    assert resp.status_code == 200
