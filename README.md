# HomeVault

HomeVault is a local private cloud storage web application built with Flask and SQLite. It is designed for home or family use and gives a simple browser-based way to upload, organize, search, download, and delete files while keeping the real files stored on the user's own computer.

The project is inspired by the idea of a lightweight Google Drive or Google Photos style experience, but it runs fully on local storage instead of external cloud servers. Metadata is stored in SQLite, files are saved on disk, and image thumbnails are generated for photo uploads.

## Features

- Upload files from the browser
- Automatic file categorization into Photos, Videos, Documents, and Others
- File metadata stored in SQLite
- Search files by name
- Filter files by category
- Download stored files
- Delete files from the system
- Generate thumbnails for photos
- Simple web dashboard for managing files

## Tech Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- Jinja2
- Pillow

## Project Structure

```text
HomeVault/
|-- app.py
|-- database.py
|-- thumbnailer.py
|-- requirements.txt
|-- templates/
|   `-- index.html
|-- static/
|   |-- css/
|   `-- thumbnails/
`-- storage/
    |-- Photos/
    |-- Videos/
    |-- Documents/
    `-- Others/
```

## How It Works

- `app.py` handles routes, upload logic, download logic, delete logic, and filtering.
- `database.py` manages the SQLite database and stores file metadata.
- `thumbnailer.py` creates thumbnails for uploaded photo files.
- `storage/` stores the real uploaded files on local disk.
- `homevault.db` stores metadata such as original filename, category, size, and upload date.

This project uses two storage layers:
- File storage: actual files are saved inside `storage/`
- Metadata storage: file information is stored in `homevault.db`

## Installation

1. Clone the repository:

```bash
git clone <your-repository-url>
cd HomeVault
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
venv\Scripts\activate.bat
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Create the required folders if they do not already exist:

```text
storage/Photos
storage/Videos
storage/Documents
storage/Others
static/thumbnails
```

6. Run the application:

```bash
python app.py
```

7. Open in your browser:

```text
http://127.0.0.1:5000
```

## Notes

- This is a local-first project, so files remain on the same computer where the app runs.
- `venv/`, `__pycache__/`, uploaded files, thumbnails, and the SQLite database should not be pushed to GitHub.
- The repository should only contain source code, templates, styles, and setup files needed to run the project.

## Future Scope

Possible future improvements:

- better file preview support
- rename files
- recycle bin or trash feature
- storage usage statistics
- personal and shared spaces for family users
- mobile backup support

## Repository Description

Local private cloud storage web app built with Flask and SQLite for uploading, organizing, searching, and managing files on local disk.
