import os
import requests


os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'


class Registry(object):
    def __init__(self, host, scheme='https', version='v1'):
        self.host = host
        self.scheme = scheme
        self.version = version

    def _url(self, *components):
        path = '/'.join(components)
        return '{}://{}/{}/{}'.format(self.scheme, self.host, self.version,
                                      path)

    def _get(self, url):
        r = requests.get(url)
        r.raise_for_status()
        return r.json()

    def image_info(self, image):
        url = self._url('images', image, 'json')
        return self._get(url)

    def tags(self, repo, info=False):
        url = self._url('repositories', repo, 'tags')
        repo_tags = self._get(url)

        if info:
            for tag, image in repo_tags.iteritems():
                repo_tags[tag] = self.image_info(image)

        return repo_tags
