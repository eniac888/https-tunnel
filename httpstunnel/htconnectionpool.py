
import asyncio

import htglobal


class HTConnectionPool:
    connections = {}
    _flush_idle_connections_running = False

    @staticmethod
    def _get_addr_tuple(host, port, ssl):
        return host, port, bool(ssl)

    @classmethod
    @asyncio.coroutine
    def get_connection(cls, host=None, port=None, *args, ssl=None, **kwargs):
        cls.flush_idle_connections()
        addr_tuple = cls._get_addr_tuple(host, port, ssl)
        if addr_tuple in cls.connections:
            result = cls.connections[addr_tuple].pop(0)[:2]
            if len(cls.connections[addr_tuple]) == 0:
                del cls.connections[addr_tuple]
            return result
        else:
            return (yield from asyncio.open_connection(host, port, ssl=ssl, *args, **kwargs))

    @classmethod
    @asyncio.coroutine
    def push_connection(cls, reader, writer, host=None, port=None, *args, ssl=None, **kwargs):
        if reader.at_eof():
            yield from htstreamutil.full_close(reader, writer)
            return
        addr_tuple = cls._get_addr_tuple(host, port, ssl)
        if addr_tuple not in cls.connections:
            cls.connections[addr_tuple] = list()
        cls.connections[addr_tuple].append((reader, writer, asyncio.get_event_loop().time()))
        cls.flush_idle_connections()

    @classmethod
    def flush_idle_connections(cls):
        if cls._flush_idle_connections_running:
            return
        if len(cls.connections) != 0:
            cls._flush_idle_connections_running = True
            loop = asyncio.get_event_loop()
            time_now = loop.time()
            time_min = time_now
            for addr_tuple in cls.connections:
                connections_set = cls.connections[addr_tuple]
                for idx, this_connection in reversed(list(enumerate(connections_set))):  # list() generates a new copy
                    if this_connection[0].at_eof() or this_connection[2] - time_now > htglobal.HTTP_IDLE_TIME:
                        del connections_set[idx]  # delete in reversed order
                        try:
                            this_connection[1].close()
                        except Exception:
                            pass
                        try:
                            this_connection[0].feed_eof()
                        except Exception:
                            pass
                    else:
                        time_min = min(time_min, this_connection[2])
                if len(connections_set) == 0:
                    del cls.connections[addr_tuple]
            if len(cls.connections) != 0:
                loop.call_later(htglobal.HTTP_IDLE_TIME+time_min-time_now, flush_idle_connections)
            else:
                cls._flush_idle_connections_running = False
