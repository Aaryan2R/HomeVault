from flask import Flask, render_template, request, redirect, url_for, send_file, session
from database import (init_db, upgrade_db, save_file, get_all_files, get_file_by_id,
                      delete_file, trash_file, get_trashed_files, restore_file,
                      search_files, get_files_by_folder, get_files_by_owner,
                      get_shared_files, toggle_shared,
                      create_user, check_login, get_all_users,
                      get_user_by_id, get_username_by_id, count_users,
                      get_storage_stats, rename_file, get_admin_stats, get_db)
from thumbnailer import generate_thumbnail
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename

# Load .env values before the app starts
load_dotenv()

app = Flask(__name__)
# Read secret key from environment variable
# If not found fall back to a random key
# (random key means sessions reset on restart — fine for dev)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'storage')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024


# small helper functions

def get_folder(filename):
    """
    Decides which category a file belongs to based on its extension.
    For example: photo.jpg → 'Photos', report.pdf → 'Documents'
    """
    ext = filename.rsplit('.', 1)[-1].lower()
    photos    = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'heic']
    videos    = ['mp4', 'mkv', 'mov', 'avi', 'webm', 'flv']
    documents = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv']
    if ext in photos:    return 'Photos'
    if ext in videos:    return 'Videos'
    if ext in documents: return 'Documents'
    return 'Others'


def format_size(bytes):
    """
    Turn bytes into a smaller readable format like KB, MB, or GB.
    This is mainly used in the templates.
    """
    if bytes < 1024:
        return str(bytes) + ' B'
    elif bytes < 1024 * 1024:
        return str(round(bytes / 1024, 1)) + ' KB'
    elif bytes < 1024 * 1024 * 1024:
        return str(round(bytes / (1024 * 1024), 1)) + ' MB'
    else:
        return str(round(bytes / (1024 * 1024 * 1024), 2)) + ' GB'


def group_files_by_date(files, sort='date_desc'):
    """
    Group files into simple date sections like Today or This Week.
    """
    today     = datetime.now().date()
    yesterday = today - timedelta(days=1)
    week_ago  = today - timedelta(days=7)
    groups = {}

    for file in files:
        try:
            if sort in ('exif_desc', 'exif_asc'):
                file_path = os.path.join(BASE_DIR, 'storage',
                                         file['folder'], file['filename'])
                date_str = get_exif_date(file_path) or file['upload_date']
            else:
                date_str = file['upload_date']

            file_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
        except (ValueError, TypeError, KeyError):
            file_date = today

        if file_date == today:
            label = 'Today'
        elif file_date == yesterday:
            label = 'Yesterday'
        elif file_date >= week_ago:
            label = 'This Week'
        else:
            label = datetime.strptime(date_str[:10], '%Y-%m-%d').strftime('%B %Y')

        if label not in groups:
            groups[label] = []
        groups[label].append(file)

    return groups


def get_exif_date(file_path):
    # Try to read the taken date from photo EXIF data.
    # If nothing is found, return None.
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img  = Image.open(file_path)
        exif = img._getexif()

        if exif is None:
            return None

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal':
                return value.replace(':', '-', 2)

        return None

    except Exception:
        return None


# Make helper functions available in Jinja templates
app.jinja_env.globals['format_size'] = format_size
app.jinja_env.globals['get_username'] = get_username_by_id


def ensure_folders():
    """
    Create the folders HomeVault needs before the app starts.
    This avoids upload errors when a folder is missing.
    """
    folders = [
        os.path.join(BASE_DIR, 'storage', 'Photos'),
        os.path.join(BASE_DIR, 'storage', 'Videos'),
        os.path.join(BASE_DIR, 'storage', 'Documents'),
        os.path.join(BASE_DIR, 'storage', 'Others'),
        os.path.join(BASE_DIR, 'static', 'thumbnails'),
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)


# Simple login-check decorator used on protected routes

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


# authentication routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If the user is already logged in, send them to the dashboard
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
    # The first account is open registration.
    # After that, only an admin should add more users.
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
            # The very first account becomes admin
            if first_user:
                role = 'admin'

            user_id = create_user(username, password, role)

            if user_id is None:
                error = 'Username already taken'
            else:
                if first_user:
                    # Log in immediately after creating the first account
                    session['user_id']  = user_id
                    session['username'] = username
                    session['role']     = 'admin'
                    return redirect(url_for('home'))
                else:
                    return redirect(url_for('admin_users'))

    return render_template('register.html', error=error, first_user=first_user)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


# main app routes

@app.route('/')
@login_required
def home():
    query  = request.args.get('search', '')
    folder = request.args.get('folder', '')
    view   = request.args.get('view', 'mine')  # mine, all, or shared
    sort   = request.args.get('sort', 'date_desc')

    user_id = session['user_id']
    role    = session['role']

    # Admin gets the extra all-files view
    if role == 'admin' and view == 'all':
        if query:
            files = search_files(query, sort=sort)
        elif folder:
            files = get_files_by_folder(folder, sort=sort)
        else:
            files = get_all_files(sort=sort)

    elif view == 'shared':
        if query:
            files = [f for f in get_shared_files(sort=sort) if query.lower() in f['original_name'].lower()]
        elif folder:
            files = [f for f in get_shared_files(sort=sort) if f['folder'] == folder]
        else:
            files = get_shared_files(sort=sort)

    else:  # normal default view
        if query:
            files = search_files(query, owner_id=user_id, sort=sort)
        elif folder:
            files = get_files_by_folder(folder, owner_id=user_id, sort=sort)
        else:
            files = get_files_by_owner(user_id, sort=sort)

    # EXIF date sort is done after the DB query because the date lives in the file itself
    if sort in ('exif_desc', 'exif_asc'):
        def exif_sort_key(file):
            file_path = os.path.join(BASE_DIR, 'storage',
                                     file['folder'], file['filename'])
            exif_date = get_exif_date(file_path)
            return exif_date if exif_date else file['upload_date']

        reverse = (sort == 'exif_desc')
        files   = sorted(files, key=exif_sort_key, reverse=reverse)

    # Right panel stats use only the current user in normal view.
    # Admin can see global stats in the all-files view.
    if view == 'mine' or role != 'admin':
        stats = get_storage_stats(owner_id=user_id)
    else:
        stats = get_storage_stats()

    grouped_files = group_files_by_date(files, sort=sort)
    my_count = len(get_files_by_owner(user_id))
    trash_count = len(get_trashed_files(owner_id=user_id if role != 'admin' else None))

    return render_template('index.html',
                           files=files,
                           grouped_files=grouped_files,
                           query=query,
                           folder=folder,
                           view=view,
                           sort=sort,
                           stats=stats,
                           my_count=my_count,
                           trash_count=trash_count)


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    files   = request.files.getlist('file')
    user_id = session['user_id']
    is_shared = 1 if request.form.get('is_shared') else 0

    if not files or files[0].filename == '':
        return redirect(url_for('home'))

    for file in files:
        if file.filename == '':
            continue

        safe_name   = secure_filename(file.filename)
        if not safe_name:
            continue

        folder      = get_folder(safe_name)
        ext         = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
        unique_name = str(uuid.uuid4()) + ('.' + ext if ext else '')
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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return 'ok', 200

    return redirect(url_for('home'))


@app.route('/download/<int:file_id>')
@login_required
def download(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return 'File not found', 404

    # Files in trash should not open from here
    if file['is_deleted']:
        return 'File not found', 404

    # Members can only download their own files or shared ones
    if role != 'admin' and file['owner_id'] != user_id and not file['is_shared']:
        return 'Access denied', 403

    file_path = os.path.join(BASE_DIR, 'storage', file['folder'], file['filename'])

    if not os.path.exists(file_path):
        return 'File not found on disk', 404

    return send_file(file_path, download_name=file['original_name'], as_attachment=True)




@app.route('/preview/<int:file_id>')
@login_required
def preview(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return 'File not found', 404

    # No preview for trashed files
    if file['is_deleted']:
        return 'File not found', 404

    # Preview follows the same access rule as download
    if role != 'admin' and file['owner_id'] != user_id and not file['is_shared']:
        return 'Access denied', 403

    file_path = os.path.join(BASE_DIR, 'storage', file['folder'], file['filename'])

    if not os.path.exists(file_path):
        return 'File not found on disk', 404

    # Guess the mime type from the extension so the browser knows how to open it

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'

    # Show the file in the browser instead of forcing a download
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=False,
        download_name=file['original_name']
    )



# Routes below change app data, so they stay POST

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return redirect(url_for('home'))

    # Members should only delete their own files
    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    trash_file(file_id)
    return redirect(url_for('home'))


@app.route('/share/<int:file_id>', methods=['POST'])
@login_required
def share(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return redirect(url_for('home'))

    # Do not allow sharing from the trash
    if file['is_deleted']:
        return redirect(url_for('home'))

    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    toggle_shared(file_id)
    return redirect(url_for('home'))


# trash-related routes

@app.route('/trash')
@login_required
def trash():
    user_id     = session['user_id']
    role        = session['role']
    my_count    = len(get_files_by_owner(user_id))
    trash_count = len(get_trashed_files(owner_id=user_id if role != 'admin' else None))

    if role == 'admin':
        files = get_trashed_files()
    else:
        files = get_trashed_files(owner_id=user_id)

    return render_template('trash.html',
                           files=files,
                           my_count=my_count,
                           trash_count=trash_count)


@app.route('/empty_trash', methods=['POST'])
@login_required
def empty_trash():
    user_id = session['user_id']
    role    = session['role']

    if role == 'admin':
        files = get_trashed_files()
    else:
        files = get_trashed_files(owner_id=user_id)

    for file in files:
        file_path = os.path.join(BASE_DIR, 'storage',
                                 file['folder'], file['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        thumb_path = os.path.join(BASE_DIR, 'static', 'thumbnails',
                                  str(file['id']) + '.jpg')
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        delete_file(file['id'])

    return redirect(url_for('trash'))


@app.route('/restore/<int:file_id>', methods=['POST'])
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


@app.route('/permanent_delete/<int:file_id>', methods=['POST'])
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


@app.route('/rename/<int:file_id>', methods=['POST'])
@login_required
def rename(file_id):
    file    = get_file_by_id(file_id)
    user_id = session['user_id']
    role    = session['role']

    if file is None:
        return 'File not found', 404

    if file['is_deleted']:
        return 'File not found', 404

    if role != 'admin' and file['owner_id'] != user_id:
        return 'Access denied', 403

    new_name = request.form.get('name', '').strip()

    if not new_name:
        return 'Name cannot be empty', 400

    rename_file(file_id, new_name)
    return 'ok', 200


# admin routes

@app.route('/admin/users')
@admin_required
def admin_users():
    stats = get_admin_stats()
    return render_template('admin_users.html', stats=stats)


@app.route('/settings')
@login_required
def settings():
    user_id = session['user_id']
    user    = get_user_by_id(user_id)
    stats   = get_storage_stats(owner_id=user_id)
    return render_template('settings.html', user=user, stats=stats)


@app.route('/settings/change_password', methods=['POST'])
@login_required
def change_password():
    from werkzeug.security import check_password_hash, generate_password_hash
    user_id     = session['user_id']
    current     = request.form.get('current_password', '')
    new_pass    = request.form.get('new_password', '')
    confirm     = request.form.get('confirm_password', '')

    user = get_user_by_id(user_id)

    if not check_password_hash(user['password'], current):
        return render_template('settings.html', user=user,
                               stats=get_storage_stats(owner_id=user_id),
                               error='Current password is incorrect',
                               tab='account')

    if new_pass != confirm:
        return render_template('settings.html', user=user,
                               stats=get_storage_stats(owner_id=user_id),
                               error='New passwords do not match',
                               tab='account')

    if len(new_pass) < 4:
        return render_template('settings.html', user=user,
                               stats=get_storage_stats(owner_id=user_id),
                               error='Password must be at least 4 characters',
                               tab='account')

    conn   = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password = ? WHERE id = ?',
                   (generate_password_hash(new_pass), user_id))
    conn.commit()
    conn.close()

    return render_template('settings.html', user=user,
                           stats=get_storage_stats(owner_id=user_id),
                           success='Password changed successfully',
                           tab='account')


@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_view_user(user_id):
    user  = get_user_by_id(user_id)

    if user is None:
        return 'User not found', 404

    files = get_files_by_owner(user_id)
    return render_template('admin_view_user.html', user=user, files=files)


if __name__ == '__main__':
    ensure_folders()
    init_db()
    upgrade_db()
    # Read debug mode from .env.
    # Keep it off by default.
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', debug=debug_mode, threaded=True)
