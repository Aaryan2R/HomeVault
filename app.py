#app.py
from flask import Flask, render_template, request, redirect, url_for, send_file
from database import init_db, save_file, get_all_files, get_db, delete_file, search_files, get_files_by_folder
from thumbnailer import generate_thumbnail
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'storage'
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
    file = request.files['file']

    if file.filename == '':
        return 'No file selected'

    folder       = get_folder(file.filename)
    ext          = file.filename.rsplit('.', 1)[-1].lower()
    unique_name  = str(uuid.uuid4()) + '.' + ext
    save_path    = os.path.join('storage', folder, unique_name)
    upload_date  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    file = cursor.fetchone()
    conn.close()

    if file is None:
        return 'File not found', 404

    file_path = os.path.join('storage', file['folder'], file['filename'])

    return send_file(file_path, download_name=file['original_name'], as_attachment=True)


@app.route('/delete/<int:file_id>')
def delete(file_id):
    file = delete_file(file_id)

    if file:
        file_path = os.path.join('storage', file['folder'], file['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # also delete the thumbnail if it exists
        thumb_path = os.path.join('static', 'thumbnails', str(file['id']) + '.jpg')
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    return redirect(url_for('home'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, threaded=True)