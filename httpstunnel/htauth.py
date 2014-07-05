
import asyncio
import time
import urllib.parse

import htglobal
import htstreamutil

class HTAuth:
    @staticmethod
    @asyncio.coroutine
    def accept_auth(request):
        chunk = yield from htstreamutil.read_http_chunk(request.reader, request.request_headers)
        query = urllib.parse.parse_qs(chunk.decode('utf-8', 'replace'))
        username = query.get('username')
        password = query.get('password')
        request.writer.write(('HTTP/1.1 302 Found\r\nCache-Control: no-cache, must-revalidate\r\nContent-Length: 0\r\nLocation: %s\r\nPragma: no-cache\r\nSet-Cookie: PHPSESSID=%s; path=/\r\nConnection: Keep-Alive\r\n\r\n' % (htglobal.DATA_REDIR, 'placeholder')).encode('utf-8', 'replace'))
