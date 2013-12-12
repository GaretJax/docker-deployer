import os
import hashlib
import json
import struct
import socket
from datetime import datetime

from flask import current_app


def _route_filename(base_path, key, ip, port):
    name = '{} {}:{}'.format(key, ip, port)
    name = hashlib.sha224(name).hexdigest() + '.json'
    return os.path.join(base_path, 'subscriptions', name)


def add(router_ip, router_port, key, ip, port, weight=1):
    filename = _route_filename(current_app.config['DATA_ROOT'], key, ip, port)

    subscription = {
        'key': key,
        'ip': ip,
        'port': port,
        'weight': weight,
    }

    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    with open(filename, 'w') as fh:
        json.dump(subscription, fh)

    update_subscription(router_ip, router_port, **subscription)


def remove(router_ip, router_port, key, ip, port):
    filename = _route_filename(current_app.config['DATA_ROOT'], key, ip, port)

    if os.path.exists(filename):
        with open(filename, 'rb') as fh:
            subscription = json.load(fh)
            update_subscription(router_ip, router_port,
                                subscription['key'],
                                subscription['ip'],
                                subscription['port'],
                                remove=True)

        os.remove(filename)


def getall(router_ip, router_stats_port):
    data = ''

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((router_ip, router_stats_port))

    while True:
        read = s.recv(1024)
        if not read:
            break
        data += read
    s.close()

    subscriptions = json.loads(data)['subscriptions']

    for s in subscriptions:
        for n in s['nodes']:
            n['last_check'] = datetime.fromtimestamp(n['last_check'])

    return subscriptions


def update_subscription(router_ip, router_port, key, ip, port, remove=False,
                        **attrs):
    payload = {
        'key': key,
        'address': '{}:{}'.format(ip, port),
    }
    payload.update(**attrs)

    msg = ''

    for k, v in payload.iteritems():
        v = str(v)
        msg += struct.pack('<h', len(k)) + str(k)
        msg += struct.pack('<h', len(v)) + v

    msg = struct.pack('<BhB', 224, len(msg), 1 if remove else 0) + msg

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(msg, (router_ip, router_port))
