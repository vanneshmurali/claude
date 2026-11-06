import math
from flask import Blueprint, render_template, request
from auth import login_required, role_required
from db import get_db

bp = Blueprint("employees", __name__)

MAX_LEN = 100


def validate_employee(form):
    """Return (data, errors) for an add/edit form. data is only safe to save when errors is empty."""
    data, errors = {}, []
    for field in ("name", "department"):
        value = form.get(field, "").strip()
        if not value:
            errors.append(f"{field.capitalize()} is required.")
        elif len(value) > MAX_LEN:
            errors.append(f"{field.capitalize()} must be at most {MAX_LEN} characters.")
        data[field] = value

    email = form.get("email", "").strip()
    if email and ("@" not in email or len(email) > 254):
        errors.append("Email must be a valid address.")
    data["email"] = email

    salary = form.get("salary", "").strip()
    try:
        data["salary"] = float(salary) if salary else 0
        if not math.isfinite(data["salary"]) or data["salary"] < 0:
            errors.append("Salary must be a number of 0 or more.")
    except ValueError:
        errors.append("Salary must be a number of 0 or more.")
    return data, errors


@bp.route("/", methods=["GET", "POST"])
@login_required
def employees():
    errors, form, status = [], {}, 200
    con = get_db()
    if request.method == "POST":
        data, errors = validate_employee(request.form)
        if errors:
            form, status = request.form, 400
        else:
            con.execute("INSERT INTO employees (name, email, department, salary) VALUES (?, ?, ?, ?)",
                        (data["name"], data["email"], data["department"], data["salary"]))
            con.commit()
    rows = con.execute("SELECT name, email, department, salary FROM employees").fetchall()
    con.close()
    return render_template("employees.html", title="Employees", rows=rows, errors=errors, form=form), status


@bp.route("/dashboard")
@role_required("admin")
def dashboard():
    con = get_db()
    total, avg = con.execute("SELECT COUNT(*), COALESCE(AVG(salary), 0) FROM employees").fetchone()
    by_dept = con.execute("SELECT department, COUNT(*) FROM employees GROUP BY department").fetchall()
    con.close()
    return render_template("dashboard.html", title="Dashboard", total=total, avg=avg, by_dept=by_dept)
