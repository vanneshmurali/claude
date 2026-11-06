import re
import sqlite3
import pytest
from app import create_app

PASSWORDS = {"admin": "admin123", "user": "user123"}


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DB": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


def token(client, url):
    """CSRF token from the form rendered at url."""
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


@pytest.fixture
def login(client):
    def do(user):
        return client.post("/login", data={"username": user, "password": PASSWORDS[user],
                                           "csrf_token": token(client, "/login")})
    return do


@pytest.fixture
def add(client):
    def do(**fields):
        data = {"name": "", "email": "", "department": "", "salary": "", **fields}
        return client.post("/", data={**data, "csrf_token": token(client, "/")})
    return do


@pytest.fixture
def rows(app):
    def do():
        con = sqlite3.connect(app.config["DB"])
        result = con.execute("SELECT name, email, department, salary FROM employees").fetchall()
        con.close()
        return result
    return do
