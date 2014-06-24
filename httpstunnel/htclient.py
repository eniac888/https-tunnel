#!/usr/bin/env python3

import asyncio
import hashlib
import logging
import re
import salsa20

import hthttpconnector

class HTClient:
    @classmethod
    @asyncio.coroutine
    def connect(cls, gateuri):
        gateway_http = hthttpconnector.HTHTTPConnector(gateuri)
        yield from gateway_http.connect('POST')
        yield from gateway_http.close()

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(HTClient.connect(gateuri='http://localhost:8888/'))

if __name__ == '__main__':
    main()
