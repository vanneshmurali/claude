# Testing Expectations

Tests use `pytest` with Flask's test client:

```powershell
py -m pip install -r requirements-dev.txt
py -m pytest
```

## Layout and fixtures (`tests/conftest.py`)

| Fixture / helper | What it does                                                          |
|------------------|-----------------------------------------------------------------------|
| `app`            | `create_app({"TESTING": True, "DB": <tmp_path>/test.db})`; a fresh DB per test |
| `client`         | `app.test_client()`                                                   |
| `login(user)`    | Logs in as `"admin"` or `"user"`, including the CSRF token            |
| `add(**fields)`  | POSTs the add-employee form with a valid CSRF token                   |
| `rows()`         | Reads the `employees` table straight from the test DB                 |
| `token(client, url)` | Returns the CSRF token from the form at `url`                     |

```python
def test_add_and_list(login, add, rows):
    login("user")
    add(name="Ann", department="IT", salary="1500")
    assert rows() == [("Ann", "", "IT", 1500)]
```

## Rules

- New routes or behaviour changes need tests. Never point tests at the real `employees.db`; always use the
  `app` fixture.
- At a minimum, cover: the happy path, an unauthenticated request (expect a redirect to `/login`), and a
  wrong-role request where it applies (expect `403`).
- Validation rules get a test per rule (use `pytest.mark.parametrize`), checking both the `400` and that
  nothing was saved.

## Security Tests

- Every protected route has a test with **no session** and a test with the **wrong role**.
- A POST without a valid `csrf_token` returns `400`.
- `GET /logout` returns `405`.
- A failed login does not set a session and shows "Invalid login".
- Templated user input is escaped (e.g. an employee named `<script>` is rendered as text).
