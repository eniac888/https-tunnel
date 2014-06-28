
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
