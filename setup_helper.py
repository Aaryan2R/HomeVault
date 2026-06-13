import subprocess
import sys
import os
import socket
import secrets
import shutil
import time

# Paths passed by Inno Setup so this script knows where HomeVault is installed.
# Usage: python setup_helper.py --install-dir "C:\Program Files\HomeVault"

def get_install_dir():
    for i, arg in enumerate(sys.argv):
        if arg == '--install-dir' and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return os.path.dirname(os.path.abspath(__file__))

INSTALL_DIR  = get_install_dir()
ENV_FILE     = os.path.join(INSTALL_DIR, '.env')
NGINX_TARGET = os.path.join(INSTALL_DIR, 'nginx')
NGINX_EXE    = os.path.join(NGINX_TARGET, 'nginx.exe')
NGINX_LOGS   = os.path.join(NGINX_TARGET, 'logs')
NGINX_CONF   = os.path.join(NGINX_TARGET, 'conf', 'nginx.conf')
ASSETS_DIR   = os.path.join(INSTALL_DIR, 'installer_assets')
LOG_FILE     = os.path.join(INSTALL_DIR, 'setup.log')


# Print setup messages and save them in setup.log too.
def log(msg):
    print(msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            import datetime
            f.write(f'{datetime.datetime.now()} - {msg}\n')
    except Exception:
        pass


# Run setup commands without opening command windows.
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

    # Unzip the Nginx copy included with the installer.
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

        # Rename the versioned folder to just nginx.
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
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()


def write_nginx_config():
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


# Bonjour helps other devices find homevault.local.
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
    bonjour_installer = bonjour_msi if os.path.exists(bonjour_msi) \
                        else bonjour_exe

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


# Allow HomeVault through the Windows firewall.
def setup_firewall():
    log('Setting firewall rules...')

    exe_path = os.path.join(INSTALL_DIR, 'HomeVault.exe')

    rules = [
        ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
         'name=HomeVault', 'dir=in', 'action=allow',
         f'program={exe_path}', 'enable=yes', 'profile=private'],
        ['netsh', 'advfirewall', 'firewall', 'add', 'rule',
         'name=HomeVault-Flask', 'dir=in', 'action=allow',
         'protocol=TCP', 'localport=5000',
         'enable=yes', 'profile=private'],
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


# Main setup steps used by the installer.
# Python is already packed inside HomeVault.exe, so no venv is needed here.
def main():
    log('-' * 50)
    log('HomeVault Setup Helper')
    log(f'Install directory: {INSTALL_DIR}')
    log('-' * 50)

    t0 = time.time()

    t = time.time()
    check_nginx()
    log(f'Nginx done in {time.time()-t:.1f}s')

    t = time.time()
    check_bonjour()
    log(f'Bonjour done in {time.time()-t:.1f}s')

    t = time.time()
    create_env_file()
    log(f'Env file done in {time.time()-t:.1f}s')

    t = time.time()
    setup_firewall()
    log(f'Firewall done in {time.time()-t:.1f}s')

    t = time.time()
    update_hosts()
    log(f'Hosts done in {time.time()-t:.1f}s')

    t = time.time()
    setup_ip_watcher()
    log(f'IP watcher done in {time.time()-t:.1f}s')

    log(f'Total setup time: {time.time()-t0:.1f}s')
    log('-' * 50)
    log('Setup complete')
    log('-' * 50)
    return 0


if __name__ == '__main__':
    sys.exit(main())
