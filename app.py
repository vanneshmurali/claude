import os
import secrets
from flask import Flask
import auth
import employees
from db import init_db


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        # Without SECRET_KEY a random key is used, so sessions reset on every restart.
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DB=os.environ.get("EMPLOYEES_DB", "employees.db"),
    )
    app.config.update(config or {})
    init_db(app.config["DB"])

    app.jinja_env.globals["csrf_token"] = auth.csrf_token
    app.before_request(auth.check_csrf)
    app.register_blueprint(auth.bp)
    app.register_blueprint(employees.bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=os.environ.get("FLASK_DEBUG") == "1")
