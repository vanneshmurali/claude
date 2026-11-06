import sqlite3
from flask import current_app


def init_db(path):
    # Schema bootstrap; add idempotent ALTERs here when columns are added.
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS employees "
                "(id INTEGER PRIMARY KEY, name TEXT, email TEXT, department TEXT, salary REAL)")
    con.commit()
    con.close()


def get_db():
    return sqlite3.connect(current_app.config["DB"])
