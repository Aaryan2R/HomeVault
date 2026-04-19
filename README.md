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
- 📤 Multi-file upload with real-time progress bars per file (drag and drop supported)
- 📁 Auto-categorization into Photos, Videos, Documents, and Others
- 🖼️ Automatic thumbnail generation for photo uploads
- 👁️ File preview in browser — images, videos, PDFs open without downloading
- ⬇️ Download files from any device on your local network
- 🔍 Search files by name
- 🗂️ Filter files by category
- 🔲 Grid and list view toggle (like Google Drive)
- 🗑️ Trash system — soft delete with restore, permanent delete, and empty trash
- ✏️ Rename files inline by double clicking the filename
- 📅 Files grouped by date — Today, Yesterday, This Week, Month Year
- 🔃 Sort by newest, oldest, name, size, or actual photo date (EXIF metadata)

### Users and Access
- 👤 User authentication — login, register, logout
- 👨‍👩‍👧 Multi-user support — each user has their own private space
- 🔐 Role-based access — Admin sees everything, Members see only their own files
- 🤝 Shared files — mark any file as public so all users on the network can access it
- 🛡️ Permission checks — members cannot download, preview, or modify other users' files
- 👁️ File owner name shown on every file row

### Admin Panel
- 📊 Dashboard with total users, total files, storage used, and trash count
- 👥 Per-user file count and storage breakdown
- 🔍 View any user's files directly

### Settings
- 🔑 Change password from settings page
- 🌙 Dark mode toggle with persistence
- 💾 Personal storage breakdown per user

### UI and Experience
- 🌙 Professional dark mode — dark slate blues, not pure black, remembers preference
- 📱 Fully responsive — works on desktop, tablet, and mobile
- 📊 Storage breakdown panel — see how much space each category uses
- 🎨 Modern dashboard design with sidebar navigation and category cards
- 🔢 File count badges on sidebar navigation items

### Network Access
- 🏠 Local network access via Nginx reverse proxy — no port number in URL
- 🔄 Auto IP watcher — detects network changes and updates Nginx automatically
- 🌐 Two access modes — Local Only (homevault.local) or Anywhere Access (Cloudflare Tunnel)

### Security
- Passwords hashed with Werkzeug — never stored as plain text
- Session-based authentication with signed cookies
- Secret key stored in environment variable — never hardcoded in source
- File access permission-checked on every route
- Trashed files fully blocked from download, preview, and share
- All state-changing actions use POST requests — not GET links
- Files never leave your local machine or network

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python, Flask                     |
| Database   | SQLite (built into Python)        |
| Frontend   | HTML, CSS, Jinja2, JavaScript     |
| Images     | Pillow (thumbnail generation)     |
| Auth       | Flask sessions, Werkzeug hashing  |
| Network    | Nginx reverse proxy               |
| Config     | python-dotenv                     |

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
7. XHR upload shows real-time progress bar in the UI

Each file has two names in the database:
- `filename` — the UUID name on disk (prevents conflicts between users)
- `original_name` — the name the user uploaded (shown in the UI)

---

## User Roles

| Role   | What they can do                                                    |
|--------|---------------------------------------------------------------------|
| Admin  | See and manage all users files, create accounts, access everything  |
| Member | See only their own files and files marked as shared                 |

The first user to register automatically becomes Admin.
After that, only the Admin can create new accounts from the Manage Users page.

---

## Network Access Modes

HomeVault supports two access modes configured during installation:

### Local Only (Default)
- Access via `http://homevault.local` from any device on the same WiFi
- Uses mDNS broadcasting via Bonjour — zero configuration on any device
- Data never leaves your home network
- No internet dependency

### Anywhere Access (Optional)
- Access via `https://yourname.duckdns.org` from anywhere in the world
- Uses Cloudflare Tunnel — free, no port forwarding, no router changes
- HTTPS included automatically
- Switch between modes anytime from the Settings page

---

## Project Structure

```text
HomeVault/
├── app.py                   # Flask server — all routes and logic
├── database.py              # SQLite operations — all database functions
├── thumbnailer.py           # Thumbnail generation using Pillow
├── mdns_broadcast.py        # mDNS broadcasting for homevault.local
├── ip_watcher.py            # Auto-updates Nginx when IP changes
├── requirements.txt         # Python dependencies
├── .env                     # Secret key and config (never committed to Git)
├── templates/
│   ├── base.html            # Shared sidebar and layout
│   ├── index.html           # Main file dashboard
│   ├── login.html           # Login page
│   ├── register.html        # Register page
│   ├── trash.html           # Trash / deleted files
│   ├── settings.html        # User settings page
│   ├── admin_users.html     # Admin panel with stats
│   └── admin_view_user.html # Admin — view one user's files
├── static/
│   ├── css/
│   │   └── style.css        # Full design system with dark mode
│   ├── js/
│   │   └── app.js           # Dark mode, menus, preview, grid toggle, upload progress
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

### 4. Create environment file

Generate a secret key and create your `.env` file:

```powershell
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" > .env
echo FLASK_DEBUG=false >> .env
```

### 5. Run the app

```bash
python app.py
```

The app automatically creates all required storage folders on startup.
No manual folder creation needed.

### 6. Open in your browser

```
http://127.0.0.1:5000
```

### 7. First time setup

Go to `/register` — the first account you create is automatically set as Admin.
After that, only the Admin can create new accounts from the Manage Users page.

### 8. Access from other devices on your home network

With Nginx running, other devices on the same WiFi can access HomeVault at:

```
http://192.168.x.x
```

Or with mDNS broadcasting running:

```
http://homevault.local
```

---

## Security Notes

- Passwords are hashed using Werkzeug — never stored as plain text
- Secret key stored in `.env` file — never in source code, never on GitHub
- Sessions are cookie-based and signed with the secret key
- File access is permission-checked on every route
- Trashed files are fully blocked from download, preview, and share
- All state-changing actions use POST requests — not GET links
- Files never leave your local machine or network
- Debug mode disabled by default — only enabled via `.env` for development

---

## Notes

- This is a local-first project. Files stay on the machine running the app.
- `venv/`, `storage/`, `static/thumbnails/`, `homevault.db`, and `.env` are excluded
  from version control via `.gitignore`.
- The repository contains only source code, templates, and configuration files.

---

## Upcoming Improvements

### Remote Access
- [ ] Cloudflare Tunnel integration — access HomeVault from anywhere for free
- [ ] DuckDNS setup — free custom subdomain (yourname.duckdns.org)
- [ ] Network tab in Settings — switch between Local Only and Anywhere Access
- [ ] Automatic DuckDNS registration in installer

### Installer
- [ ] PyInstaller packaging — convert app to portable .exe (no Python needed)
- [ ] NSSM Windows Service — Flask, Nginx, IP watcher start automatically on boot
- [ ] Inno Setup — full HomeVault_Setup.exe one-click Windows installer
- [ ] Automatic static IP detection and configuration
- [ ] Advanced network settings for power users with restore/rollback option
- [ ] Bonjour/mDNS auto-registration for homevault.local

### Features
- [ ] Google Photos style masonry grid — photos display in natural aspect ratios
- [ ] User-created folders — organise files into custom folders like Google Drive
- [ ] Move files between folders from the UI
- [ ] Pagination — load files in batches for large collections
- [ ] Encrypted personal vault per user (locker feature)
- [ ] File sharing via generated links (share with non-users)
- [ ] Android app — automatic background photo and video backup
- [ ] Better error pages (custom 404, 403, 500)

### Post-Submission
- [ ] EXIF metadata stored in database on upload for faster sorting
- [ ] Production server mode (Waitress instead of Flask dev server)
- [ ] CSRF protection on all state-changing routes

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
| Remote access        | Yes              | Planned (free)     |
| Custom control       | No               | Full               |
| Setup complexity     | None             | Minimal            |

---

## License

MIT — free to use, modify, and distribute.
