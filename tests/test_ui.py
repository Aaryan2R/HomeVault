"""This test file confirms that your core navigation is functional"""


def test_homepage_loads(client):
    """Verify that the home page loads successfully."""

    resp = client.get("/", follow_redirects=True)
    assert resp.status_code == 200


def test_login_page_works(client):
    """Verify that the login page loads successfully."""

    resp = client.get("/login")
    assert resp.status_code == 200
