# Coding Conventions

## Backend (Flask / Python)

- **App factory.** Build the app with `create_app(config=None)` in `app.py`. Never create a module-level
  `app`. Config comes from env vars, overridden by the `config` dict (used by tests).
- **Routes live in blueprints** (`auth.bp`, `employees.bp`). Keep the existing URLs stable.
- **One connection per request.** Call `get_db()`, do the work, `commit()` if you wrote anything, then `close()`.
- **Parameterised SQL only.** Never build SQL with f-strings or `+`.

  ```python
  # Good
  con.execute("INSERT INTO employees (name, email) VALUES (?, ?)", (name, email))
  # Never
  con.execute(f"INSERT INTO employees (name, email) VALUES ('{name}', '{email}')")
  ```

- **Schema changes go in `init_db()`** (`db.py`), so a fresh checkout still creates the table. If a column is
  added to an existing table, add an idempotent `ALTER TABLE` there, guarded by a `PRAGMA table_info` check.
  `CREATE TABLE IF NOT EXISTS` will not change an existing table.
- **Validate on the server.** All employee form input goes through `validate_employee(form)`, which returns
  `(data, errors)`. Save `data` only when `errors` is empty; otherwise re-render with status `400`.
- **Every route has an auth decorator** (`login_required` / `role_required`), see Security in `CLAUDE.md`.
- Keep the existing style: short functions, short variable names (`con`, `rows`), no type hints, double quotes.

## Templates / Frontend

- Templates live in `templates/` and extend `base.html` (layout, nav bar, logout form). Render with
  `render_template("x.html", title=..., ...)`.
- **Pass user data as template variables** and let Jinja autoescape it. Never use `| safe` or `Markup`
  on anything that came from a user.

  ```html
  <!-- Good: autoescaped -->
  <td>{{ name }}</td>
  <!-- Never: XSS -->
  <td>{{ name | safe }}</td>
  ```

- **Every `<form method="post">` must include the CSRF field**, or the request is rejected with `400`:

  ```html
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ```

- Plain HTML forms, no JavaScript. Keep it that way unless there is a real need.
