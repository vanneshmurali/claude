# Employee App — Application Roadmap

**Status:** Phase 1 done (2026-11-05). Phases 2 and 3 not started.

## Context

`employee_app` is a single-file Flask + SQLite app (`app.py`):

- login with two hard-coded users (password hashes);
- an employee list with an add form;
- an admin-only dashboard;
- CSRF protection, a secret key taken from an environment variable, and debug mode switched off by default (all added earlier).

What's still missing:

- automated tests;
- server-side input checks (only the HTML form enforces required fields);
- any way to edit or remove an employee;
- search;
- production run and config guidance.

`app.py` is also starting to mix configuration, database code, auth, templates and routes in one file.

The user asked for a full roadmap in three phases:

1. Foundation
2. Features
3. Operations

Each phase is shippable on its own and leaves the app working.

**Deliverable:** when this plan is approved, the first step is to save it into the repo as `docs/PLAN.md`, then carry out Phase 1.

## Current state (reuse, don't rewrite)

| Piece | Location | Keep / change |
|---|---|---|
| `db()` connect + `CREATE TABLE IF NOT EXISTS` | `app.py` | Keep the approach; move to `db.py`, read the path from `app.config["DB"]` |
| `csrf_token()` + `check_csrf` before-request | `app.py` | Keep as is; move to `auth.py` |
| `USERS` (scrypt hashes) + `check_password_hash` login | `app.py` | Keep; move to `auth.py` |
| Inline auth checks (`redirect("/login")`, `abort(403)`) | `employees()`, `dashboard()` | Replace with `login_required` / `role_required` decorators |
| `PAGE` inline template with `{{ body \| safe }}` | `app.py` | Replace with `templates/base.html` (removes the `\| safe` XSS trap) |
| Smoke-test logic (CSRF, roles, escaping) | scratchpad `smoke.py` | Turn into the pytest suite |
| `/review-quality` command, `db-hub` MCP | `.claude/`, `.mcp.json` | Use them to check the work (see Verification) |

---

## Phase 1 — Foundation (no behaviour change for users)

### 1.1 Dependencies
- Add `requirements.txt` with `flask==3.0.3`, and `requirements-dev.txt` with `-r requirements.txt` plus `pytest`.

### 1.2 Split `app.py` with an app factory

```
employee_app/
├── app.py          # create_app(): config, register blueprints, before_request CSRF; __main__ runs it
├── db.py           # get_db(), init_db() with schema + idempotent ALTERs
├── auth.py         # Blueprint: USERS, csrf_token, check_csrf, login_required, role_required, /login, /logout
├── employees.py    # Blueprint: /, /dashboard (Phase 2 routes land here too)
├── templates/      # base.html, login.html, employees.html, dashboard.html
└── tests/
```

- `create_app(config=None)` sets `DB` to `os.environ.get("EMPLOYEES_DB", "employees.db")`. Tests can pass `{"DB": tmp_path / "t.db"}` instead.
- Keep the URLs exactly as they are (`/`, `/login`, `/logout`, `/dashboard`), so the README and users' bookmarks still work.
- Move the templates to `templates/*.html`. They extend `base.html`, which holds the nav bar and the logout form with its CSRF field. No user data goes through `| safe`.

### 1.3 Auth decorators (in `auth.py`)
```python
def login_required(view):        # redirect to /login when no session
def role_required(role):         # 403 when session role != role; implies login_required
```
Use them on every route. The rule in `CLAUDE.md` that each route must check access itself still holds; the decorators are just how each route does it.

### 1.4 Server-side validation on add
| Field | Rule | On failure |
|---|---|---|
| `name`, `department` | Trimmed, not empty, ≤ 100 chars | Re-render the form with the error, status `400`, keep what the user typed |
| `email` | Optional; if given, must contain an `@` | Same |
| `salary` | Optional; if given, a number ≥ 0 (blank → 0) | Same |

Write it as one small helper, `validate_employee(form) -> (data, errors)`, which the edit form in Phase 2 also uses.

### 1.5 Test suite (`tests/`)
- `conftest.py`: an `app` fixture that uses a temporary DB, a `client` fixture, and a `login(client, user)` helper that fills in the CSRF token.
- `test_auth.py`: login success and failure, logout is POST only (`GET /logout` → 405), a POST without a CSRF token → 400.
- `test_employees.py`: add and list, validation errors, salary default, `<script>` is shown escaped, and no session → redirect.
- `test_dashboard.py`: admin → 200 with the correct stats, user → 403, no session → redirect.

### 1.6 Docs
Update the project structure, the "inline templates" note, and the auth snippets in `CLAUDE.md`. In `docs/testing.md`, replace "patch `app.DB`" with "pass `DB` to `create_app`". Add a "Run tests" line to the README.

---

## Phase 2 — Features

### 2.1 Edit employee (admin only)
- `GET/POST /employees/<id>/edit` with `role_required("admin")`. Uses the same form template and `validate_employee`.
- Returns 404 for an id that doesn't exist or is archived.
- The list gets an "Edit" link for admins. The link is only a convenience; the route enforces the admin check.

### 2.2 Archive instead of delete (admin only)
- Schema: `init_db()` adds `archived INTEGER NOT NULL DEFAULT 0` with an idempotent `ALTER TABLE`, guarded by a `PRAGMA table_info` check.
- `POST /employees/<id>/archive` and `POST /employees/<id>/restore`, both CSRF-protected forms.
- The list, the search and the dashboard stats exclude archived rows. Admins can view archived rows with `GET /?archived=1`.
- There is still no hard delete, in line with CLAUDE.md's "Don't Do" list.

### 2.3 Search, filter and pagination
- `GET /?q=<text>&department=<dept>&page=<n>`:
  - `q` matches name or email with a parameterised `LIKE ?`;
  - `department` is a dropdown built from `SELECT DISTINCT department`;
  - 20 rows per page using `LIMIT/OFFSET`.
- The filter values stay in the page and next/previous links.

### 2.4 Email uniqueness (needs a decision first)
- First check the existing data for duplicates, using `db-hub` (`SELECT lower(email), COUNT(*) … HAVING COUNT(*) > 1`).
- If there are none, add `CREATE UNIQUE INDEX IF NOT EXISTS ux_employees_email ON employees(lower(email)) WHERE email <> ''`, plus a friendly validation error on add and edit.
- If duplicates exist, stop and ask the user how to resolve them.

### 2.5 Tests and docs
Each new route gets tests for the happy path, no session, wrong role (user → 403), a missing CSRF token, and a nonexistent id (404).

Update the Key Domain Rules and Roles tables in `CLAUDE.md`:

| Role | List / search / add | Edit / archive / restore | Dashboard |
|---|---|---|---|
| admin | ✅ | ✅ | ✅ |
| user | ✅ | ❌ 403 | ❌ 403 |

---

## Phase 3 — Operations

### 3.1 Configuration
| Env var | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Session signing | Random per start (dev only) |
| `EMPLOYEES_DB` | SQLite path | `employees.db` |
| `FLASK_DEBUG` | Debugger | Off |
| `APP_ENV` | `production` makes the app refuse to start without `SECRET_KEY` | `development` |

### 3.2 Hardening
- Session cookie settings: `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SAMESITE="Lax"`, plus `SESSION_COOKIE_SECURE=True` when `APP_ENV=production`.
- Logging with the stdlib `logging` module: log login success and failure (username only, never the password) and edit, archive and restore actions with the acting user.

### 3.3 Running in production
- Add `waitress` to `requirements.txt`, since it works on Windows.
- Add `serve.py`, or document the command `waitress-serve --call app:create_app`.
- README section on running in production: environment variables, the waitress command, and backing up `employees.db`.

### 3.4 Tooling
- Make the database path in `dbhub.toml` easy to change for other machines, and document that in the README.
- Run `/review-quality` on each new module and fix any High or Critical findings before the phase is done.

---

## Verification (run at the end of each phase)

1. `py -m pip install -r requirements-dev.txt`, then `py -m pytest`: all tests pass.
2. `py app.py`, then check in the browser:
   - log in as `admin`: add, edit, archive and restore an employee, search, open the dashboard;
   - log in as `user`: no Edit or Archive links, and going straight to `/employees/1/edit` gives 403.
3. `db-hub` MCP: `search_objects` shows the expected schema (the `archived` column and the unique email index after Phase 2).
4. `/review-quality` on `app.py`, `auth.py` and `employees.py`: no Critical or High findings.
5. Phase 3: `APP_ENV=production` without `SECRET_KEY` refuses to start; with it set, `waitress-serve --call app:create_app` serves the app.
