#!/usr/bin/env python3

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--key', help='Encryption key')
    parser.add_argument('-g', '--gateway', help='Gateway address [Default: /ht/login.php]')
    parser.add_argument('-p', '--port', type=int, help='Port to set up a SOCKS proxy on [Default: 8888]', default=8888)
    parser.add_argument('-l', '--listen', help='Address to set up a SOCKS proxy on [Default: localhost]', default=None)
    args = parser.parse_args()
    htglobal.ENCRYPT_KEY = args.key
    htglobal.GATEWAY_ADDR = args.gateway
    htglobal.LISTEN_PORT = args.port
    htglobal.LISTEN_ADDR = args.listen
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.Task(HTClient.connect(gateuri='http://localhost:8888/')))
    htsocksserver.HTSocksServer(htglobal.LISTEN_PORT, htglobal.LISTEN_ADDR)
    loop.run_forever()


if __name__ == '__main__':
    main()
