
import asyncio
import urllib.request

import htconnectionpool
import htstreamutil
import hturlparser


class HTHTTPConnector:
    def __init__(self, url):
        self.url = hturlparser.HTURLParser(url)

    @asyncio.coroutine
    def connect(self, method='GET', headers=None):
        self.reader, self.writer = yield from htconnectionpool.HTConnectionPool.get_connection(self.url.connect_hostname, self.url.connect_port, ssl=self.url.connect_ssl)
        self.tunnel_hostname, self.tunnel_port = self.url.connect_hostname, self.url.connect_port
        if self.url.proxy and self.url.scheme == 'https':
            yield from self._do_proxy_connect()
        request_line = '%s %s HTTP/1.1\r\n' % (method, self.url.connect_request)
        if headers is None:
            headers = {}
        headers['Host'] = headers.get('Host', self.url.vhost)
        if self.url.proxy and self.url.proxy_scheme == 'http':
            headers['Proxy-Connection'] = headers.get('Proxy-Connection', 'keep-alive')
        else:
            headers['Connection'] = headers.get('Connection', 'keep-alive')
        self.writer.writelines([request_line.encode('utf-8', 'replace'), '\r\n'.join(map(': '.join, sorted(headers.items()))).encode('utf-8', 'replace'), b'\r\n\r\n'])

    @asyncio.coroutine
    def close(self):
        yield from htconnectionpool.HTConnectionPool.push_connection(self.reader, self.writer, self.tunnel_hostname, self.tunnel_port, ssl=self.url.scheme == 'https')

    @asyncio.coroutine
    def _do_proxy_connect(self):
        self.writer.write(('CONNECT %s HTTP/1.1\r\n\r\n' % self.url.vhost).encode('utf-8', 'replace'))
        line = yield from self.reader.readline()
        if not line.startswith(b'200 '):
            yield from htstreamutil.full_close(self.reader, self.writer)
            raise urllib.request.HTTPError(str(self.url), 502, 'Proxy Connection Failure', None, None)
        while (yield from self.reader.readline().rstrip('\r\n')):
            pass
        self.reader.feed_eof()
        self.writer.write_eof()
        self.reader, self.writer = yield from asyncio.open_connection(ssl=True, sock=self.writer.get_extra_info('socket'), server_hostname=self.url.hostname)
        self.tunnel_hostname, self.tunnel_port = self.url.hostname, self.url.port
