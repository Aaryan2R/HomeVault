"""
This file provides the database mocking and provides the
Flask client fixture to the test files.
"""

import pytest
import os
import tempfile
from app import app as flask_app
import database


@pytest.fixture
def client(monkeypatch):
    """
    Fixture providing a Flask test client with a temporary database
    and initialized storage directory.
    """

    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    monkeypatch.setattr(database, "DB_PATH", db_path)

    storage_dir = os.path.join("storage", "Documents")
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

    database.init_db()

    flask_app.config.update(
        {"TESTING": True, "SECRET_KEY": "dev_key_for_testing"}
    )

    with flask_app.test_client() as client:
        yield client

    if os.path.exists(db_path):
        os.unlink(db_path)
