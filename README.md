# HomeVault 🗄️

A lightweight self-hosted private cloud storage system for home and family use.
Think Google Drive — but local, private, and fully yours. No internet required,
no monthly fees, no data leaving your house.

Built as a BCA final year project using Python, Flask, and SQLite.

---

## What is HomeVault?

Most people either pay for cloud storage or dump everything into one messy folder.
HomeVault gives you organized, private, local storage with a clean browser-based UI.

Upload files from any device on your home network. HomeVault automatically sorts
them into Photos, Videos, Documents, and Others — generates thumbnails for images,
stores metadata in SQLite, and lets you search, filter, preview, download, and manage
everything from a modern dashboard that looks and feels like a real cloud storage app.

Inspired by Google Drive and Google Photos, but runs entirely on your own hardware.

---

## Features

### Core Storage
- 📤 Multi-file upload directly from the browser (drag and drop supported)
- 📁 Auto-categorization into Photos, Videos, Documents, and Others
- 🖼️ Automatic thumbnail generation for photo uploads
- 👁️ File preview in browser — images, videos, PDFs open without downloading
- ⬇️ Download files from any device on your local network
- 🔍 Search files by name
- 🗂️ Filter files by category
- 🔲 Grid and list view toggle (like Google Drive)
- 🗑️ Trash system — soft delete with restore and permanent delete

### Users and Access
- 👤 User authentication — login, register, logout
- 👨‍👩‍👧 Multi-user support — each user has their own private space
- 🔐 Role-based access — Admin sees everything, Members see only their own files
- 🤝 Shared files — mark any file as public so all users on the network can access it
- 🛡️ Permission checks — members cannot download, preview, or modify other users' files

### UI and Experience
- 🌙 Professional dark mode — dark slate blues, not pure black, remembers preference
- 📱 Fully responsive — works on desktop, tablet, and mobile
- 📊 Storage breakdown panel — see how much space each category uses
- 🎨 Modern dashboard design with sidebar navigation and category cards

### Security
- Passwords hashed with Werkzeug — never stored as plain text
- Session-based authentication with signed cookies
- All data-changing actions use POST requests — not GET links
- Trashed files are fully blocked from download, preview, and share
- Files stay entirely on your own machine — nothing leaves your network

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python, Flask                     |
| Database   | SQLite (built into Python)        |
| Frontend   | HTML, CSS, Jinja2, JavaScript     |
| Images     | Pillow (thumbnail generation)     |
| Auth       | Flask sessions, Werkzeug hashing  |

---

## How It Works

HomeVault uses two storage layers:

```
Uploaded file → saved to disk under storage/Photos/ (or Videos, Documents, Others)
File metadata → saved to SQLite database (homevault.db)
```

When you upload a file:
1. Flask checks if you are logged in
2. File type is detected from the extension
3. A unique UUID filename is generated to avoid conflicts
4. File is saved to the correct folder on disk
5. Metadata (original name, size, category, date, owner) is saved to SQLite
6. A thumbnail is generated in the background if the file is a photo

Each file has two names in the database:
- `filename` — the UUID name on disk (prevents conflicts between users)
- `original_name` — the name the user uploaded (shown in the UI)

---

## User Roles

| Role   | What they can do                                              |
|--------|---------------------------------------------------------------|
| Admin  | See and manage all users' files, create accounts, access everything |
| Member | See only their own files and files marked as shared           |

The first user to register automatically becomes Admin.
After that, only the Admin can create new accounts from the Manage Users page.

---

## Project Structure

```text
HomeVault/
├── app.py                   # Flask server — all routes and logic
├── database.py              # SQLite operations — all database functions
├── thumbnailer.py           # Thumbnail generation using Pillow
├── requirements.txt         # Python dependencies
├── templates/
│   ├── base.html            # Shared sidebar and layout (all pages extend this)
│   ├── index.html           # Main file dashboard
│   ├── login.html           # Login page
│   ├── register.html        # Register page
│   ├── trash.html           # Trash / deleted files
│   ├── admin_users.html     # Admin — list of all users
│   └── admin_view_user.html # Admin — view one user's files
├── static/
│   ├── css/
│   │   └── style.css        # Full design system with dark mode
│   ├── js/
│   │   └── app.js           # Dark mode, menus, preview modal, grid toggle
│   └── thumbnails/          # Auto-generated photo thumbnails
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
git clone https://github.com/Aaryan2R/HomeVault.git
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

### 4. Run the app

```bash
python app.py
```

The app automatically creates all required storage folders on startup.
No manual folder creation needed.

### 5. Open in your browser

```
http://127.0.0.1:5000
```

### 6. First time setup

Go to `/register` — the first account you create is automatically set as Admin.
After that, only the Admin can create new accounts from the Manage Users page.

### 7. Access from other devices on your home network

The app already runs on all network interfaces by default. Find your PC's local IP:

```powershell
ipconfig
```

Look for IPv4 Address under your Wi-Fi adapter, then open from any device on the same network:

```
http://192.168.x.x:5000
```

---

## Security Notes

- Passwords are hashed using Werkzeug — never stored as plain text
- Sessions are cookie-based and signed with a secret key
- File access is permission-checked on every route — members cannot access other users' private files
- Trashed files are fully blocked from download, preview, and share
- All state-changing actions (delete, share, restore, logout) use POST requests
- Files never leave your local machine or network

---

## Notes

- This is a local-first project. Files stay on the machine running the app.
- `venv/`, `storage/`, `static/thumbnails/`, and `homevault.db` are excluded
  from version control via `.gitignore`.
- The repository contains only source code, templates, and configuration files.

---

## Upcoming Improvements

These features are planned for the next phase of development:

### Deployment and Installation
- [ ] Static IP configuration guide for stable home network access
- [ ] Nginx reverse proxy setup — access via `http://homevault` instead of IP address
- [ ] Auto IP watcher — detects network changes and updates Nginx config automatically
- [ ] PyInstaller packaging — convert app to a portable .exe (no Python required)
- [ ] NSSM Windows Service — Flask starts automatically on system boot
- [ ] Inno Setup installer — full `HomeVault_Setup.exe` one-click Windows installer

### Features
- [ ] File rename from the UI
- [ ] Move files between folders from the UI
- [ ] Pagination — load files in batches for large collections
- [ ] Encrypted personal vault per user (locker feature)
- [ ] File sharing via generated links (share with non-users)
- [ ] Android app — automatic background photo and video backup

### Polish
- [ ] Secret key moved to environment variable (not hardcoded)
- [ ] Production server mode (Waitress instead of Flask dev server)
- [ ] Better error pages (custom 404, 403, 500)

---

## Why Not Just Use Google Drive?

| Feature              | Google Drive     | HomeVault          |
|----------------------|------------------|--------------------|
| Cost                 | Paid after 15 GB | Free               |
| Privacy              | Data on Google   | Data stays with you|
| Internet required    | Yes              | No                 |
| Multi-user support   | Paid plans only  | Built in           |
| File preview         | Yes              | Yes                |
| Dark mode            | Yes              | Yes                |
| Custom control       | No               | Full               |
| Setup complexity     | None             | Minimal            |

---

## License

MIT — free to use, modify, and distribute.
