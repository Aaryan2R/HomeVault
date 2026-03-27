# HomeVault 🗄️

A lightweight self-hosted private cloud storage system for home and family use.
Think Google Drive — but local, private, and fully yours. No internet required,
no monthly fees, no data leaving your house.

Built as a BCA final year project using Python, Flask, and SQLite.

---

## What is HomeVault?

Most people either pay for cloud storage or dump everything into one messy folder.
HomeVault gives you organized, private, local storage with a clean browser-based UI.

Upload files from any device on your network, and HomeVault automatically sorts
them into Photos, Videos, Documents, and Others — generates thumbnails for images,
stores metadata in SQLite, and lets you search, filter, download, and delete
everything from a simple dashboard.

Inspired by Google Drive and Google Photos, but runs entirely on your own hardware.

---

## Features

- 📤 Upload files directly from the browser
- 📁 Auto-categorization into Photos, Videos, Documents, and Others
- 🖼️ Automatic thumbnail generation for photo uploads
- 🔍 Search files by name
- 🗂️ Filter files by category
- ⬇️ Download files from any device on your local network
- 🗑️ Delete files with confirmation (removes from disk and database)
- 💾 SQLite database — no external database setup needed
- 🚀 Lightweight — runs on any old PC, laptop, or Raspberry Pi

---

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python, Flask           |
| Database   | SQLite                  |
| Frontend   | HTML, CSS, Jinja2       |
| Images     | Pillow                  |

---

## How It Works

HomeVault uses two storage layers:

```
Uploaded file → saved to disk under storage/Photos/ (or Videos, Documents, Others)
File metadata → saved to SQLite database (homevault.db)
```

When you upload a file:
1. Flask receives it and detects the file type from the extension
2. A unique UUID filename is generated to avoid conflicts
3. The file is saved to the correct folder on disk
4. Metadata (original name, size, category, date) is recorded in SQLite
5. A thumbnail is generated if the file is a photo

Each file in the database has two names:
- `filename` — the UUID name used on disk (prevents conflicts)
- `original_name` — the name you uploaded (shown in the UI)

---

## Project Structure

```text
HomeVault/
├── app.py              # Flask server — all routes and logic
├── database.py         # SQLite operations — save, fetch, delete
├── thumbnailer.py      # Thumbnail generation using Pillow
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Main UI template (Jinja2)
├── static/
│   ├── css/
│   │   └── style.css   # Stylesheet
│   └── thumbnails/     # Auto-generated photo thumbnails
└── storage/
    ├── Photos/
    ├── Videos/
    ├── Documents/
    └── Others/
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/HomeVault.git
cd HomeVault
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows PowerShell:
```powershell
venv\Scripts\Activate.ps1
```

Windows Command Prompt:
```bat
venv\Scripts\activate.bat
```

Linux / Mac:
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create required folders

Linux / Mac:
```bash
mkdir -p storage/Photos storage/Videos storage/Documents storage/Others static/thumbnails
```

Windows PowerShell:
```powershell
mkdir storage\Photos, storage\Videos, storage\Documents, storage\Others, static\thumbnails
```

### 5. Run the app

```bash
python app.py
```

### 6. Open in your browser

```
http://127.0.0.1:5000
```

To access from another device on the same network, run with:

```bash
flask run --host=0.0.0.0
```

Then open `http://<your-pc-ip>:5000` from any device on the same Wi-Fi.

---

## Notes

- This is a local-first project. Files stay on the machine running the app.
- `venv/`, `storage/`, `static/thumbnails/`, and `homevault.db` are excluded
  from version control via `.gitignore`.
- The repo contains only source code, templates, and setup files.

---

## Roadmap

Features planned for future versions:

- [ ] Multi-file upload in one go
- [ ] File preview in browser (images, PDFs, videos)
- [ ] Rename files from the UI
- [ ] Trash / restore system instead of permanent delete
- [ ] Storage usage analytics dashboard
- [ ] Multi-user support with personal and shared spaces
- [ ] Authentication (login / register)
- [ ] Mobile app for automatic photo backup

---

## Why Not Just Use Google Drive?

| Feature              | Google Drive     | HomeVault          |
|----------------------|------------------|--------------------|
| Cost                 | Paid after 15GB  | Free               |
| Privacy              | Data on Google   | Data stays with you|
| Internet required    | Yes              | No                 |
| Custom control       | No               | Full               |
| Setup complexity     | None             | Minimal            |

---

## License

MIT — free to use, modify, and distribute.

---
