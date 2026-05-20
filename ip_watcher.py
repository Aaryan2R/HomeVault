import socket
import time
import subprocess
import re
import os

# Where the Nginx config file lives
NGINX_CONF    = 'C:\\nginx\\conf\\nginx.conf'
NGINX_EXE     = 'C:\\nginx\\nginx.exe'
CHECK_EVERY   = 60  # seconds between IP checks


def get_local_ip():
    # Open a UDP socket and connect to an external address
    # This does not send any data — just checks routing
    # Returns our real network IP like 192.168.0.111
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

    # Match server_name followed by ANYTHING (IP or hostname)
    # [\S]+ means one or more non-whitespace characters
    # This matches both "homevault" and "192.168.0.111"
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
        # Check if Nginx is already running by looking for the PID file
        pid_file = 'C:\\nginx\\logs\\nginx.pid'

        if os.path.exists(pid_file):
            # Nginx is running — reload config with zero downtime
            subprocess.run([NGINX_EXE, '-s', 'reload'], check=True)
            print('Nginx reloaded successfully')
        else:
            # Nginx is not running — start it fresh
            subprocess.Popen([NGINX_EXE])
            print('Nginx started successfully')

    except Exception as e:
        print('Nginx operation failed:', e)


def watch():
    print('IP Watcher starting...')
    last_ip = None

    # Check immediately on startup
    # This handles the case where PC rebooted and IP changed overnight
    current_ip = get_local_ip()
    print('Current IP:', current_ip)
    update_nginx_config(current_ip)
    reload_nginx()
    last_ip = current_ip

    # Now keep watching every 60 seconds
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


# Run the watcher
if __name__ == '__main__':
    try:
        watch()
    except KeyboardInterrupt:
        print('\nIP Watcher stopped.')