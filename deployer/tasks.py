from uwsgidecorators import timer

from deployer import utils


def container_ip_updater(docker_client, container, cache_key=None):
    cache_key = cache_key or '{}_IP'.format(container)

    @timer(5)
    def update_ip(signum):
        ip = utils._update_container_ip(docker_client, container, cache_key)
        print '{} IP is {}'.format(container, ip)
