import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def client(app):
    with app.app_context():
        _db.create_all()
        yield app.test_client()
        _db.session.remove()
        _db.drop_all()


def register(client, username, email, password):
    return client.post("/auth/register", json={
        "username": username, "email": email, "password": password
    })


def login(client, email, password):
    return client.post("/auth/login", json={"email": email, "password": password})


@pytest.fixture
def user_token(client):
    register(client, "testuser", "test@example.com", "pass123")
    r = login(client, "test@example.com", "pass123")
    return r.get_json()["data"]["access_token"]


@pytest.fixture
def user_refresh_token(client):
    register(client, "testuser", "test@example.com", "pass123")
    r = login(client, "test@example.com", "pass123")
    return r.get_json()["data"]["refresh_token"]


@pytest.fixture
def admin_token(client):
    from app.models.user import User
    from app.extensions import db
    register(client, "adminuser", "admin@example.com", "pass123")
    with client.application.app_context():
        u = User.query.filter_by(email="admin@example.com").first()
        u.role = "admin"
        db.session.commit()
    r = login(client, "admin@example.com", "pass123")
    return r.get_json()["data"]["access_token"]
