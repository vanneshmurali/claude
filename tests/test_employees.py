import pytest


def test_requires_login(client):
    r = client.get("/")
    assert r.status_code == 302 and r.location == "/login"


def test_add_and_list(login, add, rows):
    login("user")
    r = add(name=" Ann ", email="ann@x.com", department="IT", salary="1500.5")
    assert r.status_code == 200 and "Ann" in r.get_data(as_text=True)
    assert rows() == [("Ann", "ann@x.com", "IT", 1500.5)]


def test_blank_salary_defaults_to_zero(login, add, rows):
    login("user")
    add(name="Bob", department="HR")
    assert rows() == [("Bob", "", "HR", 0)]


@pytest.mark.parametrize("fields, message", [
    ({"department": "IT"}, "Name is required."),
    ({"name": "   ", "department": "IT"}, "Name is required."),
    ({"name": "Ann"}, "Department is required."),
    ({"name": "x" * 101, "department": "IT"}, "Name must be at most 100 characters."),
    ({"name": "Ann", "department": "IT", "email": "not-an-email"}, "Email must be a valid address."),
    ({"name": "Ann", "department": "IT", "salary": "-1"}, "Salary must be a number of 0 or more."),
    ({"name": "Ann", "department": "IT", "salary": "abc"}, "Salary must be a number of 0 or more."),
    ({"name": "Ann", "department": "IT", "salary": "nan"}, "Salary must be a number of 0 or more."),
])
def test_validation_errors(login, add, rows, fields, message):
    login("user")
    r = add(**fields)
    assert r.status_code == 400 and message in r.get_data(as_text=True)
    assert rows() == []


def test_validation_error_keeps_typed_values(login, add):
    login("user")
    r = add(name="Ann", email="bad", department="Sales")
    html = r.get_data(as_text=True)
    assert 'value="Ann"' in html and 'value="Sales"' in html


def test_user_input_is_escaped(login, add):
    login("user")
    html = add(name="<script>alert(1)</script>", department="IT").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
