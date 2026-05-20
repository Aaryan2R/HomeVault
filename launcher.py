import tkinter as tk
import threading
import subprocess
import sys
import os
import time
import socket
import webbrowser
import winreg
import tempfile


# Small helper so Windows commands stay hidden.
# This stops random cmd windows from flashing for the user.
def run_silent(cmd, **kwargs):
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return subprocess.run(
        cmd,
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW,
        capture_output=True,
        **kwargs
    )


def popen_silent(cmd, **kwargs):
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return subprocess.Popen(
        cmd,
        startupinfo=si,
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs
    )


def get_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE = get_base()
_nginx_local = os.path.join(BASE, 'nginx', 'nginx.exe')
_nginx_legacy = 'C:\\nginx\\nginx.exe'
NGINX_EXE = _nginx_local if os.path.exists(_nginx_local) else _nginx_legacy
WATCHER = os.path.join(BASE, 'ip_watcher.py')
MDNS = os.path.join(BASE, 'mdns_broadcast.py')
if getattr(sys, 'frozen', False):
    APP = os.path.join(BASE, '_internal', 'app.py')
    PYTHON = os.path.join(BASE, '_internal', 'python.exe')
    if not os.path.exists(PYTHON):
        PYTHON = sys.executable
else:
    APP = os.path.join(BASE, 'app.py')
    VENV_PY = os.path.join(BASE, 'venv', 'Scripts', 'python.exe')
    PYTHON = VENV_PY if os.path.exists(VENV_PY) else sys.executable
LOG_FILE = os.path.join(BASE, 'flask.log')
LOCK_FILE = os.path.join(tempfile.gettempdir(), 'homevault_launcher.lock')

procs = {}
browser_opened = False
browser_opened_lock = threading.Lock()
tray_icon_ref = [None]


def write_debug(msg):
    log_path = os.path.join(BASE, 'debug.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            import datetime
            f.write(f'{datetime.datetime.now()} - {msg}\n')
    except Exception:
        pass


def check_single_instance():
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        return
    except FileExistsError:
        pass

    try:
        with open(LOCK_FILE, 'r', encoding='utf-8') as f:
            old_pid = int(f.read().strip())
        import psutil
        if psutil.pid_exists(old_pid):
            os._exit(0)
    except (ValueError, OSError):
        pass

    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass

    fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))


def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except OSError:
        pass


def is_port_open(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(('127.0.0.1', port))
    s.close()
    return result == 0


def fix_nginx_permissions():
    logs_dir = 'C:\\nginx\\logs'
    if not os.path.exists(logs_dir):
        return
    try:
        run_silent(['icacls', logs_dir, '/grant', '*S-1-1-0:(OI)(CI)F', '/T'])
    except Exception:
        pass


def ensure_hosts_entry():
    hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
    entry = '127.0.0.1    homevault.local'
    try:
        with open(hosts_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'homevault.local' not in content:
            with open(hosts_path, 'a', encoding='utf-8') as f:
                f.write(f'\n{entry}\n')
            print('Added homevault.local to hosts file')
    except PermissionError:
        print('Cannot write hosts file - need admin rights')
    except Exception as e:
        print('Hosts file error:', e)


def get_best_url():
    nginx_pid = 'C:\\nginx\\logs\\nginx.pid'
    if os.path.exists(nginx_pid):
        return 'http://homevault.local'
    return 'http://127.0.0.1:5000'


def is_startup_enabled():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run',
            0,
            winreg.KEY_READ
        )
        winreg.QueryValueEx(key, 'HomeVault')
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def set_startup(enable):
    target = sys.executable if getattr(sys, 'frozen', False) else os.path.join(BASE, 'HomeVault.bat')
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Run',
            0,
            winreg.KEY_SET_VALUE
        )
        if enable:
            winreg.SetValueEx(key, 'HomeVault', 0, winreg.REG_SZ, target)
        else:
            try:
                winreg.DeleteValue(key, 'HomeVault')
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print('Startup toggle error:', e)


def start_flask(cb):
    if is_port_open(5000):
        cb('flask', 'Already running', True)
        return True

    cb('flask', 'Starting...', None)

    if getattr(sys, 'frozen', False):
        # In the built exe, Flask runs inside this same process.
        def run_flask_thread():
            try:
                os.environ['HOMEVAULT_BASE'] = BASE
                import app as flask_app
                flask_app.ensure_folders()
                flask_app.init_db()
                flask_app.upgrade_db()
                flask_app.app.run(
                    host='0.0.0.0',
                    debug=False,
                    threaded=True,
                    use_reloader=False
                )
            except Exception as e:
                write_debug(f'Flask thread error: {e}')
                import traceback
                write_debug(traceback.format_exc())

        threading.Thread(target=run_flask_thread, daemon=True).start()
    else:
        try:
            log = open(LOG_FILE, 'a', encoding='utf-8')
            procs['flask'] = popen_silent(
                [PYTHON, APP],
                cwd=BASE,
                env={**os.environ, 'HOMEVAULT_BASE': BASE},
                stdout=log,
                stderr=log
            )
        except Exception as e:
            write_debug(f'Subprocess failed: {e}')
            cb('flask', f'Failed: {e}', False)
            return False

    for _ in range(20):
        time.sleep(1)
        if is_port_open(5000):
            cb('flask', 'Running OK', True)
            return True

    cb('flask', 'Timed out - check debug.log', False)
    return False


def start_nginx(cb):
    if not os.path.exists(NGINX_EXE):
        cb('nginx', 'Not installed', False)
        return

    fix_nginx_permissions()
    pid_file = 'C:\\nginx\\logs\\nginx.pid'
    nginx_running = False

    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r', encoding='utf-8') as f:
                pid = int(f.read().strip())
            import psutil
            if psutil.pid_exists(pid):
                nginx_running = True
        except Exception:
            pass

    if nginx_running:
        run_silent([NGINX_EXE, '-s', 'reload'])
        cb('nginx', 'Running OK', True)
        return

    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except OSError:
            pass

    cb('nginx', 'Starting...', None)
    nginx_dir = os.path.dirname(NGINX_EXE)
    procs['nginx'] = popen_silent([NGINX_EXE], cwd=nginx_dir)
    time.sleep(2)

    if is_port_open(80):
        cb('nginx', 'Running OK', True)
    else:
        cb('nginx', 'Failed - check C:\\nginx\\logs\\error.log', False)


def start_watcher(cb):
    if not os.path.exists(WATCHER):
        cb('watcher', 'Not found', False)
        return

    cb('watcher', 'Starting...', None)
    watcher_dir = os.path.dirname(WATCHER)
    procs['watcher'] = popen_silent([PYTHON, WATCHER], cwd=watcher_dir)
    time.sleep(1)
    cb('watcher', 'Running OK', True)


def start_mdns(cb):
    if getattr(sys, 'frozen', False):
        bundle_dir = os.path.join(os.path.dirname(sys.executable), '_internal')

        def run_mdns_thread():
            try:
                if bundle_dir not in sys.path:
                    sys.path.insert(0, bundle_dir)
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    'mdns_broadcast',
                    os.path.join(bundle_dir, 'mdns_broadcast.py')
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.start_mdns()
            except Exception as e:
                write_debug(f'mDNS thread error: {e}')

        threading.Thread(target=run_mdns_thread, daemon=True).start()
        time.sleep(2)
        cb('mdns', 'Running OK', True)
        return

    if not os.path.exists(MDNS):
        cb('mdns', 'Not found - homevault.local may not work', False)
        return

    cb('mdns', 'Starting...', None)
    procs['mdns'] = popen_silent([PYTHON, MDNS], cwd=BASE)
    time.sleep(1)
    cb('mdns', 'Running OK', True)


def stop_all():
    # First stop the extra processes this launcher started.
    for name, proc in list(procs.items()):
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
            procs[name] = None

    # Ask Nginx to stop nicely first.
    if os.path.exists(NGINX_EXE):
        run_silent([NGINX_EXE, '-s', 'stop'])
        time.sleep(1)

    # Then force-kill every nginx.exe in case workers are still hanging around.
    run_silent(['taskkill', '/F', '/IM', 'nginx.exe'])
    time.sleep(0.3)

    # Clean up Flask if something is still listening on 5000.
    try:
        result = run_silent(['netstat', '-ano'], text=True)
        for line in result.stdout.splitlines():
            if ':5000 ' in line and 'LISTENING' in line:
                pid = line.strip().split()[-1]
                run_silent(['taskkill', '/F', '/PID', pid])
    except Exception:
        pass

    # Double-check port 80 and kill anything left there.
    try:
        result = run_silent(['netstat', '-ano'], text=True)
        for line in result.stdout.splitlines():
            if ':80 ' in line and 'LISTENING' in line:
                pid = line.strip().split()[-1]
                if pid != '4':
                    run_silent(['taskkill', '/F', '/PID', pid])
    except Exception:
        pass

    # Remove the old pid file so the next start is clean.
    pid_file = 'C:\\nginx\\logs\\nginx.pid'
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except OSError:
            pass

    release_lock()


def create_tray_icon(on_open, on_show, on_toggle_start, on_exit):
    try:
        import pystray
        import PIL.Image
        import PIL.ImageDraw
        import PIL.ImageFont
    except ImportError:
        return None

    img = PIL.Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = PIL.ImageDraw.Draw(img)
    try:
        # Use the same house emoji look as the browser tab icon.
        house = '\U0001F3E0'
        font = PIL.ImageFont.truetype('seguiemj.ttf', 48)
        bbox = draw.textbbox((0, 0), house, font=font, embedded_color=True)
        x = (64 - (bbox[2] - bbox[0])) // 2 - bbox[0]
        y = (64 - (bbox[3] - bbox[1])) // 2 - bbox[1]
        draw.text((x, y), house, font=font, embedded_color=True)
    except Exception:
        draw.ellipse([6, 6, 58, 58], fill=(37, 99, 235, 255))
        draw.text((18, 18), 'HV', fill=(255, 255, 255, 255))

    menu = pystray.Menu(
        pystray.MenuItem('Open HomeVault', on_open, default=True),
        pystray.MenuItem('Show Launcher', on_show),
        pystray.MenuItem(
            'Start with Windows',
            on_toggle_start,
            checked=lambda item: is_startup_enabled()
        ),
        pystray.MenuItem('Stop HomeVault', on_exit)
    )
    return pystray.Icon('HomeVault', img, 'HomeVault - Running', menu)


class LauncherApp:
    BLUE = '#2563eb'
    RED = '#dc2626'
    GREEN = '#16a34a'
    AMBER = '#d97706'
    BG = '#f0f4f8'
    CARD = '#ffffff'
    TEXT = '#1e293b'
    MUTED = '#64748b'
    SERVICES = [
        ('flask', 'Flask Server'),
        ('nginx', 'Nginx Proxy'),
        ('watcher', 'IP Watcher'),
        ('mdns', 'Network (mDNS)'),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('HomeVault')
        self.root.geometry('440x400')
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)
        self.root.protocol('WM_DELETE_WINDOW', self._minimize_to_tray)
        self._status_vars = {}
        self._dot_vars = {}
        self._tray = None
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=self.BLUE, height=64)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        tk.Label(
            hdr,
            text='  HomeVault',
            bg=self.BLUE,
            fg='white',
            font=('Segoe UI', 17, 'bold')
        ).pack(side='left', padx=20, pady=16)
        tk.Label(
            hdr,
            text='v1.1',
            bg=self.BLUE,
            fg='#93c5fd',
            font=('Segoe UI', 10)
        ).pack(side='right', padx=20)

        card = tk.Frame(self.root, bg=self.CARD)
        card.pack(fill='both', expand=True, padx=20, pady=16)
        tk.Label(
            card,
            text='Service Status',
            bg=self.CARD,
            fg=self.TEXT,
            font=('Segoe UI', 11, 'bold')
        ).pack(anchor='w', padx=16, pady=(14, 8))

        for key, label in self.SERVICES:
            row = tk.Frame(card, bg=self.CARD)
            row.pack(fill='x', padx=16, pady=4)

            dot = tk.Label(row, text='o', bg=self.CARD, fg='#cbd5e1', font=('Segoe UI', 13))
            dot.pack(side='left', padx=(0, 8))
            self._dot_vars[key] = dot

            tk.Label(
                row,
                text=label,
                bg=self.CARD,
                fg=self.MUTED,
                font=('Segoe UI', 10),
                width=20,
                anchor='w'
            ).pack(side='left')

            status = tk.Label(row, text='Waiting...', bg=self.CARD, fg='#94a3b8', font=('Segoe UI', 10))
            status.pack(side='left')
            self._status_vars[key] = status

        tk.Frame(card, bg='#e2e8f0', height=1).pack(fill='x', padx=16, pady=12)

        btn_row = tk.Frame(card, bg=self.CARD)
        btn_row.pack(fill='x', padx=16, pady=(0, 14))

        self.open_btn = tk.Button(
            btn_row,
            text='Open in Browser',
            command=self._open_browser,
            bg=self.BLUE,
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=18,
            pady=8,
            cursor='hand2',
            state='disabled',
            activebackground='#1d4ed8',
            activeforeground='white'
        )
        self.open_btn.pack(side='left', padx=(0, 8))

        self.stop_btn = tk.Button(
            btn_row,
            text='Stop Server',
            command=self._stop_and_exit,
            bg=self.RED,
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=18,
            pady=8,
            cursor='hand2',
            state='disabled',
            activebackground='#b91c1c',
            activeforeground='white'
        )
        self.stop_btn.pack(side='left')

        tk.Label(
            self.root,
            text='Close window to keep it running in the tray. Right-click tray icon to stop.',
            bg=self.BG,
            fg='#94a3b8',
            font=('Segoe UI', 8)
        ).pack(pady=(0, 10))

    def _update(self, key, text, ok):
        def _do():
            lbl = self._status_vars.get(key)
            dot = self._dot_vars.get(key)
            if not lbl:
                return

            if ok is True:
                lbl.config(text=text, fg=self.GREEN)
                dot.config(fg=self.GREEN)
            elif ok is False:
                lbl.config(text=text, fg=self.RED)
                dot.config(fg=self.RED)
            else:
                lbl.config(text=text, fg=self.AMBER)
                dot.config(fg=self.AMBER)

            if key == 'flask' and ok is True:
                self.open_btn.config(state='normal')
                self.stop_btn.config(state='normal')
                self.root.after(800, self._open_browser_once)

        self.root.after(0, _do)

    def _open_browser_once(self):
        global browser_opened
        with browser_opened_lock:
            if browser_opened:
                return
            browser_opened = True
        webbrowser.open(get_best_url())

    def _open_browser(self):
        webbrowser.open(get_best_url())

    def _stop_and_exit(self):
        global browser_opened
        browser_opened = False

        for key in self._status_vars:
            self._status_vars[key].config(text='Stopped', fg=self.RED)
            self._dot_vars[key].config(fg=self.RED)
        self.open_btn.config(state='disabled')
        self.stop_btn.config(state='disabled')

        def _do_stop():
            stop_all()
            if self._tray:
                self._tray.stop()
            self.root.after(500, self.root.destroy)

        threading.Thread(target=_do_stop, daemon=True).start()

    def _minimize_to_tray(self):
        self.root.withdraw()
        if self._tray is None:
            self._tray = create_tray_icon(
                on_open=lambda i, it: self._open_browser(),
                on_show=lambda i, it: self.root.after(0, self.root.deiconify),
                on_toggle_start=lambda i, it: set_startup(not is_startup_enabled()),
                on_exit=self._tray_exit
            )
            if self._tray:
                tray_icon_ref[0] = self._tray
                threading.Thread(target=self._tray.run, daemon=True).start()

    def _tray_exit(self, icon=None, item=None):
        self._stop_and_exit()

    def _run_services(self):
        ensure_hosts_entry()
        start_flask(self._update)
        start_nginx(self._update)
        start_watcher(self._update)
        start_mdns(self._update)

    def start(self):
        threading.Thread(target=self._run_services, daemon=True).start()
        self.root.mainloop()
        release_lock()


if __name__ == '__main__':
    check_single_instance()
    app = LauncherApp()
    app.start()
