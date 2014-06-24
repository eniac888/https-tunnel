
import logging
import urllib.parse
import urllib.request


class HTURLParser:
    def __init__(self, url):
        '''Results:
        scheme: 'http' or 'https'
        hostname: Host name (lower case)
        port: Port number as integer
        vhost: hostname:port
        path: Hierarchical path, starting with '/'
        query: Query component, the string after '?'
        request: path?query
        proxy: Boolean, whether proxy should be used
        connect_hostname: The host name to be connected
        connect_port: The port number to be connected
        connect_request: The second parameter to be sent when HTTP connection is set up
        '''
        self.url = str(url)
        try:
            urlsplit = urllib.parse.urlsplit(str(url), scheme='http')
            self.scheme = urlsplit.scheme
            self.hostname = urlsplit.hostname
            if urlsplit.port is None:
                self.port = 443 if urlsplit.scheme == 'https' else 80
            else:
                self.port = urlsplit.port
            self.vhost = urlsplit.netloc
            self.path = urlsplit.path or '/'
            self.query = urlsplit.query
            self.request = self.path+('?'+self.query if self.query else '')
            self.proxy = False
            if not urllib.request.proxy_bypass(self.hostname):
                self._testproxy(urlsplit)
            if self.proxy:
                self.connect_hostname = self.proxy_hostname
                self.connect_port = self.proxy_port
                if self.scheme == 'https':
                    if ':' in self.hostname:
                        self.connect_request = '[%s]:%d' % (self.hostname, self.port)
                    else:
                        self.connect_request = ':'.join((self.hostname, self.port))
                else:
                    self.connect_request = urllib.parse.urlunsplit(urlsplit[:4]+('',))
            else:
                self.connect_hostname = self.hostname
                self.connect_port = self.port
                self.connect_request = self.request
        except (AttributeError, IndexError, TypeError, ValueError) as e:
            raise ValueError('Invalid URL: %s' % url) from e

    def _testproxy(self, urlsplit):
        self.proxy = False
        getproxies = urllib.request.getproxies()
        try:
            proxy = getproxies[urlsplit.scheme]
            try:
                proxy_urlsplit = urllib.parse.urlsplit(getproxies[urlsplit.scheme], scheme='http')
                if proxy_urlsplit.scheme in ('http', 'https'):
                    self.proxy_scheme = proxy_urlsplit.scheme
                else:
                    logging.error('Can not use proxy %s, only HTTP and HTTPS proxy are supported' % proxy)
                    return
                self.proxy_hostname = proxy_urlsplit.hostname
                if proxy_urlsplit.port is None:
                    self.proxy_port = 443 if self.proxy_scheme == 'https' else 80
                else:
                    self.proxy_port = proxy_urlsplit.port
                self.proxy = True
            except Exception:
                logging.error('Can not use proxy %s' % proxy)
        except KeyError:
            pass

    def __str__(self):
        return self.url

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.url)
