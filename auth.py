import secrets
from functools import wraps
from flask import Blueprint, abort, redirect, render_template, request, session
from werkzeug.security import check_password_hash

bp = Blueprint("auth", __name__)

# username: (password hash, role) - hashes from werkzeug generate_password_hash
USERS = {
    "admin": ("scrypt:32768:8:1$Mm627klpS2ytZJw1$ade8db31b069d447c4b9ba20752c1b690460ed53e6b1aa35e08ea3dc72ae054f0a5d22c9732566f298c378dd320b1a07cb5c9cfc75ff16f20509908c48e7e7d9", "admin"),
    "user": ("scrypt:32768:8:1$8zXSoIan47xiwgSe$5f26e59d9f0f33880087f255d84590ead7ad4806c47504d9425a971b3a73494e19c63dd21552ffcf3599e2c27b1f4b41a7dcfec87c5edeeab36129842f951fc1", "user"),
}


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def check_csrf():
    if request.method == "POST":
        sent, expected = request.form.get("csrf_token", ""), session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(sent, expected):
            abort(400)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        u, p = request.form.get("username", ""), request.form.get("password", "")
        if u in USERS and check_password_hash(USERS[u][0], p):
            session.clear()
            session["user"], session["role"] = u, USERS[u][1]
            return redirect("/")
        error = "Invalid login"
    return render_template("login.html", title="Login", error=error)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/login")
