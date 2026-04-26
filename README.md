# HomeVault ⚡

### Your Personal Cloud Storage — Private, Local, Yours.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Aaryan2R/HomeVault)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

A lightweight self-hosted cloud storage system for home and family use.
Think Google Drive — but local, private, and fully yours. No internet required,
no monthly fees, no data leaving your house.

<br>

## Why HomeVault?

Most people either pay for cloud storage or dump everything into one messy folder.
HomeVault gives you organized, private, local storage with a clean browser-based UI.

Upload files from any device on your home network. HomeVault automatically sorts
them into **Photos, Videos, Documents, and Others** — generates thumbnails for images,
stores metadata in SQLite, and lets you search, filter, preview, download, and manage
everything from a modern dashboard that looks and feels like a real cloud app.

Inspired by Google Drive and Google Photos, but runs entirely on your own hardware.

---

## Features

### 📦 Core Storage
- Multi-file upload with real-time per-file progress bars
- Drag-and-drop upload support
- Auto-categorization into Photos, Videos, Documents, and Others
- Automatic thumbnail generation for photo uploads
- In-browser preview — images, videos, and PDFs open without downloading
- Download files from any device on your local network
- Search files by name
- Filter by category
- Grid and list view toggle
- Sort by date, name, size, or actual photo date (EXIF metadata)
- Files grouped by date — Today, Yesterday, This Week, Month Year

### 🗑️ File Management
- Trash system with soft delete, restore, and permanent delete
- Empty trash to bulk-remove all trashed files
- Rename files inline by double-clicking the filename

### 👥 Users & Access
- User authentication — login, register, logout
- Multi-user support — each user has their own private space
- Role-based access — Admin sees everything, Members see only their own files
- Shared files — mark any file as public so all users on the network can access it
- Permission checks on every route — members cannot access other users' files

### 🛡️ Admin Panel
- Dashboard with total users, total files, storage used, and trash count
- Per-user file count and storage breakdown
- View any user's files directly
- Create and manage user accounts

### ⚙️ Settings
- Change password from settings page
- Dark mode toggle with persistence across sessions
- Personal storage breakdown per user

### 🎨 UI & Experience
- Professional dark mode — dark slate blues, not pure black
- Fully responsive — works on desktop, tablet, and mobile
- Modern dashboard with sidebar navigation and category cards
- File count badges on navigation items
- Storage breakdown panel with visual progress bar

### 🌐 Network Access
- Access from any device on the same WiFi via local IP
- mDNS broadcasting — access via `http://homevault.local` (requires Bonjour)
- Nginx reverse proxy support — clean URLs without port numbers

### 🔒 Security
- Passwords hashed with Werkzeug — never stored as plain text
- Session-based authentication with signed cookies
- Secret key stored in `.env` — never hardcoded in source
- File access permission-checked on every route
- Trashed files fully blocked from download, preview, and share
- All state-changing actions use POST requests
- Files never leave your local machine or network

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python 3, Flask                   |
| Database   | SQLite                            |
| Frontend   | HTML, CSS, Jinja2, JavaScript     |
| Images     | Pillow (thumbnail generation)     |
| Auth       | Flask sessions, Werkzeug hashing  |
| Network    | Nginx reverse proxy, Zeroconf     |
| Config     | python-dotenv                     |

---

## Project Structure

```
HomeVault/
├── app.py                   # Flask server — all routes and logic
├── database.py              # SQLite layer — all database operations
├── thumbnailer.py           # Thumbnail generation using Pillow
├── mdns_broadcast.py        # mDNS broadcasting for homevault.local
├── start_homevault.py       # Windows launcher — starts all services
├── HomeVault.bat            # One-click startup script
├── requirements.txt         # Python dependencies
├── .env                     # Secret key and config (not in Git)
├── templates/
│   ├── base.html            # Shared sidebar layout and preview modal
│   ├── index.html           # Main file dashboard
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── trash.html           # Trash / deleted files
│   ├── settings.html        # User settings (account, appearance, storage)
│   ├── admin_users.html     # Admin panel with user stats
│   └── admin_view_user.html # Admin — view one user's files
├── static/
│   ├── css/style.css        # Full design system with light/dark themes
│   ├── js/app.js            # Client-side logic (upload, preview, menus, etc.)
│   ├── favicon.svg          # App icon (SVG)
│   ├── favicon.ico          # App icon (ICO fallback)
│   └── thumbnails/          # Auto-generated photo thumbnails (not in Git)
└── storage/
    ├── Photos/              # Uploaded photos (not in Git)
    ├── Videos/              # Uploaded videos (not in Git)
    ├── Documents/           # Uploaded documents (not in Git)
    └── Others/              # Other file types (not in Git)
```

---

## Installation

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Aaryan2R/HomeVault.git
cd HomeVault

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux / Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create your .env file
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .env
echo FLASK_DEBUG=false >> .env

# 6. Run the app
python app.py
```

The app automatically creates all required storage folders on first run.

### Open in Browser

```
http://127.0.0.1:5000
```

### First Time Setup

Navigate to `/register` — the first account you create is automatically set as **Admin**.
After that, only the Admin can create new accounts from the **Manage Users** page.

### Access from Other Devices

Any device on the same WiFi can access HomeVault at:
```
http://<your-pc-ip>:5000
```

With Nginx and mDNS running (via `start_homevault.py` or `HomeVault.bat`):
```
http://homevault.local
```

> **Note:** The current launcher expects Nginx at `C:\nginx\nginx.exe`. This is acceptable
> for the current release. A proper configurable installer is planned for v1.1.

---

## How It Works

HomeVault uses two storage layers:

```
Uploaded file → saved to disk under storage/{category}/
File metadata → saved to SQLite database (homevault.db)
```

**Upload flow:**
1. Flask verifies the user is logged in
2. File type is detected from the extension
3. A unique UUID filename is generated to prevent conflicts
4. File is saved to the correct category folder on disk
5. Metadata (original name, size, category, date, owner) is stored in SQLite
6. If the file is a photo, a 200×200 thumbnail is generated
7. The browser shows real-time upload progress via XHR

Each file has two names in the database:
- `filename` — UUID name on disk (prevents conflicts between users)
- `original_name` — the name the user uploaded (shown in the UI)

---

## User Roles

| Role   | Permissions                                                         |
|--------|---------------------------------------------------------------------|
| Admin  | See and manage all users' files, create accounts, access everything |
| Member | See only their own files and files marked as shared                 |

---

## Security

- Passwords hashed with Werkzeug — never stored as plain text
- Secret key stored in `.env` — never in source code, never on GitHub
- Sessions are cookie-based and signed with the secret key
- File access is permission-checked on every route
- Trashed files are fully blocked from download, preview, and share
- All state-changing actions use POST requests
- Debug mode disabled by default
- Files never leave your local machine or network

---

## Comparison

| Feature              | Google Drive     | HomeVault          |
|----------------------|------------------|--------------------|
| Cost                 | Paid after 15 GB | Free forever       |
| Privacy              | Data on Google   | Data stays with you|
| Internet required    | Yes              | No                 |
| Multi-user support   | Paid plans only  | Built in           |
| File preview         | Yes              | Yes                |
| Dark mode            | Yes              | Yes                |
| Custom control       | No               | Full               |
| Setup complexity     | None             | One-time, minimal  |

---

## Roadmap

This is the first stable release of HomeVault (**v1.0.0**). The project will now receive
versioned updates going forward, like any standard open-source software.

### v1.1 — Launcher & Startup (Planned)
- [ ] Proper Windows launcher application (replacing the `.bat` file)
- [ ] Auto-start with Windows on boot
- [ ] Windows `.exe` installer via Inno Setup (one-click install, no Python needed)
- [ ] Configurable Nginx path (remove hardcoded `C:\nginx` dependency)

### v1.2 — Features & Quality
- [ ] CSRF protection on all state-changing routes
- [ ] Production-grade server (Waitress instead of Flask dev server)
- [ ] Custom error pages (404, 403, 500)
- [ ] Pagination for large file collections
- [ ] EXIF metadata cached in database for faster photo-date sorting

### Future
- [ ] User-created folders and file organization
- [ ] Google Photos style masonry grid for photos
- [ ] Remote access via Cloudflare Tunnel (free, no port forwarding)
- [ ] Encrypted personal vault per user
- [ ] File sharing via generated links
- [ ] Android companion app for automatic photo/video backup

---

## Changelog

### v1.0.0 — Initial Stable Release
- Full file management: upload, download, preview, rename, trash, restore, permanent delete
- Multi-user system with admin and member roles
- Auto-categorization and thumbnail generation
- Search, filter, sort (including EXIF photo date)
- Grid and list view toggle
- File sharing between users
- Professional dark mode with persistence
- Responsive design for desktop, tablet, and mobile
- Admin panel with user management and storage stats
- Settings page with password change and storage breakdown
- mDNS broadcasting for `homevault.local` access
- Nginx reverse proxy support
- One-click launcher with system tray integration

---

## License

MIT — free to use, modify, and distribute.
