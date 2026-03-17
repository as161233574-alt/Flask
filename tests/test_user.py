from tests.conftest import register, login


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# --- GET /users/me ---

def test_get_me_success(client, user_token):
    r = client.get("/users/me", headers=auth(user_token))
    assert r.status_code == 200
    assert r.get_json()["data"]["username"] == "testuser"


def test_get_me_no_token(client):
    r = client.get("/users/me")
    assert r.status_code == 401


# --- PUT /users/me ---

def test_update_me_username(client, user_token):
    r = client.put("/users/me", json={"username": "newname"}, headers=auth(user_token))
    assert r.status_code == 200
    assert r.get_json()["data"]["username"] == "newname"


def test_update_me_email(client, user_token):
    r = client.put("/users/me", json={"email": "new@example.com"}, headers=auth(user_token))
    assert r.status_code == 200
    assert r.get_json()["data"]["email"] == "new@example.com"


def test_update_me_no_fields(client, user_token):
    r = client.put("/users/me", json={}, headers=auth(user_token))
    assert r.status_code == 200


def test_update_me_duplicate_username(client, user_token):
    register(client, "other", "other@example.com", "pass123")
    r = client.put("/users/me", json={"username": "other"}, headers=auth(user_token))
    assert r.status_code == 409


def test_update_me_duplicate_email(client, user_token):
    register(client, "other", "other@example.com", "pass123")
    r = client.put("/users/me", json={"email": "other@example.com"}, headers=auth(user_token))
    assert r.status_code == 409


# --- PUT /users/me/password ---

def test_change_password_success(client, user_token):
    r = client.put("/users/me/password", json={
        "current_password": "pass123", "new_password": "newpass456"
    }, headers=auth(user_token))
    assert r.status_code == 200


def test_change_password_missing_fields(client, user_token):
    r = client.put("/users/me/password", json={"current_password": "pass123"}, headers=auth(user_token))
    assert r.status_code == 400


def test_change_password_wrong_current(client, user_token):
    r = client.put("/users/me/password", json={
        "current_password": "wrongpass", "new_password": "newpass456"
    }, headers=auth(user_token))
    assert r.status_code == 401


def test_change_password_short_new(client, user_token):
    r = client.put("/users/me/password", json={
        "current_password": "pass123", "new_password": "abc"
    }, headers=auth(user_token))
    assert r.status_code == 400


# --- GET /users (admin only) ---

def test_list_users_admin(client, admin_token):
    r = client.get("/users/", headers=auth(admin_token))
    assert r.status_code == 200
    assert isinstance(r.get_json()["data"], list)


def test_list_users_non_admin(client, user_token):
    r = client.get("/users/", headers=auth(user_token))
    assert r.status_code == 403


def test_list_users_no_token(client):
    r = client.get("/users/")
    assert r.status_code == 401


# --- PUT /users/<id>/role (admin only) ---

def test_set_role_success(client, admin_token):
    register(client, "target", "target@example.com", "pass123")
    from app.models.user import User
    with client.application.app_context():
        u = User.query.filter_by(username="target").first()
        uid = u.id
    r = client.put(f"/users/{uid}/role", json={"role": "admin"}, headers=auth(admin_token))
    assert r.status_code == 200
    assert r.get_json()["data"]["role"] == "admin"


def test_set_role_invalid_role(client, admin_token):
    register(client, "target", "target@example.com", "pass123")
    from app.models.user import User
    with client.application.app_context():
        u = User.query.filter_by(username="target").first()
        uid = u.id
    r = client.put(f"/users/{uid}/role", json={"role": "superuser"}, headers=auth(admin_token))
    assert r.status_code == 400


def test_set_role_user_not_found(client, admin_token):
    r = client.put("/users/9999/role", json={"role": "admin"}, headers=auth(admin_token))
    assert r.status_code == 404


def test_set_role_non_admin(client, user_token):
    r = client.put("/users/1/role", json={"role": "admin"}, headers=auth(user_token))
    assert r.status_code == 403


def test_set_role_no_token(client):
    r = client.put("/users/1/role", json={"role": "admin"})
    assert r.status_code == 401
