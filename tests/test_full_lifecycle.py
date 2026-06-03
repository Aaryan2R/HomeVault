from io import BytesIO


def test_full_user_file_lifecycle(client):
    """
    Master flow test:
    Register user
    Login
    Upload file
    Admin verifies file exists
    User deletes file
    Admin verifies file is gone
    """

    # Register
    client.post(
        "/register",
        data={"username": "alice", "password": "123", "confirm": "123"},
    )

    # Login as User
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alice"
        sess["role"] = "member"
        sess["_fresh"] = True

    # Upload file
    data = {"file": (BytesIO(b"master test content"), "secret.txt")}
    client.post("/upload", data=data, content_type="multipart/form-data")

    # Login as Admin and verify file exists
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "admin"
        sess["_fresh"] = True

    # Assuming /download/1 is the path for the first uploaded file
    assert client.get("/download/1").status_code == 200

    # Switch back to User and delete
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alice"
        sess["role"] = "member"

    client.post("/delete/1", follow_redirects=True)

    # Admin verifies it's gone
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    assert client.get("/download/1").status_code == 404
