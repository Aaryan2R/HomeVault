# HomeVault

A lightweight self-hosted private cloud storage system for home and family use.
Think Google Drive, but local, private, and fully yours. No internet required,
no monthly fees, no data leaving your house.

Built as a BCA final year project using Python, Flask, SQLite, Nginx, and a
Windows launcher.

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/Aaryan2R/HomeVault/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

---

## What is HomeVault?

Most people either pay for cloud storage or dump everything into one messy folder.
HomeVault gives you organized, private, local storage with a clean browser-based UI.

Upload files from any device on your home network. HomeVault automatically sorts
them into Photos, Videos, Documents, and Others, generates thumbnails for images,
stores metadata in SQLite, and lets you search, filter, preview, download, and manage
everything from a modern dashboard that looks and feels like a real cloud storage app.

Inspired by Google Drive and Google Photos, but runs entirely on your own hardware.

---

## Versions

| Version | Status | What it includes |
|---------|--------|-----------------|
| [v1.0.0](https://github.com/Aaryan2R/HomeVault/releases/tag/v1.0.0) | Stable | Full web app, multi-user, dark mode, file preview, sort, EXIF, admin panel, settings |
| [v1.1.0-beta](https://github.com/Aaryan2R/HomeVault/releases/tag/v1.1.0-beta) | Beta | Everything in v1.0.0 + GUI launcher, system tray, one-click start/stop |
| [v1.2.0](https://github.com/Aaryan2R/HomeVault/releases/tag/v1.2.0) | Installer Beta | Everything in v1.1.0 + Windows installer, auto dependency detection |
| [v1.3.0](https://github.com/Aaryan2R/HomeVault/releases/tag/v1.3.0) | Stable | Everything in v1.2.0 + production server, pagination, CSRF protection |

---

## What's New in v1.3.0

- **Production server** — Flask dev server replaced with Waitress, no more dev server warning
- **Pagination** — 50 files per page with Previous/Next and numbered page controls, all filters preserved
- **CSRF protection** — Flask-WTF CSRFProtect added across every form and upload/rename request
- **Custom error pages** — friendly 404, 403, and 500 pages (community contribution)
- **Mobile UI fixes** — resolved layout edge cases on small screens
- **Test suite** — initial Python test coverage for core functions (community contribution)

---

## Features

### Core Storage
- Multi-file upload with real-time per-file progress bars
- Drag-and-drop upload support
- Auto-categorization into Photos, Videos, Documents, and Others
- Automatic thumbnail generation for photo uploads
- In-browser file preview for images, videos, and PDFs
- Download files from any device on your local network
- Search files by name
- Filter by category
- Grid and list view toggle
- Sort by date, name, size, or actual photo date (EXIF metadata)
- Files grouped by date — Today, Yesterday, This Week, Month Year
- Pagination — 50 files per page, fast even with large collections

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

### Windows Launcher
- GUI launcher window with per-service status indicators
- System tray icon — HomeVault runs silently in background
- Single instance guard — opening the launcher twice just opens the browser
- Start with Windows toggle from the tray menu
- Clean stop — kills Flask, Nginx, and all helper processes with no cmd flashes

### Network Access
- Nginx reverse proxy — clean URLs without port numbers
- mDNS broadcasting — access via `http://homevault.local` from any device on your WiFi
- Auto IP watcher — detects network IP changes and updates Nginx automatically
- Hosts file integration — `homevault.local` works on the host PC automatically

### Security
- Passwords hashed with Werkzeug — never stored as plain text
- Secret key stored in `.env` — never hardcoded in source
- CSRF protection on every form and upload/rename request
- File access permission-checked on every route
- Trashed files fully blocked from download, preview, and share
- All state-changing actions use POST requests
- Debug mode disabled by default
- Custom error pages for 404, 403, and 500 — no stack traces shown to users

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask, Waitress |
| Database | SQLite |
| Frontend | HTML, CSS, Jinja2, JavaScript |
| Images | Pillow |
| Auth | Flask sessions, Werkzeug hashing, Flask-WTF (CSRF) |
| Network | Nginx, Zeroconf/mDNS |
| Config | python-dotenv |
| Launcher | tkinter, pystray, PyInstaller |
| Installer | Inno Setup |

---

## Installation

### Option A — Windows Installer (Recommended)

1. Go to the [Releases page](https://github.com/Aaryan2R/HomeVault/releases)
2. Download `HomeVault_Setup.exe` from the latest release
3. Double-click and follow the wizard
4. HomeVault launches automatically when install completes
5. Access from any device on your WiFi at `http://homevault.local`

The installer handles everything automatically:
- Extracts and configures Nginx
- Installs Bonjour for `homevault.local` support
- Sets Windows firewall rules
- Creates desktop shortcut and Start Menu entry

If upgrading from an older version, the installer detects the existing
installation and updates files in place. Your `.env`, database, and
uploaded files are preserved.

### Option B — Manual Setup (Developers)

```powershell
# 1. Clone the repository
git clone https://github.com/Aaryan2R/HomeVault.git
cd HomeVault

# 2. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
python -c "
import secrets
with open('.env', 'w', encoding='utf-8') as f:
    f.write('SECRET_KEY=' + secrets.token_hex(32) + chr(10))
    f.write('FLASK_DEBUG=false' + chr(10))
"

# 5. Run the app
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

### Prerequisites for Manual Setup

**Nginx** — for clean URLs without port numbers

Download `nginx/Windows-1.30.0` stable from https://nginx.org/en/download.html
and extract to `C:\nginx`.

**Bonjour** — for `homevault.local` on other devices

Download from https://support.apple.com/kb/DL999 and install.

---

## Testing

This project uses `pytest` for core function tests.

```powershell
.\venv\Scripts\Activate.ps1
pytest
```

---

## First Time Setup

Go to `/register` — the first account is automatically set as Admin.
After that only the Admin can create new accounts from the Manage Users page.

---

## Access

```
From this PC:        http://homevault.local
From other devices:  http://homevault.local  (same WiFi, requires Bonjour)
Direct IP fallback:  http://192.168.x.x
```

---

## Project Structure

```text
HomeVault/
|-- app.py                  # Main Flask app - all routes and logic
|-- database.py             # SQLite helper functions
|-- thumbnailer.py          # Image thumbnail generation
|-- launcher.py             # Windows GUI launcher and system tray
|-- setup_helper.py         # Installer-time setup tasks
|-- homevault.iss           # Inno Setup installer script
|-- ip_watcher.py           # Updates Nginx config when local IP changes
|-- mdns_broadcast.py       # Broadcasts homevault.local on the network
|-- HomeVault.bat           # Development launcher shortcut
|-- requirements.txt        # Python dependencies
|-- templates/              # HTML templates
|-- static/                 # CSS, JS, icons
`-- storage/                # Uploaded files (ignored by Git)
```

---

## Building from Source

### Build the Launcher EXE

```powershell
.\venv\Scripts\Activate.ps1
pyinstaller --onedir --name HomeVault --noconsole --uac-admin `
  --icon "static\icon.ico" `
  --add-data "templates;templates" `
  --add-data "static;static" `
  --add-data ".env;." `
  --add-data "mdns_broadcast.py;." `
  --add-data "ip_watcher.py;." `
  --add-data "requirements.txt;." `
  --hidden-import=zeroconf `
  --hidden-import=PIL --hidden-import=PIL.Image `
  --hidden-import=PIL.ImageDraw `
  --hidden-import=werkzeug --hidden-import=dotenv `
  --hidden-import=pystray --hidden-import=psutil `
  --hidden-import=flask --hidden-import=tkinter `
  --hidden-import=app --hidden-import=database `
  --hidden-import=thumbnailer `
  --hidden-import=waitress `
  --hidden-import=flask_wtf `
  --noconfirm launcher.py
```

### Build the Installer

Place these files in `installer_assets/` first:

```text
installer_assets/
|-- python-3.13.13-embed-amd64.zip   (embedded Python runtime)
|-- nginx.zip                        (Nginx Windows stable zip)
`-- Bonjour64.exe or .msi            (Bonjour for Windows)
```

Then compile:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ".\homevault.iss"
```

Output: `installer_output\HomeVault_Setup.exe`

---

## Known Limitations

- `homevault.local` resolution depends on Bonjour and browser - use direct IP as fallback
- No HTTPS on local network (browser shows Not Secure) - planned for v1.4

---

## Roadmap

### v1.4 — Remote Access and Features
- [ ] Cloudflare Tunnel integration - access HomeVault from anywhere for free
- [ ] Support HTTPS via self-signed certificate for local network
- [ ] Google Photos style masonry grid for photo display
- [ ] User-created folders for custom file organisation

### Future
- [ ] Add file type icons for more formats
- [ ] Android companion app - automatic photo and video backup
- [ ] Linux support (Ubuntu, Raspberry Pi)
- [ ] Full-text search inside document contents
- [ ] Real-time notifications when files are shared

---

## Contributing

HomeVault is open source and welcomes contributions.

### Good First Issues

- Add file type icons for more formats

### How to Contribute

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/HomeVault.git

# Create a branch
git checkout -b feature/your-feature-name

# Make your changes and test with python app.py

# Push and open a pull request
git push origin feature/your-feature-name
```

Please keep pull requests focused on one thing.

### Reporting Bugs

Open an issue with:
- What you were doing
- What you expected
- What actually happened
- Your Windows version and Python version

---

## Why Not Just Use Google Drive?

| Feature | Google Drive | HomeVault |
|---------|-------------|-----------|
| Cost | Paid after 15 GB | Free forever |
| Privacy | Data on Google | Data stays with you |
| Internet required | Yes | No |
| Multi-user support | Paid plans only | Built in |
| File preview | Yes | Yes |
| Dark mode | Yes | Yes |
| Remote access | Yes | Planned (free) |
| Custom control | No | Full |
| Setup complexity | None | Minimal |

---

## License

MIT — free to use, modify, and distribute.
