"""This test covers uploading, deleting, and restoring."""

from io import BytesIO


def test_upload_and_delete(client):
    """Verify file upload, move to delete, and subsequent restoration."""

    client.post(
        "/register",
        data={"username": "u1", "password": "246", "confirm": "246"},
    )

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "u1"
        sess["role"] = "admin"
        sess["_fresh"] = True

    data = {"file": (BytesIO(b"dummy file content"), "test.txt")}
    resp = client.post(
        "/upload",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    client.post("/delete/1", follow_redirects=True)
    assert client.get("/download/1").status_code == 404

    client.post("/restore/1", follow_redirects=True)
    assert client.get("/download/1").status_code == 200
