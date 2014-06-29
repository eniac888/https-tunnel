#!/usr/bin/env python3

import argparse
import asyncio
import hashlib
import logging
import urllib.request

import htglobal
import hthttperror
import htstreamutil


class HTServer:

    @classmethod
    def listen(cls, host=None, port=None):
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
            yield from self.dispatch_http_request()

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
            return (yield from self.write_error(400))
        logging.info('Request URI: %s' % self.uri)
        if method.upper() != 'POST':
            return (yield from self.write_error(405))
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
                return (yield from self.write_error(400))

    @asyncio.coroutine
    def write_error(self, error_code):
        self.writer.write(hthttperror.get_http_error(error_code)
        yield from htstreamutil.full_close(self.reader, self.writer)

    @asyncio.coroutine
    def dispatch_http_request(self):
        if self.uri == htglobal.GATEWAY_ADDR:
            
        if self.uri == htglobal.DATA_ADDR:


def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key', help='Encryption key')
    parser.add_argument('-g', '--gateway', help='Gateway address [Default: /ht/login.php]', default='/ht/login.php')
    parser.add_argument('-d', '--data', help='Data transport address [Default: /ht/file.php]', default='/ht/file.php')
    parser.add_argument('-p', '--port', type=int, help='Port to listen on [Default: 8888]', default=8888)
    parser.add_argument('-l', '--listen', help='Address to listen on [Default: localhost]', default=None)
    args = parser.parse_args()
    htglobal.ENCRYPT_KEY = args.key
    htglobal.GATEWAY_ADDR = args.gateway
    htglobal.DATA_ADDR = args.data
    htglobal.LISTEN_PORT = args.port
    htglobal.LISTEN_ADDR = args.listen
    loop = asyncio.get_event_loop()
    HTServer.listen(host=htglobal.LISTEN_ADDR, port=htglobal.LISTEN_PORT)
    loop.run_forever()


if __name__ == '__main__':
    main()
