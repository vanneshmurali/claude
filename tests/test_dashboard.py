def test_requires_login(client):
    r = client.get("/dashboard")
    assert r.status_code == 302 and r.location == "/login"


def test_user_role_forbidden(client, login):
    login("user")
    assert client.get("/dashboard").status_code == 403


def test_user_does_not_see_dashboard_link(client, login):
    login("user")
    assert 'href="/dashboard"' not in client.get("/").get_data(as_text=True)


def test_admin_sees_stats(client, login, add):
    login("admin")
    add(name="Ann", department="IT", salary="1000")
    add(name="Bob", department="IT", salary="3000")
    add(name="Cy", department="HR", salary="")
    r = client.get("/dashboard")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Total employees: <b>3</b>" in html
    assert "Average salary: <b>1333.33</b>" in html
    assert "<li>IT: 2</li>" in html and "<li>HR: 1</li>" in html
