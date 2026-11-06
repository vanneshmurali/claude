import pytest
from conftest import token


def test_login_success_sets_session(client, login):
    r = login("admin")
    assert r.status_code == 302 and r.location == "/"
    with client.session_transaction() as s:
        assert s["user"] == "admin" and s["role"] == "admin"


@pytest.mark.parametrize("username, password", [("admin", "wrong"), ("nobody", "admin123"), ("", "")])
def test_login_failure(client, username, password):
    r = client.post("/login", data={"username": username, "password": password,
                                    "csrf_token": token(client, "/login")})
    assert r.status_code == 200 and "Invalid login" in r.get_data(as_text=True)
    with client.session_transaction() as s:
        assert "user" not in s


def test_post_without_csrf_token_is_rejected(client):
    r = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 400


def test_post_with_wrong_csrf_token_is_rejected(client, login):
    login("admin")
    token(client, "/")
    r = client.post("/", data={"name": "A", "department": "IT", "csrf_token": "wrong"})
    assert r.status_code == 400


def test_logout_get_not_allowed(client, login):
    login("user")
    assert client.get("/logout").status_code == 405


def test_logout_post_clears_session(client, login):
    login("user")
    r = client.post("/logout", data={"csrf_token": token(client, "/")})
    assert r.status_code == 302 and r.location == "/login"
    assert client.get("/").location == "/login"
