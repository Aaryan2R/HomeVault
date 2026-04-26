import subprocess
import sys
import os
import time
import socket
import threading
import webbrowser
import ctypes

# Check if this script already has admin rights.
# Firewall changes on Windows need that.
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def restart_as_admin():
    # Try starting the same script again with admin rights.
    # If user cancels UAC, just keep going without admin-only setup.
    result = ctypes.windll.shell32.ShellExecuteW(
        None, 'runas', sys.executable, ' '.join(sys.argv), None, 1
    )
    if result > 32:
        sys.exit()
    print('Admin request was skipped, continuing without it')
    return False


# Main paths used by the launcher script
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
NGINX_EXE  = 'C:\\nginx\\nginx.exe'
WATCHER    = 'C:\\nginx\\ip_watcher.py'
MDNS       = os.path.join(BASE_DIR, 'mdns_broadcast.py')
VENV_PY    = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
PYTHON     = VENV_PY if os.path.exists(VENV_PY) else sys.executable
APP        = os.path.join(BASE_DIR, 'app.py')
REQ_FLAG   = os.path.join(BASE_DIR, '.requirements_ready')

# Keep process objects here so stop_all() can close them later
procs = {}


# Step 1: make sure the needed Python packages are there
def install_requirements():
    req = os.path.join(BASE_DIR, 'requirements.txt')
    if not os.path.exists(req):
        print('requirements.txt not found, skipping')
        return
    if os.path.exists(REQ_FLAG):
        try:
            if os.path.getmtime(REQ_FLAG) >= os.path.getmtime(req):
                print('Requirements already checked, skipping')
                return
        except OSError:
            pass
    print('Checking requirements...')
    subprocess.run(
        [PYTHON, '-m', 'pip', 'install', '-r', req, '-q'],
        check=False
    )
    try:
        with open(REQ_FLAG, 'w', encoding='utf-8') as f:
            f.write('ok')
    except OSError:
        pass
    print('Requirements OK')


# Step 2: check if Nginx exists in C:\nginx
def check_nginx():
    if not os.path.exists(NGINX_EXE):
        print('WARNING: Nginx not found at C:\\nginx\\nginx.exe')
        print('Please download nginx from https://nginx.org/en/download.html')
        print('and extract to C:\\nginx')
        return False
    print('Nginx found OK')
    return True


# Step 3: check if Bonjour is available for .local access
def check_bonjour():
    try:
        result = subprocess.run(
            ['sc', 'query', 'Bonjour Service'],
            capture_output=True, text=True
        )
        if 'RUNNING' in result.stdout or 'STOPPED' in result.stdout:
            print('Bonjour found OK')
            return True
    except:
        pass
    print('WARNING: Bonjour not found')
    print('Download from https://support.apple.com/kb/DL999')
    return False


# Step 4: add firewall rules when admin access is available
def setup_firewall():
    if not is_admin():
        print('Skipping firewall setup (not running as admin)')
        return

    rules = [
        # Allow Flask on port 5000
        'netsh advfirewall firewall add rule name="HomeVault-Flask" '
        'dir=in action=allow protocol=TCP localport=5000 '
        'profile=private enable=yes',

        # Allow Nginx on port 80
        'netsh advfirewall firewall add rule name="HomeVault-Nginx" '
        'dir=in action=allow protocol=TCP localport=80 '
        'profile=private enable=yes',
    ]

    for rule in rules:
        result = subprocess.run(rule, shell=True,
                                capture_output=True, text=True)
        if 'Ok.' in result.stdout or 'already exists' in result.stdout.lower():
            print('Firewall rule OK:', rule.split('name="')[1].split('"')[0])
        else:
            print('Firewall rule set:', rule.split('name="')[1].split('"')[0])


# Step 5: start the background parts HomeVault needs
def start_flask():
    print('Starting Flask...')
    procs['flask'] = subprocess.Popen(
        [PYTHON, APP],
        cwd=BASE_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    # Wait until Flask is actually ready on port 5000
    for i in range(15):
        time.sleep(1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s.connect_ex(('127.0.0.1', 5000)) == 0:
            s.close()
            print('Flask running OK on port 5000')
            return True
        s.close()
    print('WARNING: Flask did not start in time')
    return False


def start_nginx():
    if not os.path.exists(NGINX_EXE):
        print('Nginx not found, skipping')
        return
    print('Starting Nginx...')
    procs['nginx'] = subprocess.Popen(
        [NGINX_EXE],
        cwd='C:\\nginx',
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    time.sleep(1)
    print('Nginx started OK')


def start_ip_watcher():
    if not os.path.exists(WATCHER):
        print('IP watcher not found, skipping')
        return
    print('Starting IP watcher...')
    procs['watcher'] = subprocess.Popen(
        [PYTHON, WATCHER],
        cwd='C:\\nginx',
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print('IP watcher started OK')


def start_mdns():
    if not os.path.exists(MDNS):
        print('mDNS script not found, skipping')
        return
    print('Starting mDNS broadcast...')
    procs['mdns'] = subprocess.Popen(
        [PYTHON, MDNS],
        cwd=BASE_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    print('mDNS started OK')


# Step 6: stop anything this launcher started
def stop_all():
    print('Stopping all services...')

    # Stop Nginx first
    if os.path.exists(NGINX_EXE):
        subprocess.run(
            [NGINX_EXE, '-s', 'stop'],
            capture_output=True
        )

    # Then stop the other processes started here
    for name, proc in procs.items():
        if proc and proc.poll() is None:
            proc.terminate()
            print(f'Stopped {name}')

    print('All services stopped.')


# Step 7: use a tray icon so the app can stay running
def run_tray(open_url):
    try:
        import pystray
        import PIL.Image
        import PIL.ImageDraw
    except ImportError:
        print('pystray not installed, running without tray icon')
        print('Press Ctrl+C to stop HomeVault')
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            stop_all()
        return

    # Make a small tray icon in code so no extra icon file is needed
    img  = PIL.Image.new('RGB', (64, 64), color=(37, 99, 235))
    draw = PIL.ImageDraw.Draw(img)
    draw.text((14, 18), 'HV', fill='white')

    def on_open(icon, item):
        webbrowser.open(open_url)

    def on_stop(icon, item):
        stop_all()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem('Open HomeVault', on_open, default=True),
        pystray.MenuItem('Stop HomeVault', on_stop)
    )

    icon = pystray.Icon(
        name='HomeVault',
        icon=img,
        title='HomeVault - Running',
        menu=menu
    )

    print('HomeVault running in system tray')
    print('Right click tray icon to open or stop')
    icon.run()


# Main launcher flow for HomeVault
def main():
    print('=' * 50)
    print('HomeVault Startup')
    print('=' * 50)

    install_requirements()

    nginx_ok = check_nginx()
    bonjour_ok = check_bonjour()

    setup_firewall()

    flask_ok = start_flask()
    start_nginx()
    start_ip_watcher()
    start_mdns()

    print('=' * 50)
    print('HomeVault is running!')
    print('Local:    http://homevault.local')
    print('Direct:   http://127.0.0.1:5000')
    print('=' * 50)

    # Open the browser after Flask starts
    if flask_ok:
        open_url = 'http://homevault.local'
        if not nginx_ok or not bonjour_ok:
            open_url = 'http://127.0.0.1:5000'
        time.sleep(1)
        webbrowser.open(open_url)
    else:
        open_url = 'http://127.0.0.1:5000'

    # Keep the launcher alive in the tray
    run_tray(open_url)


if __name__ == '__main__':
    # Ask for admin access before trying firewall setup
    if not is_admin():
        print('Requesting admin rights for firewall setup...')
        restart_as_admin()
    main()
