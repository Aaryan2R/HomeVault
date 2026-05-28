# HomeVault

A lightweight self-hosted private cloud storage system for home and family use.
Think Google Drive, but local, private, and fully yours. No internet is required
for normal home-network use.

Built as a BCA final year project using Python, Flask, SQLite, Nginx, and a
Windows launcher.

[![Version](https://img.shields.io/badge/version-1.2.0-orange.svg)](https://github.com/Aaryan2R/HomeVault/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()
[![Status](https://img.shields.io/badge/status-installer--beta-yellow.svg)]()

## Installer Beta Notice

HomeVault v1.2.0 adds the Windows installer workflow. The core web app and
launcher are working, but the installer should still be tested on a fresh
Windows machine before calling it a final public release.

## Features

- Upload and manage files from a browser.
- Auto-sort files into Photos, Videos, Documents, and Others.
- Generate thumbnails for images.
- Preview images, videos, and PDFs in the browser.
- Search, filter, rename, download, restore, and delete files.
- Multi-user login with Admin and Member roles.
- Admin dashboard for users, file counts, and storage usage.
- Dark mode and settings page.
- Local network access through Nginx and `homevault.local`.
- Windows launcher with service status, tray icon, and clean stop action.
- Inno Setup installer script for building `HomeVault_Setup.exe`.

## What's New in v1.2.0

- Added `homevault.iss` for Inno Setup installer builds.
- Added `setup_helper.py` for installer-time setup tasks.
- Added repo-local `ip_watcher.py` so the installer does not depend on `C:\nginx`.
- Added installer asset handling for Python, Nginx, and Bonjour.
- Updated launcher paths to prefer installed files and fall back to legacy paths.
- Updated icon handling so the launcher and installer use the same app icon.
- Cleaned shutdown behavior for Flask and Nginx.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Flask |
| Database | SQLite |
| Frontend | HTML, CSS, Jinja2, JavaScript |
| Images | Pillow |
| Auth | Flask sessions, Werkzeug password hashing |
| Network | Nginx, Zeroconf/mDNS |
| Config | python-dotenv |
| Launcher | tkinter, pystray, PyInstaller |
| Installer | Inno Setup |

## Project Structure

```text
HomeVault/
|-- app.py                  # Main Flask app
|-- database.py             # SQLite helper functions
|-- thumbnailer.py          # Image thumbnail generation
|-- launcher.py             # Windows GUI launcher and tray app
|-- setup_helper.py         # Installer setup tasks
|-- homevault.iss           # Inno Setup installer script
|-- ip_watcher.py           # Updates Nginx when local IP changes
|-- mdns_broadcast.py       # Broadcasts homevault.local on the network
|-- HomeVault.bat           # Development launcher shortcut
|-- requirements.txt        # Python dependencies
|-- templates/              # HTML templates
|-- static/                 # CSS, JS, icons
`-- storage/                # Uploaded files, ignored by Git
```

## Development Setup

```powershell
cd "C:\Users\admin\Desktop\My Files\Study Material\HomeVault"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Launcher Build

```powershell
.\venv\Scripts\Activate.ps1
pyinstaller --onedir --name HomeVault --noconsole `
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
  --hidden-import=app `
  --hidden-import=database `
  --hidden-import=thumbnailer `
  --noconfirm launcher.py
```

## Installer Build

Installer assets must exist locally in `installer_assets/` with these names:

```text
installer_assets/
|-- python-installer.exe
|-- nginx.zip
`-- Bonjour64.exe or Bonjour64.msi
```

Then compile:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ".\homevault.iss"
```

The output is:

```text
installer_output\HomeVault_Setup.exe
```

## Git Ignore Notes

The repo intentionally ignores local runtime files and large generated files:

- `.env`
- `venv/`
- `dist/`
- `build/`
- `installer_output/`
- installer asset binaries
- uploaded files in `storage/`
- databases and logs

## Known Limitations

- The v1.2.0 installer still needs a clean Windows VM test before final release.
- `homevault.local` can depend on Bonjour/mDNS behavior on the device and browser.
- HTTPS is not included for local-network use.
- CSRF protection is not implemented yet.

## License

MIT License.
