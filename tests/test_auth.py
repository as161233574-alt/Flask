from tests.conftest import register, login


# --- register ---

def test_register_success(client):
    r = register(client, "alice", "alice@example.com", "pass123")
    assert r.status_code == 201
    data = r.get_json()
    assert data["success"] is True
    assert data["data"]["username"] == "alice"
    assert data["data"]["role"] == "user"


def test_register_missing_fields(client):
    r = client.post("/auth/register", json={"username": "x"})
    assert r.status_code == 400
    assert r.get_json()["success"] is False


def test_register_short_password(client):
    r = register(client, "bob", "bob@example.com", "abc")
    assert r.status_code == 400


def test_register_duplicate_username(client):
    register(client, "alice", "alice@example.com", "pass123")
    r = register(client, "alice", "other@example.com", "pass123")
    assert r.status_code == 409
    assert "username" in r.get_json()["error"]


def test_register_duplicate_email(client):
    register(client, "alice", "alice@example.com", "pass123")
    r = register(client, "alice2", "alice@example.com", "pass123")
    assert r.status_code == 409
    assert "email" in r.get_json()["error"]


# --- login ---

def test_login_success(client):
    register(client, "alice", "alice@example.com", "pass123")
    r = login(client, "alice@example.com", "pass123")
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_missing_fields(client):
    r = client.post("/auth/login", json={"email": "x@x.com"})
    assert r.status_code == 400


def test_login_wrong_password(client):
    register(client, "alice", "alice@example.com", "pass123")
    r = login(client, "alice@example.com", "wrongpass")
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = login(client, "nobody@example.com", "pass123")
    assert r.status_code == 401


# --- logout ---

def test_logout_success(client, user_token):
    r = client.post("/auth/logout", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.get_json()["success"] is True


def test_logout_revoked_token_rejected(client, user_token):
    client.post("/auth/logout", headers={"Authorization": f"Bearer {user_token}"})
    r = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 401


def test_logout_no_token(client):
    r = client.post("/auth/logout")
    assert r.status_code == 401


# --- refresh ---

def test_refresh_success(client, user_refresh_token):
    r = client.post("/auth/refresh", headers={"Authorization": f"Bearer {user_refresh_token}"})
    assert r.status_code == 200
    assert "access_token" in r.get_json()["data"]


def test_refresh_no_token(client):
    r = client.post("/auth/refresh")
    assert r.status_code == 401
