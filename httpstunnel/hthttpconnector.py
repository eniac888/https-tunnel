
import asyncio
import urllib.request

import hturlparser

class HTHTTPConnector:
    def __init__(self, url):
        self.url = hturlparser.HTURLParser(url)

    @asyncio.coroutine
    def connect(self, method='GET', headers=None):
        self.reader, self.writer = yield from HTHTTPConnectionManager.get_connection(self.url.connect_hostname, self.url.connect_port, ssl=self.url.connect_ssl)
        if self.url.proxy and self.url.scheme == 'https':
            yield from self._do_proxy_connect()
        request_line = '%s %s HTTP/1.1\r\n' % (method, self.url.connect_request)
        if headers is None:
            headers = {}
        headers['Host'] = headers.get('Host') or self.url.vhost
        if self.url.proxy and self.url.proxy_scheme == 'http':
            headers['Proxy-Connection'] = headers.get('Proxy-Connection') or 'keep-alive'
        else:
            headers['Connection'] = headers.get('Connection') or 'keep-alive'
        self.writer.writelines([request_line.encode('utf-8', 'replace'), '\r\n'.join(map(': '.join, sorted(headers.items()))).encode('utf-8', 'replace'), b'\r\n\r\n'])

    @asyncio.coroutine
    def close(self):
        self.writer.close()
        self.reader.feed_eof()
        yield from self.reader.read()

    @asyncio.coroutine
    def _do_proxy_connect(self):
        self.writer.write(('CONNECT %s HTTP/1.1\r\n\r\n' % self.url.vhost).encode('utf-8', 'replace'))
        line = yield from self.reader.readline()
        if not line.startswith(b'200 '):
            self.close()
            raise urllib.request.HTTPError(str(self.url), 502, 'Proxy Connection Failure', None, None)
        while (yield from self.reader.readline().rstrip('\r\n')):
            pass
        self.reader, self.writer = yield from self.writer.do_ssl_handshake(server_hostname=self.url.hostname)


class HTHTTPConnectionManager:
    connections = {}
    
    @staticmethod
    def _get_addr_tuple(host=None, port=None, ssl=None, family=0, proto=0, local_addr=None, sock=None):
        return ((host, port), local_addr, family, proto, ssl, sock)

    @classmethod
    @asyncio.coroutine
    def get_connection(cls, host=None, port=None, *args, ssl=None, family=0, proto=0, sock=None, local_addr=None, **kwargs):
        addr_tuple = cls._get_addr_tuple(host, port, ssl, family, proto, local_addr, sock)
        if addr_tuple not in cls.connections:
            rwpair = yield from cls.new_connection(host, port, ssl=ssl, family=family, proto=proto, sock=sock, local_addr=local_addr, *args, **kwargs)
            return rwpair
        else:
            for i in cls.connections[addr_tuple]:
                if i[1].http_idle:
                    i[1].http_idle = False
                    return i
            else:
                rwpair = yield from cls.new_connection(host, port, ssl=ssl, family=family, proto=proto, sock=sock, local_addr=local_addr, *args, **kwargs)
                return rwpair
        
    @classmethod
    @asyncio.coroutine
    def new_connection(cls, host=None, port=None, *args, ssl=None, family=0, proto=0, sock=None, local_addr=None, **kwargs):
        addr_tuple = cls._get_addr_tuple(host, port, ssl, family, proto, local_addr, sock)
        rwpair = yield from asyncio.open_connection(host, port, ssl=ssl, family=family, proto=proto, sock=sock, local_addr=local_addr, *args, **kwargs)
        rwpair_1_close = rwpair[1].close
        def on_connection_close():
            cls.connections[addr_tuple].remove(rwpair)
            if len(cls.connections[addr_tuple]) == 0:
                del cls.connections[addr_tuple]
            rwpair_1_close()
            try:
                self.ssl_wrapped[1].close()
            except AttributeError:
                pass
        rwpair[1].close = on_connection_close
        @asyncio.coroutine
        def do_ssl_handshake(sslcontext=True, server_hostname=None):
            yield from rwpair[1].drain()
            ssl_rwpair = yield from cls.new_connection(ssl=sslcontext, sock=rwpair[1].get_extra_info('socket'), server_hostname=server_hostname)
            ssl_rwpair[1].ssl_wrapped = rwpair
        rwpair[1].do_ssl_handshake = do_ssl_handshake
        rwpair[1].http_idle = False
        if addr_tuple in cls.connections:
            cls.connections[addr_tuple].append(rwpair)
        else:
            cls.connections[addr_tuple] = [rwpair]
        return rwpair
