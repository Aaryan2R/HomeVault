import socket
import time
from zeroconf import Zeroconf, ServiceInfo


def get_local_ip():
    # Ask Windows which local IP is being used right now.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def start_mdns():
    ip = get_local_ip()
    ip_bytes = socket.inet_aton(ip)

    # Only advertise on the active IP to avoid virtual adapter confusion.
    zeroconf = Zeroconf(interfaces=[ip])

    # Register HomeVault as a normal HTTP service on the local network.
    info = ServiceInfo(
        type_='_http._tcp.local.',
        name='HomeVault._http._tcp.local.',
        addresses=[ip_bytes],
        port=80,
        properties={'path': '/'},
        server='homevault.local.'
    )

    zeroconf.register_service(info)
    print('mDNS broadcasting: homevault.local ->', ip)
    print('Devices on the same network can use http://homevault.local')

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        # Remove the broadcast before the script exits.
        zeroconf.unregister_service(info)
        zeroconf.close()
        print('mDNS broadcast stopped.')


if __name__ == '__main__':
    try:
        start_mdns()
    except KeyboardInterrupt:
        print('\nStopped.')
