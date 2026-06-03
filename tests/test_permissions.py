"""This file tests Member and Admin restrictions."""


def test_member_access_denied_for_admin_route(client):
    """Verify that a member cannot access the admin user list."""

    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["role"] = "member"
        sess["username"] = "member1"
        sess["_fresh"] = True

    resp = client.get("/admin/users")

    assert resp.status_code in [403, 302]


def test_admin_access_granted_for_admin_route(client):
    """Verify that an admin CAN access the admin user list."""

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"
        sess["username"] = "admin1"
        sess["_fresh"] = True

    resp = client.get("/admin/users")

    assert resp.status_code == 200
