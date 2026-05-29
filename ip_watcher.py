import socket
import time
import subprocess
import re
import os

# Nginx files used by the watcher.
NGINX_CONF = 'C:\\nginx\\conf\\nginx.conf'
NGINX_EXE = 'C:\\nginx\\nginx.exe'
CHECK_EVERY = 60


def get_local_ip():
    # This does not send data. It just asks Windows which local IP is active.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def update_nginx_config(new_ip):
    with open(NGINX_CONF, 'r') as f:
        config = f.read()

    # Replace the first server_name value with the latest local IP.
    updated = re.sub(
        r'(server_name\s+)[\S]+;',
        r'\g<1>' + new_ip + ';',
        config
    )

    with open(NGINX_CONF, 'w') as f:
        f.write(updated)

    print('Config updated with IP:', new_ip)


def reload_nginx():
    try:
        pid_file = 'C:\\nginx\\logs\\nginx.pid'

        if os.path.exists(pid_file):
            # Reload is enough when Nginx is already running.
            subprocess.run([NGINX_EXE, '-s', 'reload'], check=True)
            print('Nginx reloaded successfully')
        else:
            # If it is not running, start it fresh.
            subprocess.Popen([NGINX_EXE])
            print('Nginx started successfully')

    except Exception as e:
        print('Nginx operation failed:', e)


def watch():
    print('IP Watcher starting...')
    last_ip = None

    # Check once right away in case the IP changed since last run.
    current_ip = get_local_ip()
    print('Current IP:', current_ip)
    update_nginx_config(current_ip)
    reload_nginx()
    last_ip = current_ip

    # Keep checking every minute.
    while True:
        time.sleep(CHECK_EVERY)

        current_ip = get_local_ip()

        if current_ip != last_ip:
            print('IP changed from', last_ip, 'to', current_ip)
            update_nginx_config(current_ip)
            reload_nginx()
            last_ip = current_ip
        else:
            print('IP unchanged:', current_ip)


if __name__ == '__main__':
    try:
        watch()
    except KeyboardInterrupt:
        print('\nIP Watcher stopped.')
