# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

A small employee directory web app. Logged-in users can add and list employees.
Admins can also open a dashboard with headcount, average salary and a per-department breakdown.

The roadmap is in [docs/PLAN.md](docs/PLAN.md). Phase 1 (foundation) is done; Phases 2 and 3 are still to do.

## Tech Stack

| Layer      | Technology                                                   |
|------------|--------------------------------------------------------------|
| Language   | Python 3 (run with the `py` launcher on Windows)             |
| Web        | Flask 3.0 (app factory, blueprints, `render_template`)       |
| Database   | SQLite via the stdlib `sqlite3` module (`employees.db`)      |
| Templates  | Jinja2 files in `templates/`, all extending `base.html`      |
| Auth       | Flask signed-cookie session; users hard-coded in `USERS`     |
| Tests      | pytest + Flask test client                                   |

Dependencies are pinned in `requirements.txt` (runtime) and `requirements-dev.txt` (adds pytest).
There is no ORM, no build step, and no frontend framework.

## Project Structure

```
employee_app/
├── app.py              # create_app(): config, CSRF hook, blueprints; __main__ runs the dev server
├── db.py               # init_db(path) schema bootstrap, get_db() per-request connection
├── auth.py             # USERS, csrf_token/check_csrf, login_required/role_required, /login, /logout
├── employees.py        # validate_employee(), / (list + add), /dashboard
├── templates/          # base.html (layout + nav), login.html, employees.html, dashboard.html
├── tests/              # conftest.py fixtures + test_auth/test_employees/test_dashboard
├── requirements.txt / requirements-dev.txt / pytest.ini
├── employees.db        # SQLite database (created by init_db on startup)
├── README.md           # Run instructions and demo logins
├── .mcp.json           # MCP servers: db-hub (DBHub 1.5.0, employees.db), github (token from $GITHUB_PAT), gitlab (OAuth)
├── dbhub.toml          # db-hub config: execute_sql is read-only; the DSN path is absolute (machine-specific)
├── .claude/
│   ├── commands/
│   │   ├── review-quality.md   # /review-quality <file>: read-only review, writes reviews/<file>-review.md
│   │   └── build-phase.md      # /build-phase <n>: phase-coder -> quality-verifier -> bug-fixer
│   └── agents/
│       ├── phase-coder.md      # Implements one PLAN.md phase + tests + docs, reports files changed
│       ├── quality-verifier.md # Read-only review, writes reviews/phase-<n>-review.md (ID, severity, status)
│       ├── bug-fixer.md        # Fixes report issues one by one, runs pytest after each, updates Status
│       ├── pr-reviewer.md      # Reviews a GitHub PR / GitLab MR via MCP, writes reviews/pr-<n>-review.md
│       └── github-reviewer.md  # Reviews a GitHub PR, commit, compare or whole repo via the github MCP server
└── docs/
    ├── PLAN.md                 # Roadmap (Phases 1-3)
    ├── coding-conventions.md   # Backend and template rules (imported below)
    └── testing.md              # Test expectations (imported below)
```

New routes go in a blueprint module (`employees.py` for employee features), not in `app.py`.

## Build / Run / Test Commands

```powershell
py -m pip install -r requirements-dev.txt   # runtime + test dependencies
py app.py                                   # run the dev server at http://127.0.0.1:5000
py -m pytest                                # run the test suite

$env:SECRET_KEY = "<random>"     # optional: keeps sessions valid across restarts
$env:EMPLOYEES_DB = "other.db"   # optional: SQLite path (default employees.db)
$env:FLASK_DEBUG = "1"           # optional: debugger + auto-reload (local only)
```

Demo logins: `admin` / `admin123` (admin), `user` / `user123` (user).

## Coding Conventions and Testing

These rules live in separate files, imported here so they are always loaded:

- Coding conventions (backend, templates): @docs/coding-conventions.md
- Testing expectations (including security tests): @docs/testing.md

Update those files, not this one, when the rules change.

## Key Domain Rules

| Rule                                                       | Where it is enforced                       |
|------------------------------------------------------------|--------------------------------------------|
| `name` and `department` required, trimmed, at most 100 chars | `validate_employee()` (HTML `required` is UX only) |
| `email` optional; if given must contain `@`, at most 254 chars | `validate_employee()`                    |
| `salary` optional; blank becomes `0`; must be a finite number of 0 or more | `validate_employee()`    |
| Invalid input: status `400`, errors listed, typed values kept | `employees()` POST                       |
| Dashboard stats are computed live in SQL                   | `/dashboard` (`COUNT`, `AVG`, `GROUP BY`)  |
| Employee list shows name, email, department, salary        | `/` GET; `id` is never displayed           |

There is no update or delete endpoint yet (planned for Phase 2 as admin-only edit and archive, never hard
delete). Don't add one as a side effect of another change. Email is not unique; ask before adding a
constraint, because existing rows may conflict.

## Security

### Roles

| Role    | Employees list / add (`/`) | Dashboard (`/dashboard`) |
|---------|----------------------------|--------------------------|
| `admin` | ✅                          | ✅                        |
| `user`  | ✅                          | ❌ (`403`)                |
| (none)  | redirect to `/login`       | redirect to `/login`     |

### Auth Flow

1. `GET /login` renders the form. `csrf_token()` stores a random token in the session.
2. `POST /login` passes `check_csrf` (registered in `create_app`), then calls `check_password_hash` against `USERS`.
3. On success, the session is cleared, then `user` and `role` are set. Flask stores the session in a cookie signed
   with `SECRET_KEY`, which comes from the env var (a random key is used if it is unset).
4. Each protected route is guarded by `login_required` or `role_required(role)`.
5. `POST /logout` (a CSRF-protected form in the nav bar of `base.html`) clears the session.

To add or change a user, generate a hash and store only that:

```powershell
py -c "from werkzeug.security import generate_password_hash as g; print(g('new-password'))"
```

### Backend Conventions

- **Every route except `/login` has an auth decorator** from `auth.py`, placed under `@bp.route`:

  ```python
  @bp.route("/")
  @login_required            # no session -> redirect to /login
  def employees(): ...

  @bp.route("/dashboard")
  @role_required("admin")    # no session -> redirect; wrong role -> 403
  def dashboard(): ...
  ```

- Only the session carries identity. Don't trust role or user values from form fields, query strings or headers.

### Frontend Conventions

- Hiding the Dashboard link for non-admins (`{% if session.role == 'admin' %}` in `base.html`) is **UX only**.
  The real check is `role_required` on the route. Any new admin-only link must have a matching decorator.

### Hard Rules

- **No frontend-only auth checks.** Every restriction shown in a template must also exist on the route.
- **No committed secrets.** Read keys and tokens from the environment. Never hard-code `SECRET_KEY`.
- **No plaintext passwords.** Store only `generate_password_hash` output.
- **No POST form without the CSRF field**, and don't exempt routes from `check_csrf`.
- **State-changing actions are POST only** (including logout).
- **No string-built SQL.**
- **No `| safe` or `Markup` on user input.** Templates rely on Jinja autoescaping.

## Don't Do

- Don't commit `employees.db` changes or real employee data. Use a temp DB for tests and experiments.
- Don't add hard-delete, update, or bulk endpoints unless asked.
- Don't add heavyweight dependencies (ORM, SPA framework) for small changes.
- Don't change the demo logins in `README.md` without regenerating the hashes in `USERS`, and the reverse.
- Don't set `FLASK_DEBUG=1` anywhere except a local machine.
- Don't remove the `CREATE TABLE IF NOT EXISTS` bootstrap in `init_db()`.
