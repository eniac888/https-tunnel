
import asyncio
import logging
import struct

import htstreamutil

class HTSocksServer:

    @classmethod
    def listen(cls, host=None, port=None):
        asyncio.Task(asyncio.start_server(cls, host=host, port=port))

    def __init__(self, reader, writer):
        self.reader, self.writer = reader, writer
        asyncio.Task(self.accept())

    @asyncio.coroutine
    def accept(self):
        try:
            self.socks_version = ord((yield from self.reader.read_exactly(1)))
        except asyncio.IncompleteReadError:
            return (yield from htstreamutil.full_close(self.reader, self.writer))
        if self.socks_version == 5:
            yield from self.request_socks5()
        elif self.socks_version == 4:
            yield from self.request_socks4()
        else:
            yield from htstreamutil.full_close(self.reader, self.writer)

    @asyncio.coroutine
    def fail(self, code=0x01):
        try:
            if self.socks_version == 5:
                self.writer.write(b''.join((b'\x05', bytes((code,)), b'\x01', bytes(6))))
            elif self.socks_version == 4:
                self.writer.write(b'\x00\x5b\x00\x00\x00\x00\x00\x00')
        except AttributeError:
            pass
        yield from htstreamutil.full_close(self.reader, self.writer)

    @asyncio.coroutine
    def request_socks4(self):
        try:
            command_code, port = struct.unpack('>BH', (yield from self.reader.read_exactly(3)))
            ipv4 = struct.unpack('>4B', (yield from self.reader.read_exactly(4)))
            while (yield from self.reader.read_exactly(1)) != b'\0':
                pass
            if (0, 0, 0, 0) <= ipv4 < (1,):
                host = []
                while True:
                    c = yield from self.reader.read_exactly(1)
                    if c == b'\0':
                        break
                    else:
                        host.append(c)
                host = ''.join(host)
                try:
                    host = host.decode('utf-8', 'replace')
                except UnicodeDecodeError:
                    host = host.decode('iso-8859-1')
            else:
                host = '.'.join(ipv4)
        except asyncio.IncompleteReadError:
            logging.error('Incomplete SOCKS4 request')
            yield from self.fail()
        if self.command_code == 1:
            return (yield from onconnect(host, port))
        elif self.command_code == 2:
            return (yield from onbind(host, port))
        else:
            yield from self.fail()

    @asyncio.coroutine
    def request_socks5(self):
        try:
            command_code, addr_type = struct.unpack('>BxB', (yield from self.reader.read_exactly(3)))
            if addr_type == 1:
                host = '.'.join(map(int, (yield from self.reader.read_exactly(4))))
            elif addr_type == 3:
                host_len = ord((yield from self.reader.read_exactly(1)))
                host = yield from self.reader.read_exactly(host_len)
                try:
                    host = host.decode('utf-8', 'replace')
                except UnicodeDecodeError:
                    host = host.decode('iso-8859-1')
            elif addr_type == 4:
                host = ':'.join(map(lambda x: format(x, 'x'), (yield from self.reader.read_exactly(16))))
            else:
                yield from self.fail(0x08)
        except asyncio.IncompleteReadError:
            logging.error('Incomplete SOCKS5 request')
            yield from self.fail(0x07)
        if self.command_code == 1:
            return (yield from onconnect(host, port))
        elif self.command_code == 2:
            return (yield from onbind(host, port))
        else:
            yield from self.fail(0x07)

    @asyncio.coroutine
    def onconnect(self, host, port):
        yield from self.fail(0x07)
        raise NotImplementedError

    @asyncio.coroutine
    def onbind(self, host, port):
        yield from self.fail(0x07)
        raise NotImplementedError
