import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'homevault.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filename     TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type    TEXT NOT NULL,
            file_size    INTEGER NOT NULL,
            folder       TEXT NOT NULL,
            upload_date  TEXT NOT NULL,
            is_deleted   INTEGER DEFAULT 0,
            deleted_at   TEXT DEFAULT NULL,
            owner_id     INTEGER DEFAULT NULL,
            is_shared    INTEGER DEFAULT 0
        )
    ''')

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL,
            role       TEXT NOT NULL DEFAULT 'member',
            created_at TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print('Database Ready !!!')


def upgrade_db():
    conn = get_db()
    cursor = conn.cursor()

    # Add new columns to existing databases safely
    new_columns = [
        'ALTER TABLE files ADD COLUMN is_deleted INTEGER DEFAULT 0',
        'ALTER TABLE files ADD COLUMN deleted_at TEXT DEFAULT NULL',
        'ALTER TABLE files ADD COLUMN owner_id INTEGER DEFAULT NULL',
        'ALTER TABLE files ADD COLUMN is_shared INTEGER DEFAULT 0',
    ]

    for sql in new_columns:
        try:
            cursor.execute(sql)
        except:
            pass  # column already exists, skip

    conn.commit()
    conn.close()


# ─── User functions ───────────────────────────────────────────

def create_user(username, password, role='member'):
    conn = get_db()
    cursor = conn.cursor()

    # Check if username already exists
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return None  # username taken

    hashed   = generate_password_hash(password)
    created  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO users (username, password, role, created_at)
        VALUES (?, ?, ?, ?)
    ''', (username, hashed, role, created))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role, created_at FROM users ORDER BY created_at')
    users = cursor.fetchall()
    conn.close()
    return users


def check_login(username, password):
    user = get_user_by_username(username)
    if user is None:
        return None  # user not found
    if check_password_hash(user['password'], password):
        return user  # password correct
    return None      # wrong password


def count_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ─── File functions ───────────────────────────────────────────

def save_file(filename, original_name, file_type, file_size, folder, upload_date, owner_id, is_shared=0):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO files (filename, original_name, file_type, file_size, folder, upload_date, owner_id, is_shared)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (filename, original_name, file_type, file_size, folder, upload_date, owner_id, is_shared))

    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id


def get_all_files():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM files WHERE is_deleted = 0 ORDER BY upload_date DESC
    ''')
    files = cursor.fetchall()
    conn.close()
    return files


def get_files_by_owner(owner_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM files 
        WHERE owner_id = ? AND is_deleted = 0 
        ORDER BY upload_date DESC
    ''', (owner_id,))
    files = cursor.fetchall()
    conn.close()
    return files


def get_shared_files():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM files 
        WHERE is_shared = 1 AND is_deleted = 0 
        ORDER BY upload_date DESC
    ''')
    files = cursor.fetchall()
    conn.close()
    return files


def get_file_by_id(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    file = cursor.fetchone()
    conn.close()
    return file


def get_files_by_folder(folder, owner_id=None):
    conn = get_db()
    cursor = conn.cursor()

    if owner_id:
        cursor.execute('''
            SELECT * FROM files
            WHERE folder = ? AND owner_id = ? AND is_deleted = 0
            ORDER BY upload_date DESC
        ''', (folder, owner_id))
    else:
        cursor.execute('''
            SELECT * FROM files
            WHERE folder = ? AND is_deleted = 0
            ORDER BY upload_date DESC
        ''', (folder,))

    files = cursor.fetchall()
    conn.close()
    return files


def search_files(query, owner_id=None):
    conn = get_db()
    cursor = conn.cursor()

    if owner_id:
        cursor.execute('''
            SELECT * FROM files
            WHERE original_name LIKE ? AND owner_id = ? AND is_deleted = 0
            ORDER BY upload_date DESC
        ''', ('%' + query + '%', owner_id))
    else:
        cursor.execute('''
            SELECT * FROM files
            WHERE original_name LIKE ? AND is_deleted = 0
            ORDER BY upload_date DESC
        ''', ('%' + query + '%',))

    files = cursor.fetchall()
    conn.close()
    return files


def delete_file(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    file = cursor.fetchone()

    if file is None:
        conn.close()
        return False

    cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return file


def trash_file(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    file = cursor.fetchone()

    if file is None:
        conn.close()
        return False

    deleted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE files SET is_deleted = 1, deleted_at = ?
        WHERE id = ?
    ''', (deleted_at, file_id))

    conn.commit()
    conn.close()
    return file


def get_trashed_files(owner_id=None):
    conn = get_db()
    cursor = conn.cursor()

    if owner_id:
        cursor.execute('''
            SELECT * FROM files 
            WHERE is_deleted = 1 AND owner_id = ?
            ORDER BY deleted_at DESC
        ''', (owner_id,))
    else:
        cursor.execute('''
            SELECT * FROM files 
            WHERE is_deleted = 1
            ORDER BY deleted_at DESC
        ''')

    files = cursor.fetchall()
    conn.close()
    return files


def restore_file(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE files SET is_deleted = 0, deleted_at = NULL
        WHERE id = ?
    ''', (file_id,))
    conn.commit()
    conn.close()


def toggle_shared(file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT is_shared FROM files WHERE id = ?', (file_id,))
    file = cursor.fetchone()

    if file is None:
        conn.close()
        return

    # flip 0 to 1 or 1 to 0
    new_value = 1 if file['is_shared'] == 0 else 0
    cursor.execute('UPDATE files SET is_shared = ? WHERE id = ?', (new_value, file_id))
    conn.commit()
    conn.close()
