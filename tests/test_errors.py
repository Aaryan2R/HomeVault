"""This test confirms error-handling - invalid routes/ data."""


def test_404_on_invalid_route(client):
    """Verify that visiting a non-existent route returns a 404."""

    resp = client.get("/this-path-does-not-exist")
    assert resp.status_code == 404


def test_download_nonexistent_file(client):
    """Verify that requesting a non-existent file ID returns a 404."""

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "u1"
        sess["role"] = "member"

    resp = client.get("/download/99999")
    assert resp.status_code == 404
