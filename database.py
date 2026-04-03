import sqlite3
from datetime import datetime
import os

def get_db():
    conn = sqlite3.connect('homevault.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            folder TEXT NOT NULL,
            upload_date TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print('Database Ready !!!')


def save_file(filename, original_name, file_type, file_size, folder, upload_date):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO files (filename, original_name, file_type, file_size, folder, upload_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (filename, original_name, file_type, file_size, folder, upload_date))

    file_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return file_id


def get_all_files():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT * FROM files
                   WHERE is_deleted = 0
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


def search_files(query):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM files
        WHERE original_name LIKE ? AND is_deleted = 0
        ORDER BY upload_date DESC
    ''', ('%' + query + '%',))

    files = cursor.fetchall()
    conn.close()
    return files


def get_files_by_folder(folder):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM files
        WHERE folder = ? AND is_deleted = 0
        ORDER BY upload_date DESC
    ''', (folder,))

    files = cursor.fetchall()
    conn.close()
    return files


def upgrade_db():
    conn = get_db()
    cursor = conn.cursor()

    # Add is_deleted column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE files ADD COLUMN is_deleted INTEGER DEFAULT 0')
        print('Added is_deleted column')
    except:
        pass  # column already exists, skip

    # Add deleted_at column if it doesn't exist
    try:
        cursor.execute('ALTER TABLE files ADD COLUMN deleted_at TEXT DEFAULT NULL')
        print('Added deleted_at column')
    except:
        pass  # column already exists, skip

    conn.commit()
    conn.close()
    
    
    
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


def get_trashed_files():
    conn = get_db()
    cursor = conn.cursor()

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