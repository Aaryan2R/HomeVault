from flask import Flask, render_template, request, redirect, url_for, send_file, session
from database import (init_db, upgrade_db, save_file, get_all_files, get_file_by_id,
                      delete_file, trash_file, get_trashed_files, restore_file,
                      search_files, get_files_by_folder, get_files_by_owner,
                      get_shared_files, toggle_shared,
                      create_user, check_login, get_all_users,
                      get_user_by_id, count_users)
from thumbnailer import generate_thumbnail
from datetime import datetime
from functools import wraps
import os
import uuid

app = Flask(__name__)
app.secret_key = 'homevault-secret-key-change-this-later'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'storage')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024


# ─── Helpers ──────────────────────────────────────────────────

def get_folder(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    photos    = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'heic']
    videos    = ['mp4', 'mkv', 'mov', 'avi', 'webm', 'flv']
    documents = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv']
    if ext in photos:    return 'Photos'
    if ext in videos:    return 'Videos'
    if ext in documents: return 'Documents'
    return 'Others'


def format_size(bytes):
    if bytes < 1024:
        return str(bytes) + ' B'
    elif bytes < 1024 * 1024:
        return str(round(bytes / 1024, 1)) + ' KB'
    elif bytes < 1024 * 1024 * 1024:
        return str(round(bytes / (1024 * 1024), 1)) + ' MB'
    else:
        return str(round(bytes / (1024 * 1024 * 1024), 2)) + ' GB'

app.jinja_env.globals['format_size'] = format_size


def ensure_folders():
    folders = [
        os.path.join(BASE_DIR, 'storage', 'Photos'),
        os.path.join(BASE_DIR, 'storage', 'Videos'),
        os.path.join(BASE_DIR, 'storage', 'Documents'),
        os.path.join(BASE_DIR, 'storage', 'Others'),
        os.path.join(BASE_DIR, 'static', 'thumbnails'),
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)


# ─── Login required decorator ─────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return 'Access denied', 403
        return f(*args, **kwargs)
    return decorated


# ─── Auth routes ──────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in go to home
    if 'user_id' in session:
        return redirect(url_for('home'))

    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = check_login(username, password)

        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            return redirect(url_for('home'))
        else:
            error = 'Incorrect username or password'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    # Only allow registration if no users exist yet (first user = admin)
    # After that only admin can create users
    first_user = count_users() == 0

    if not first_user and session.get('role') != 'admin':
        return redirect(url_for('login'))

    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        role     = request.form.get('role', 'member')

        if not username or not password:
            error = 'Username and password are required'
        elif password != confirm:
            error = 'Passwords do not match'
        elif len(password) < 4:
            error = 'Password must be at least 4 characters'
        else:
            # First user always becomes admin
            if first_user:
                role = 'admin'

            user_id = create_user(username, password, role)

            if user_id is None:
                error = 'Username already taken'
            else:
                if first_user:
                    # Log in automatically after first registration
                    session['user_id']  = user_id
                    session['username'] = username
                    session['role']     = 'admin'
                    return redirect(url_for('home'))
                else:
                    return redirect(url_for('admin_users'))

    return render_template('register.html', error=error, first_user=first_user)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── Main routes ──────────────────────────────────────────────

@app.route('/')
@login_required
def home():
    query  = request.args.get('search', '')
    folder = request.args.get('folder', '')
    view   = request.args.get('view', 'mine')  # mine / all / shared

    user_id = session['user_id']
    role    = session['role']

    # Admins can switch between views
    if role == 'admin' and view == 'all':
        if query:
            files = search_files(query)
        elif folder:
            files = get_files_by_folder(folder)
        else:
            files = get_all_files()

    elif view == 'shared':
        if query:
            files = [f for f in get_shared_files() if query.lower() in f['original_name'].lower()]
        elif folder:
            files = [f for f in get_shared_files() if f['folder'] == folder]
        else:
            files = get_shared_files()

    else:  # 'mine' - default for everyone
        if query:
            files = search_files(query, owner_id=user_id)
        elif folder:
            files = get_files_by_folder(folder, owner_id=user_id)
        else:
            files = get_files_by_owner(user_id)

    return render_template('index.html',
                           files=files,
                           query=query,
                           folder=folder,
                           view=view)


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    files   = request.files.getlist('file')
    user_id = session['user_id']
    is_shared = 1 if request.form.get('is_shared') else 0

    if not files or files[0].filename == '':
        return 'No file selected'

    for file in files:
        if file.filename == '':
            continue

        folder      = get_folder(file.filename)
        ext         = file.filename.rsplit('.', 1)[-1].lower()
        unique_name = str(uuid.uuid4()) + '.' + ext
        save_path   = os.path.join(BASE_DIR, 'storage', folder, unique_name)
        upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        file.save(save_path)

        file_id = save_file(
            filename      = unique_name,
            original_name = file.filename,
            file_type     = folder,
            file_size     = os.path.getsize(save_path),
            folder        = folder,
            upload_date   = upload_date,
            owner_id      = user_id,
            is_shared     = is_shared
        )

        generate_thumbnail(file_id, save_path, folder)

    return redirect(url_for('home'))


@app.route('/download/<int:file_id>')
@login_required
def download(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return 'File not found', 404

    # Members can only download their own files or shared files
    if role != 'admin' and file['owner_id'] != user_id and not file['is_shared']:
        return 'Access denied', 403

    file_path = os.path.join(BASE_DIR, 'storage', file['folder'], file['filename'])
    return send_file(file_path, download_name=file['original_name'], as_attachment=True)


@app.route('/delete/<int:file_id>')
@login_required
def delete(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return redirect(url_for('home'))

    # Members can only delete their own files
    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    trash_file(file_id)
    return redirect(url_for('home'))


@app.route('/share/<int:file_id>')
@login_required
def share(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return redirect(url_for('home'))

    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    toggle_shared(file_id)
    return redirect(url_for('home'))


# ─── Trash routes ─────────────────────────────────────────────

@app.route('/trash')
@login_required
def trash():
    user_id = session['user_id']
    role    = session['role']

    if role == 'admin':
        files = get_trashed_files()
    else:
        files = get_trashed_files(owner_id=user_id)

    return render_template('trash.html', files=files)


@app.route('/restore/<int:file_id>')
@login_required
def restore(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return redirect(url_for('trash'))

    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    restore_file(file_id)
    return redirect(url_for('trash'))


@app.route('/permanent_delete/<int:file_id>')
@login_required
def permanent_delete(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return redirect(url_for('trash'))

    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    file = delete_file(file_id)

    if file:
        file_path = os.path.join(BASE_DIR, 'storage', file['folder'], file['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        thumb_path = os.path.join(BASE_DIR, 'static', 'thumbnails', str(file['id']) + '.jpg')
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    return redirect(url_for('trash'))


# ─── Admin routes ─────────────────────────────────────────────

@app.route('/admin/users')
@admin_required
def admin_users():
    users = get_all_users()
    return render_template('admin_users.html', users=users)


@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_view_user(user_id):
    user  = get_user_by_id(user_id)
    files = get_files_by_owner(user_id)
    return render_template('admin_view_user.html', user=user, files=files)


if __name__ == '__main__':
    ensure_folders()
    init_db()
    upgrade_db()
    app.run(debug=True, threaded=True)
