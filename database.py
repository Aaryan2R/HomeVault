#database.py
import sqlite3
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
                upload_DATE TEXT NOT NULL
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
                SELECT * FROM files ORDER BY upload_date DESC
                   ''')
    
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


def search_files(query):
    conn  = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
                    SELECT * FROM files
                    WHERE original_name LIKE ?
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
                    WHERE folder = ?
                    ORDER BY upload_date DESC
                   ''', (folder,))
    
    files = cursor.fetchall()
    conn.close()
    return files

