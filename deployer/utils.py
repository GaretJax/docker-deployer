import uwsgi
import functools

from uwsgidecorators import get_free_signal
from sh import sudo
from flask import current_app, request, jsonify, make_response
from docker import Client
from werkzeug.routing import BaseConverter


class RecurrentTask(object):
    def start(self, interval, now=False):
        signum = get_free_signal()
        uwsgi.register_signal(signum, '', self._handle_signal)
        uwsgi.add_timer(signum, interval)
        if now:
            self._handle_signal(signum)

    def _handle_signal(self, signum):
        self.task()

    def task(self):
        raise NotImplementedError()


iptables = sudo.iptables


def allow_traffic(parent, child, port, remove=False):
    #print '{} traffic from {} to {}:{}'.format(
    #    'Denying' if remove else 'Allowing', parent, child, port)

    args = {
        'delete' if remove else 'insert': 'FORWARD',
        'i': 'docker0',
        'o': 'docker0',
        'protocol': 'tcp',
        'jump': 'ACCEPT',
    }

    iptables(source=parent,
             dport=port,
             destination=child,
             **args)

    iptables(source=child,
             sport=port,
             destination=parent,
             **args)


def _update_container_ip(client, container_name, cache_key):
    info = client.inspect_container(container_name)
    ip_address = info['NetworkSettings']['IPAddress']
    uwsgi.cache_set(cache_key, ip_address)
    return ip_address


def get_container_ip(client, container_name):
    cache_key = '{}_{}_IP'.format(client.base_url, container_name)
    return (uwsgi.cache_get(cache_key)
            or _update_container_ip(client, container_name, cache_key))


def get_frontend_ip(client=None, name=None):
    client = client or Client(version='1.6')
    name = name or current_app.config['FRONTEND_NAME']
    return get_container_ip(client, name)


def xhr_form(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        if request.method == 'POST' and request.is_xhr:
            if response.status_code == 302:
                # Form valid, redirecting
                return jsonify(status='OK',
                               location=response.headers['Location'])
            elif response.status_code == 200:
                # Form invalid, showing again
                return jsonify(status='NOK', html=response.get_data())
        return response
    return wrapper


class RegexConverter(BaseConverter):
    def __init__(self, url_map, regex):
        super(RegexConverter, self).__init__(url_map)
        self.regex = regex
