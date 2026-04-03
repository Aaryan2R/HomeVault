from flask import Flask, render_template, request, redirect, url_for, send_file
from database import init_db, upgrade_db, save_file, get_all_files, get_file_by_id, delete_file, trash_file, get_trashed_files, restore_file, search_files, get_files_by_folder
from thumbnailer import generate_thumbnail
from datetime import datetime
import os
import uuid

app = Flask(__name__)

# BASE_DIR is the folder where app.py lives
# This makes all paths work no matter where you run Python from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'storage')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024


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
        kb = bytes / 1024
        return str(round(kb, 1)) + ' KB'
    elif bytes < 1024 * 1024 * 1024:
        mb = bytes / (1024 * 1024)
        return str(round(mb, 1)) + ' MB'
    else:
        gb = bytes / (1024 * 1024 * 1024)
        return str(round(gb, 2)) + ' GB'


app.jinja_env.globals['format_size'] = format_size


def ensure_folders():
    # Create all required folders if they don't exist
    folders = [
        os.path.join(BASE_DIR, 'storage', 'Photos'),
        os.path.join(BASE_DIR, 'storage', 'Videos'),
        os.path.join(BASE_DIR, 'storage', 'Documents'),
        os.path.join(BASE_DIR, 'storage', 'Others'),
        os.path.join(BASE_DIR, 'static', 'thumbnails'),
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)


@app.route('/')
def home():
    query  = request.args.get('search', '')
    folder = request.args.get('folder', '')

    if query:
        files = search_files(query)
    elif folder:
        files = get_files_by_folder(folder)
    else:
        files = get_all_files()

    return render_template('index.html', files=files, query=query, folder=folder)


@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('file')

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
            upload_date   = upload_date
        )

        generate_thumbnail(file_id, save_path, folder)

    return redirect(url_for('home'))


@app.route('/download/<int:file_id>')
def download(file_id):
    file = get_file_by_id(file_id)

    if file is None:
        return 'File not found', 404

    file_path = os.path.join(BASE_DIR, 'storage', file['folder'], file['filename'])

    return send_file(file_path, download_name=file['original_name'], as_attachment=True)


@app.route('/delete/<int:file_id>')
def delete(file_id):
    trash_file(file_id)
    return redirect(url_for('home'))


@app.route('/trash')
def trash():
    files = get_trashed_files()
    return render_template('trash.html', files=files)


@app.route('/restore/<int:file_id>')
def restore(file_id):
    restore_file(file_id)
    return redirect(url_for('trash'))


@app.route('/permanent_delete/<int:file_id>')
def permanent_delete(file_id):
    file = delete_file(file_id)

    if file:
        file_path = os.path.join(BASE_DIR, 'storage', file['folder'], file['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        thumb_path = os.path.join(BASE_DIR, 'static', 'thumbnails', str(file['id']) + '.jpg')
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    return redirect(url_for('trash'))


if __name__ == '__main__':
    ensure_folders()
    init_db()
    upgrade_db()
    app.run(debug=True, threaded=True)
