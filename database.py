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


def get_order_clause(sort):
    # map sort key from URL to safe SQL order text
    orders = {
        'date_desc': 'upload_date DESC',
        'date_asc':  'upload_date ASC',
        'name_asc':  'original_name ASC',
        'name_desc': 'original_name DESC',
        'size_desc': 'file_size DESC',
        'size_asc':  'file_size ASC',
    }
    return orders.get(sort, 'upload_date DESC')


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # table for files
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

    # table for users
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

    # for older db versions try adding missing columns
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
            pass  # maybe column already there

    conn.commit()
    conn.close()


# user functions

def create_user(username, password, role='member'):
    conn = get_db()
    cursor = conn.cursor()

    # check duplicate username first
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return None  # already used

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


def get_username_by_id(user_id):
    if user_id is None:
        return 'Unknown'
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user['username'] if user else 'Unknown'


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
        return None  # no such user
    if check_password_hash(user['password'], password):
        return user  # login ok
    return None      # wrong password


def count_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count


# file functions

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


def get_all_files(sort='date_desc'):
    conn = get_db()
    cursor = conn.cursor()
    order = get_order_clause(sort)
    cursor.execute(f'''
        SELECT * FROM files WHERE is_deleted = 0 ORDER BY {order}
    ''')
    files = cursor.fetchall()
    conn.close()
    return files


def get_files_by_owner(owner_id, sort='date_desc'):
    conn = get_db()
    cursor = conn.cursor()
    order = get_order_clause(sort)
    cursor.execute(f'''
        SELECT * FROM files 
        WHERE owner_id = ? AND is_deleted = 0 
        ORDER BY {order}
    ''', (owner_id,))
    files = cursor.fetchall()
    conn.close()
    return files


def get_shared_files(sort='date_desc'):
    conn = get_db()
    cursor = conn.cursor()
    order = get_order_clause(sort)
    cursor.execute(f'''
        SELECT * FROM files 
        WHERE is_shared = 1 AND is_deleted = 0 
        ORDER BY {order}
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


def get_files_by_folder(folder, owner_id=None, sort='date_desc'):
    conn = get_db()
    cursor = conn.cursor()
    order = get_order_clause(sort)

    if owner_id:
        cursor.execute(f'''
            SELECT * FROM files
            WHERE folder = ? AND owner_id = ? AND is_deleted = 0
            ORDER BY {order}
        ''', (folder, owner_id))
    else:
        cursor.execute(f'''
            SELECT * FROM files
            WHERE folder = ? AND is_deleted = 0
            ORDER BY {order}
        ''', (folder,))

    files = cursor.fetchall()
    conn.close()
    return files


def search_files(query, owner_id=None, sort='date_desc'):
    conn = get_db()
    cursor = conn.cursor()
    order = get_order_clause(sort)

    if owner_id:
        cursor.execute(f'''
            SELECT * FROM files
            WHERE original_name LIKE ? AND owner_id = ? AND is_deleted = 0
            ORDER BY {order}
        ''', ('%' + query + '%', owner_id))
    else:
        cursor.execute(f'''
            SELECT * FROM files
            WHERE original_name LIKE ? AND is_deleted = 0
            ORDER BY {order}
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

    # simple toggle
    new_value = 1 if file['is_shared'] == 0 else 0
    cursor.execute('UPDATE files SET is_shared = ? WHERE id = ?', (new_value, file_id))
    conn.commit()
    conn.close()


def rename_file(file_id, new_name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE files SET original_name = ?
        WHERE id = ?
    ''', (new_name, file_id))
    conn.commit()
    conn.close()


def get_admin_stats():
    conn   = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM files WHERE is_deleted = 0')
    total_files = cursor.fetchone()[0]

    cursor.execute('SELECT COALESCE(SUM(file_size), 0) FROM files WHERE is_deleted = 0')
    total_size = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM files WHERE is_deleted = 1')
    trash_count = cursor.fetchone()[0]

    cursor.execute('''
        SELECT u.id, u.username, u.role, u.created_at,
               COUNT(f.id) as file_count,
               COALESCE(SUM(f.file_size), 0) as total_size
        FROM users u
        LEFT JOIN files f ON f.owner_id = u.id AND f.is_deleted = 0
        GROUP BY u.id
        ORDER BY u.created_at
    ''')
    users = cursor.fetchall()

    conn.close()

    return {
        'total_users': total_users,
        'total_files': total_files,
        'total_size':  total_size,
        'trash_count': trash_count,
        'users':       users
    }


# storage stats

def get_storage_stats(owner_id=None):
    """
    Returns storage usage info for the dashboard.
    If owner_id is given, only counts that user's files.
    Only counts non-deleted files (not in trash).

    Returns a dictionary like:
    {
        'total_files': 42,
        'total_size': 157286400,       # bytes
        'categories': {
            'Photos':    {'count': 20, 'size': 80000000},
            'Videos':    {'count': 5,  'size': 50000000},
            'Documents': {'count': 12, 'size': 25000000},
            'Others':    {'count': 5,  'size': 2286400},
        }
    }
    """
    conn = get_db()
    cursor = conn.cursor()

    # where part changes if owner filter is there
    if owner_id:
        where = 'WHERE is_deleted = 0 AND owner_id = ?'
        params = (owner_id,)
    else:
        where = 'WHERE is_deleted = 0'
        params = ()

    # get count and size for each folder
    cursor.execute(f'''
        SELECT folder, COUNT(*) as count, COALESCE(SUM(file_size), 0) as size
        FROM files
        {where}
        GROUP BY folder
    ''', params)

    rows = cursor.fetchall()
    conn.close()

    # make final dict
    categories = {}
    total_files = 0
    total_size = 0

    for row in rows:
        categories[row['folder']] = {
            'count': row['count'],
            'size': row['size']
        }
        total_files += row['count']
        total_size += row['size']

    # keep all 4 categories even if count is zero
    for cat in ['Photos', 'Videos', 'Documents', 'Others']:
        if cat not in categories:
            categories[cat] = {'count': 0, 'size': 0}

    return {
        'total_files': total_files,
        'total_size': total_size,
        'categories': categories
    }
