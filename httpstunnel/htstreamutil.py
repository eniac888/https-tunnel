
import asyncio


@asyncio.coroutine
def full_close(reader, writer):
    try:
        writer.close()
    except Exception:
        pass
    try:
        reader.feed_eof()
    except Exception:
        pass
    try:
        yield from reader.read()
    except Exception:
        pass
    try:
        yield from writer.drain()
    except Exception:
        pass


@asyncio.coroutine
def read_http_chunk(reader, headers={'Content-Encoding': 'chunked'}):
    if headers.get('Content-Encoding') == 'chunked':
        chunk_length = int((yield from reader.readline()).decode('iso-8859-1'), 16)
        if chunk_length != 0:
            return (yield from reader.read_exactly(chunk_length))
        else:
            return b''
    elif 'Content-Length' in headers:
        return (yield from reader.read_exactly(int(headers['Content-Length'])))
    else:
        return (yield from reader.read())
