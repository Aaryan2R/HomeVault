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
stores metadata in SQLite, and lets you search, filter, download, and manage
everything from a simple dashboard.

Inspired by Google Drive and Google Photos, but runs entirely on your own hardware.

---

## Features

- 👤 User authentication — login, register, logout
- 👨‍👩‍👧 Multi-user support — each user has their own private space
- 🔐 Role-based access — Admin sees everything, Members see only their own files
- 🤝 Shared folder — mark files as public so all users can access them
- 📤 Multi-file upload directly from the browser
- 📁 Auto-categorization into Photos, Videos, Documents, and Others
- 🖼️ Automatic thumbnail generation for photo uploads
- 🔍 Search files by name
- 🗂️ Filter files by category (Photos, Videos, Documents, Others)
- ⬇️ Download files from any device on your local network
- 🗑️ Trash system — soft delete with restore and permanent delete
- 💾 SQLite database — no external database setup needed
- 🚀 Lightweight — runs on any old PC, laptop, or Raspberry Pi

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python, Flask                     |
| Database   | SQLite                            |
| Frontend   | HTML, CSS, Jinja2                 |
| Images     | Pillow                            |
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
2. The file type is detected from the extension
3. A unique UUID filename is generated to avoid conflicts
4. The file is saved to the correct folder on disk
5. Metadata (original name, size, category, date, owner) is recorded in SQLite
6. A thumbnail is generated if the file is a photo

Each file in the database has two names:
- `filename` — the UUID name used on disk (prevents conflicts)
- `original_name` — the name you uploaded (shown in the UI)

Passwords are never stored as plain text. They are hashed using Werkzeug's
`generate_password_hash` before being saved to the database.

---

## User Roles

| Role   | What they can do                                              |
|--------|---------------------------------------------------------------|
| Admin  | See all users' files, manage users, access everything         |
| Member | See only their own files and files marked as shared           |

The first user to register automatically becomes Admin.
After that, only the Admin can create new accounts.

---

## Project Structure

```text
HomeVault/
├── app.py                   # Flask server — all routes and logic
├── database.py              # SQLite operations — all database functions
├── thumbnailer.py           # Thumbnail generation using Pillow
├── requirements.txt         # Python dependencies
├── templates/
│   ├── index.html           # Main file dashboard
│   ├── login.html           # Login page
│   ├── register.html        # Register page
│   ├── trash.html           # Trash / deleted files
│   ├── admin_users.html     # Admin — list of all users
│   └── admin_view_user.html # Admin — view one user's files
├── static/
│   ├── css/
│   │   └── style.css        # Stylesheet
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

The app automatically creates all required folders on startup.
No manual folder creation needed.

### 5. Open in your browser

```
http://127.0.0.1:5000
```

### 6. First time setup

Go to `/register` — the first account you create automatically becomes Admin.
After that, only the Admin can create new user accounts from the Manage Users page.

### 7. Access from other devices on the same network

Run with:
```bash
flask run --host=0.0.0.0
```

Then open `http://<your-pc-ip>:5000` from any device on the same Wi-Fi.

---

## Security Notes

- Passwords are hashed using Werkzeug — never stored as plain text
- Sessions are used for authentication — cookie-based, signed with a secret key
- File access is permission-checked — members cannot access other users' files
- All data-changing actions use POST requests — not GET links
- Files stay entirely on your own machine — nothing leaves your network

---

## Notes

- This is a local-first project. Files stay on the machine running the app.
- `venv/`, `storage/`, `static/thumbnails/`, and `homevault.db` are excluded
  from version control via `.gitignore`.
- The repo contains only source code, templates, and setup files.

---

## Roadmap

Features planned for future versions:

- [ ] File preview in browser (images, PDFs, videos)
- [ ] Rename files from the UI
- [ ] Storage usage analytics dashboard
- [ ] Mobile app for automatic photo backup
- [ ] Encrypted personal vault per user
- [ ] File sharing via generated links

---

## Why Not Just Use Google Drive?

| Feature              | Google Drive     | HomeVault          |
|----------------------|------------------|--------------------|
| Cost                 | Paid after 15GB  | Free               |
| Privacy              | Data on Google   | Data stays with you|
| Internet required    | Yes              | No                 |
| Multi-user support   | Paid plans only  | Built in           |
| Custom control       | No               | Full               |
| Setup complexity     | None             | Minimal            |

---

## License

MIT — free to use, modify, and distribute.
