#!/usr/bin/env python3

import asyncio
import hashlib
import logging
import salsa20

class HTServer:
    @classmethod
    def listen(cls, host=None, port=None, gateuri='/ht/gate', datauri='/ht/data'):
        asyncio.Task(asyncio.start_server(cls, host=host, port=port))

    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer
        asyncio.Task(self.accept())

    @asyncio.coroutine
    def accept(self):
        self.peer_addr = self.writer.get_extra_info('peername')[0:2]
        logging.info('Connection from [%s]:%s' % self.peer_addr)
        while not self.reader.at_eof():
            yield from self.read_http_header()

    @asyncio.coroutine
    def read_http_header(self):
        line = yield from self.reader.readline()
        if not line:
            return
        line = line.rstrip(b'\r\n').decode('iso-8859-1')
        try:
            method, self.uri = line.split(' ', 1)
            self.uri = self.uri.rsplit(' ', 1)[0]
        except ValueError:
            yield from self.write_error(400)
            return
        if method.upper() != 'POST':
            yield from self.write_error(405)
            return
        logging.info('Request URI: %s' % self.uri)
        self.request_headers = {}
        while line:
            line = yield from self.reader.readline()
            line = line.rstrip(b'\r\n').decode('iso-8859-1')
            if not line:
                return
            try:
                header_name, header_value = line.split(': ', 1)
                self.request_headers[header_name] = header_value
            except ValueError:
                yield from self.write_error(400)
                return

    @asyncio.coroutine
    def write_error(self, error_code):
        http_error_table = {
            400: 'Bad Request',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
            503: 'Service Unavailable'
        }
        self.writer.write(('HTTP/1.1 %s %s\r\nContent-Length: 0\r\nConnection: close\r\n\r\n' % (error_code, http_error_table[error_code])).encode('iso-8859-1', 'replace'))
        self.writer.close()
        self.reader.feed_eof()
        yield from self.reader.read()

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    loop = asyncio.get_event_loop()
    HTServer.listen(port=8888)
    loop.run_forever()

if __name__ == '__main__':
    main()
