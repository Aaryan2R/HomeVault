import subprocess
import sys
import os
import socket
import secrets
import winreg
import shutil

# Paths passed by Inno Setup so this script knows where HomeVault is installed.
# Usage: python setup_helper.py --install-dir "C:\Program Files\HomeVault"

def get_install_dir():
    for i, arg in enumerate(sys.argv):
        if arg == '--install-dir' and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    # Fallback - use script's own directory
    return os.path.dirname(os.path.abspath(__file__))

INSTALL_DIR  = get_install_dir()
VENV_DIR     = os.path.join(INSTALL_DIR, 'venv')
VENV_PY      = os.path.join(VENV_DIR, 'Scripts', 'python.exe')
VENV_PIP     = os.path.join(VENV_DIR, 'Scripts', 'pip.exe')
REQ_FILE     = os.path.join(INSTALL_DIR, 'requirements.txt')
ENV_FILE     = os.path.join(INSTALL_DIR, '.env')
NGINX_TARGET = os.path.join(INSTALL_DIR, 'nginx')
NGINX_EXE    = os.path.join(NGINX_TARGET, 'nginx.exe')
NGINX_LOGS   = os.path.join(NGINX_TARGET, 'logs')
NGINX_CONF   = os.path.join(NGINX_TARGET, 'conf', 'nginx.conf')
ASSETS_DIR   = os.path.join(INSTALL_DIR, 'installer_assets')
LOG_FILE     = os.path.join(INSTALL_DIR, 'setup.log')


# Print messages and also keep a setup.log file.
def log(msg):
    print(msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            import datetime
            f.write(f'{datetime.datetime.now()} - {msg}\n')
    except:
        pass


# Run setup commands quietly in the background.
def run_silent(cmd, **kwargs):
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return subprocess.run(
        cmd,
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW,
        capture_output=True,
        text=True,
        **kwargs
    )


# Check if Python is already available.
def check_python():
    log('Checking Python...')

    # HomeVault setup needs Python 3.10 or newer when run from source.
    try:
        result = run_silent(['python', '--version'])
        version_str = result.stdout.strip() or result.stderr.strip()
        log(f'Found: {version_str}')

        # Pull out major/minor version numbers.
        parts = version_str.replace('Python ', '').split('.')
        major = int(parts[0])
        minor = int(parts[1])

        if major == 3 and minor >= 10:
            log('Python 3.10+ found - skipping install')
            return True
        else:
            log(f'Python {major}.{minor} is too old - need 3.10+')
            return False

    except Exception as e:
        log(f'Python not found: {e}')
        return False


# Kept as a backup for manual installer repair work.
def install_python():
    log('Installing Python...')
    python_installer = os.path.join(
        ASSETS_DIR, 'python-installer.exe'
    )

    if not os.path.exists(python_installer):
        log('ERROR: python-installer.exe not found in installer_assets')
        return False

    # Silent install options used by the repair/manual path.
    result = run_silent([
        python_installer,
        '/quiet',
        'InstallAllUsers=1',
        'PrependPath=1',
        'Include_test=0'
    ])

    if result.returncode == 0:
        log('Python installed successfully')
        return True
    else:
        log(f'Python install failed: {result.stderr}')
        return False


# Create a venv if a manual install ever needs one.
def create_venv():
    log('Creating virtual environment...')

    if os.path.exists(VENV_PY):
        log('venv already exists - skipping')
        return True

    # Use whichever Python command Windows can find.
    python_exe = shutil.which('python') or shutil.which('python3')
    if not python_exe:
        log('ERROR: Python not found in PATH after install')
        return False

    result = run_silent([python_exe, '-m', 'venv', VENV_DIR])

    if os.path.exists(VENV_PY):
        log('Virtual environment created')
        return True
    else:
        log(f'venv creation failed: {result.stderr}')
        return False


# Install packages into the venv for manual source installs.
def install_requirements():
    log('Installing Python packages...')

    if not os.path.exists(VENV_PY):
        log('ERROR: venv Python not found')
        return False

    if not os.path.exists(REQ_FILE):
        log('ERROR: requirements.txt not found')
        return False

    result = run_silent([
        VENV_PY, '-m', 'pip', 'install',
        '-r', REQ_FILE, '--quiet'
    ])

    if result.returncode == 0:
        log('Packages installed successfully')
        return True
    else:
        log(f'pip install failed: {result.stderr}')
        return False


# Prepare Nginx for local network access.
def check_nginx():
    log('Checking Nginx...')

    # Prefer the Nginx copy inside the install folder.
    if os.path.exists(NGINX_EXE):
        log('Nginx already present - skipping extract')
        fix_nginx_permissions()
        write_nginx_config()
        return True

    # Also support the older C:\nginx setup.
    legacy_nginx = 'C:\\nginx\\nginx.exe'
    if os.path.exists(legacy_nginx):
        log('Nginx found at C:\\nginx - using existing installation')
        fix_nginx_permissions()
        return True

    # Otherwise extract the bundled Nginx zip.
    log('Extracting Nginx...')
    nginx_zip = os.path.join(ASSETS_DIR, 'nginx.zip')

    if not os.path.exists(nginx_zip):
        log('WARNING: nginx.zip not found in installer_assets')
        log('Nginx will not be available - direct IP access still works')
        return False

    import zipfile
    try:
        with zipfile.ZipFile(nginx_zip, 'r') as z:
            z.extractall(INSTALL_DIR)

        # Nginx zip extracts with a versioned folder name, so rename it.
        for item in os.listdir(INSTALL_DIR):
            if item.startswith('nginx-') and os.path.isdir(
                    os.path.join(INSTALL_DIR, item)):
                os.rename(
                    os.path.join(INSTALL_DIR, item),
                    NGINX_TARGET
                )
                break

        log('Nginx extracted successfully')
        fix_nginx_permissions()
        write_nginx_config()
        return True

    except Exception as e:
        log(f'Nginx extract failed: {e}')
        return False


def fix_nginx_permissions():
    # Let Nginx write logs without needing admin every launch.
    logs = NGINX_LOGS if os.path.exists(NGINX_LOGS) \
           else 'C:\\nginx\\logs'
    if os.path.exists(logs):
        run_silent([
            'icacls', logs,
            '/grant', '*S-1-1-0:(OI)(CI)F', '/T'
        ])
        log('Nginx permissions fixed')


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]
    except:
        return '127.0.0.1'
    finally:
        s.close()


def write_nginx_config():
    # Write nginx.conf for the current local IP.
    conf_dir = os.path.join(NGINX_TARGET, 'conf')
    if not os.path.exists(conf_dir):
        conf_dir = 'C:\\nginx\\conf'
    if not os.path.exists(conf_dir):
        return

    ip = get_local_ip()
    config = f"""worker_processes 1;

events {{
    worker_connections 1024;
}}

http {{

    server {{
        listen 80;
        server_name {ip} homevault homevault.local;

        location / {{
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }}

        client_max_body_size 500M;
    }}

}}
"""
    conf_path = os.path.join(conf_dir, 'nginx.conf')
    try:
        with open(conf_path, 'w', encoding='utf-8') as f:
            f.write(config)
        log(f'Nginx config written with IP: {ip}')
    except Exception as e:
        log(f'Could not write nginx.conf: {e}')


# Check or install Bonjour for homevault.local.
def check_bonjour():
    log('Checking Bonjour...')

    try:
        result = run_silent(['sc', 'query', 'Bonjour Service'])
        if 'RUNNING' in result.stdout or 'STOPPED' in result.stdout:
            log('Bonjour already installed - skipping')
            return True
    except Exception:
        pass

    log('Installing Bonjour...')
    bonjour_msi = os.path.join(ASSETS_DIR, 'Bonjour64.msi')
    bonjour_exe = os.path.join(ASSETS_DIR, 'Bonjour64.exe')
    bonjour_installer = bonjour_msi if os.path.exists(bonjour_msi) else bonjour_exe

    if not os.path.exists(bonjour_installer):
        log('WARNING: Bonjour installer not found in installer_assets')
        log('homevault.local may not work on other devices')
        return False

    if bonjour_installer.lower().endswith('.msi'):
        result = run_silent([
            'msiexec', '/i', bonjour_installer,
            '/quiet', '/norestart'
        ])
    else:
        result = run_silent([
            bonjour_installer,
            '/quiet', '/norestart'
        ])

    if result.returncode == 0:
        log('Bonjour installed successfully')
        return True

    log(f'Bonjour install returned: {result.returncode}')
    return True

# Create the local .env file if it does not exist.
def create_env_file():
    log('Creating .env file...')

    if os.path.exists(ENV_FILE):
        log('.env already exists - keeping existing secret key')
        return True

    try:
        key = secrets.token_hex(32)
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(f'SECRET_KEY={key}\n')
            f.write('FLASK_DEBUG=false\n')
        log('.env created with new secret key')
        return True
    except Exception as e:
        log(f'.env creation failed: {e}')
        return False


# Add firewall rules for the app and its ports.
def setup_firewall():
    log('Setting firewall rules...')

    exe_path = os.path.join(INSTALL_DIR, 'HomeVault.exe')

    rules = [
        # Allow the launcher exe.
        ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
         f'name=HomeVault', 'dir=in', 'action=allow',
         f'program={exe_path}', 'enable=yes', 'profile=private'],
        # Allow Flask direct access.
        ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
         'name=HomeVault-Flask', 'dir=in', 'action=allow',
         'protocol=TCP', 'localport=5000',
         'enable=yes', 'profile=private'],
        # Allow clean URL access through Nginx.
        ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
         'name=HomeVault-Nginx', 'dir=in', 'action=allow',
         'protocol=TCP', 'localport=80',
         'enable=yes', 'profile=private'],
    ]

    for rule in rules:
        run_silent(rule)

    log('Firewall rules set')


# Add homevault.local to the hosts file on this PC.
def update_hosts():
    log('Updating hosts file...')
    hosts = r'C:\Windows\System32\drivers\etc\hosts'
    entry = '127.0.0.1    homevault.local'

    try:
        with open(hosts, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'homevault.local' not in content:
            with open(hosts, 'a', encoding='utf-8') as f:
                f.write(f'\n{entry}\n')
            log('Added homevault.local to hosts file')
        else:
            log('homevault.local already in hosts file')
    except Exception as e:
        log(f'Hosts file update failed: {e}')


# Keep ip_watcher available for legacy C:\nginx installs.
def setup_ip_watcher():
    log('Setting up IP watcher...')
    src = os.path.join(INSTALL_DIR, 'ip_watcher.py')
    if not os.path.exists(src):
        log('WARNING: ip_watcher.py not found in install dir')
        return

    legacy_nginx = 'C:\\nginx'
    if os.path.exists(legacy_nginx) and \
       not os.path.exists(NGINX_TARGET):
        dst = os.path.join(legacy_nginx, 'ip_watcher.py')
        try:
            shutil.copy2(src, dst)
            log('ip_watcher.py also copied to C:\\nginx')
        except Exception as e:
            log(f'Legacy C:\\nginx copy skipped: {e}')

    log('IP watcher ready')


# Main setup flow used by the installer.
def main():
    log('-' * 50)
    log('HomeVault Setup Helper')
    log(f'Install directory: {INSTALL_DIR}')
    log('-' * 50)

    # HomeVault.exe is already bundled, so this only prepares Windows services.
    check_python()
    check_nginx()
    check_bonjour()
    create_env_file()
    setup_firewall()
    update_hosts()
    setup_ip_watcher()

    log('-' * 50)
    log('Setup complete')
    log('-' * 50)
    return 0

if __name__ == '__main__':
    sys.exit(main())
