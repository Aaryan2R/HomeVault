"""
Test covers registration, login and "Access Denied" logic for non admin users.
"""


def test_registration_and_login(client):
    """Test user registration and verify subsequent successful login."""

    resp = client.post(
        "/register",
        data={
            "username": "testuser",
            "password": "password246",
            "confirm": "password246",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    resp = client.post(
        "/login",
        data={"username": "testuser", "password": "password246"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"testuser" in resp.data


def test_admin_accessed_denied(client):
    """Verify non-admin users receive a 403 Forbidden status on admin routes."""

    client.post(
        "/register",
        data={"username": "member", "password": "246", "confirm": "246"},
    )

    client.post("/login", data={"username": "member", "password": "246"})

    resp = client.get("/admin/users")
    assert resp.status_code == 302
