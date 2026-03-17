def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_cors_header(client):
    r = client.options("/auth/login", headers={"Origin": "http://mobile.example.com"})
    assert "Access-Control-Allow-Origin" in r.headers


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Flask" in r.data
