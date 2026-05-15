# HomeVault 🗄️

A lightweight self-hosted private cloud storage system for home and family use.
Think Google Drive — but local, private, and fully yours. No internet required,
no monthly fees, no data leaving your house.

Built as a BCA final year project using Python, Flask, and SQLite.

[![Version](https://img.shields.io/badge/version-1.1.0--beta-orange.svg)](https://github.com/Aaryan2R/HomeVault/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()
[![Status](https://img.shields.io/badge/status-beta-yellow.svg)]()

---

## ⚠️ Beta Notice

**v1.1.0 is currently in beta.**

The core application (v1.0.0) is stable and tested. The new Windows launcher
and system tray features introduced in v1.1.0 are functional but still being
refined. If you want the most stable experience, use v1.0.0.

To download a specific version go to the
[Releases page](https://github.com/Aaryan2R/HomeVault/releases).

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

## What's New in v1.1.0-beta

- **GUI Launcher** — A proper Windows launcher application with a service status window
- **System Tray** — HomeVault runs silently in the background from the system tray
- **One-click start** — Double click `HomeVault.bat` to start everything automatically
- **Clean shutdown** — Right-click tray icon → Stop HomeVault stops all services cleanly
- **Start with Windows** — Toggle autostart from the tray menu (registry-based)
- **Single instance** — Running the launcher twice opens your browser instead of duplicating
- **No cmd flashes** — All background processes run silently with no terminal windows
- **Smart startup** — Checks for stale processes, fixes Nginx permissions automatically

---

## Features

### Core Storage
- Multi-file upload with real-time per-file progress bars
- Drag-and-drop upload support
- Auto-categorization into Photos, Videos, Documents, and Others
- Automatic thumbnail generation for photo uploads
- In-browser file preview — images, videos, and PDFs open without downloading
- Download files from any device on your local network
- Search files by name
- Filter by category
- Grid and list view toggle (like Google Drive)
- Sort by date, name, size, or actual photo date (EXIF metadata)
- Files grouped by date — Today, Yesterday, This Week, Month Year

### File Management
- Trash system with soft delete, restore, and permanent delete
- Empty trash to bulk-remove all trashed files
- Rename files inline by double-clicking the filename

### Users and Access
- User authentication — login, register, logout
- Multi-user support — each user has their own private space
- Role-based access — Admin sees everything, Members see only their own files
- Shared files — mark any file as public so all users on the network can access it
- Permission checks on every route

### Admin Panel
- Dashboard with total users, total files, storage used, and trash count
- Per-user file count and storage breakdown
- View any user's files directly

### Settings
- Change password from settings page
- Dark mode toggle with persistence
- Personal storage breakdown per user

### Network Access
- Nginx reverse proxy — clean URLs without port numbers
- mDNS broadcasting — access via `http://homevault.local` from any device on your WiFi
- Auto IP watcher — detects network IP changes and updates Nginx automatically
- Hosts file integration — `homevault.local` works on the host PC automatically

### Security
- Passwords hashed with Werkzeug — never stored as plain text
- Secret key stored in `.env` — never hardcoded in source
- File access permission-checked on every route
- Trashed files fully blocked from download, preview, and share
- All state-changing actions use POST requests
- Debug mode disabled by default

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python 3, Flask                     |
| Database   | SQLite                              |
| Frontend   | HTML, CSS, Jinja2, JavaScript       |
| Images     | Pillow (thumbnail generation)       |
| Auth       | Flask sessions, Werkzeug hashing    |
| Network    | Nginx reverse proxy, Zeroconf/mDNS  |
| Config     | python-dotenv                       |
| Launcher   | tkinter, pystray, PyInstaller       |

---

## Versions

| Version | Status | What it includes |
|---------|--------|-----------------|
| [v1.0.0](https://github.com/Aaryan2R/HomeVault/releases/tag/v1.0.0) | Stable | Full web app, multi-user, dark mode, file preview, sort, EXIF, admin panel, settings |
| [v1.1.0-beta](https://github.com/Aaryan2R/HomeVault/releases/tag/v1.1.0-beta) | Beta | Everything in v1.0.0 + GUI launcher, system tray, one-click start/stop |

---

## Installation

### Prerequisites

Before running HomeVault you need two things installed:

**1. Nginx** (for clean URLs without port numbers)

Download `nginx/Windows-1.30.0` stable from https://nginx.org/en/download.html

Extract to `C:\nginx` so that `C:\nginx\nginx.exe` exists.

**2. Bonjour** (for `homevault.local` on other devices)

Download from https://support.apple.com/kb/DL999 and install.
This is a free Apple service already on most Windows PCs that have iTunes.

---

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Aaryan2R/HomeVault.git
cd HomeVault

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create your .env file (use Python to ensure UTF-8 encoding)
python -c "
import secrets
with open('.env', 'w', encoding='utf-8') as f:
    f.write('SECRET_KEY=' + secrets.token_hex(32) + '\n')
    f.write('FLASK_DEBUG=false\n')
"

# 6. Run the app
python app.py
```

### One-Click Launcher (v1.1.0-beta)

After setup, double-click `HomeVault.bat` to start everything automatically:
- Flask server
- Nginx reverse proxy
- IP watcher
- mDNS broadcast

A launcher window shows service status. Close it to minimize to the system tray.
Right-click the tray icon to open HomeVault or stop the server.

### Access

```
From this PC:      http://homevault.local
From other devices: http://homevault.local  (same WiFi, Bonjour required)
Direct IP:          http://192.168.x.x
```

### First Time Setup

Go to `/register` — the first account is automatically Admin.
After that only the Admin can create new accounts from Manage Users.

---

## Project Structure

```
HomeVault/
├── app.py                 # Flask server — all routes and logic
├── database.py            # SQLite layer — all database functions
├── thumbnailer.py         # Thumbnail generation
├── launcher.py            # GUI launcher with system tray (v1.1+)
├── HomeVault.bat          # One-click startup script
├── mdns_broadcast.py      # mDNS broadcasting for homevault.local
├── requirements.txt       # Python dependencies
├── .env                   # Secret key and config (never committed)
├── templates/             # HTML templates
├── static/                # CSS, JS, images
└── storage/               # Uploaded files (never committed)
```

---

## Known Limitations

- Nginx path is currently hardcoded to `C:\nginx` — configurable installer planned for v1.2
- No HTTPS on local network (browser shows "Not Secure") — Cloudflare tunnel planned for v1.2
- CSRF protection not yet implemented — low priority for local network use
- mDNS `.local` resolution not guaranteed on all Android browsers — use direct IP as fallback

---

## Roadmap

### v1.2 — Installer
- [ ] `HomeVault_Setup.exe` — one-click Windows installer via Inno Setup
- [ ] Bundles Python, Nginx, Bonjour automatically
- [ ] Configurable install location
- [ ] Automatic firewall rules
- [ ] Creates Start Menu and desktop shortcuts
- [ ] Uninstaller

### v1.3 — Remote Access
- [ ] Cloudflare Tunnel integration — access from anywhere for free
- [ ] DuckDNS or custom subdomain support
- [ ] HTTPS automatic via Cloudflare

### Future
- [ ] Google Photos masonry grid layout
- [ ] User-created folders
- [ ] Android app — automatic photo backup
- [ ] Encrypted personal vault per user
- [ ] File sharing via generated links
- [ ] Production server (Waitress instead of Flask dev server)

---

## Contributing

HomeVault is open source and welcomes contributions of all kinds.

### Good first issues
- Fix mobile UI edge cases
- Add file type icons for more formats
- Improve error pages (404, 403, 500)
- Add pagination for large file collections
- Write tests

### How to contribute

```bash
# Fork the repo on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/HomeVault.git

# Create a branch
git checkout -b feature/your-feature-name

# Make your changes
# Test them with python app.py

# Push and open a pull request
git push origin feature/your-feature-name
```

Please keep pull requests focused on one thing. Large sweeping changes are harder to review.

### Reporting bugs

Open an issue on GitHub with:
- What you were doing
- What you expected to happen
- What actually happened
- Your Windows version and Python version

---

## Why Not Just Use Google Drive?

| Feature              | Google Drive      | HomeVault          |
|----------------------|-------------------|--------------------|
| Cost                 | Paid after 15 GB  | Free forever       |
| Privacy              | Data on Google    | Data stays with you|
| Internet required    | Yes               | No                 |
| Multi-user support   | Paid plans only   | Built in           |
| File preview         | Yes               | Yes                |
| Dark mode            | Yes               | Yes                |
| Remote access        | Yes               | Planned (free)     |
| Custom control       | No                | Full               |
| Setup complexity     | None              | Minimal            |

---

## License

MIT — free to use, modify, and distribute.
