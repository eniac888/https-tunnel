#!/usr/bin/env python3

import asyncio
import hashlib
import logging
import re
import salsa20

import hthttpconnector

class HTClient:
    @classmethod
    def connect(cls, gateuri):
        gateuri = hturlparser.HTURLParser(gateuri)
