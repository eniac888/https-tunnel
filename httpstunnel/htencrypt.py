
import binascii
import hashlib
import os
import salsa20
import struct


class HTEncrypt:
    def __init__(self, key, nonce=None):
        if isinstance(key, str):
            key = hashlib.sha256(key.encode('utf-8', 'replace')).digest()
        if nonce is None:
            nonce = os.urandom(8)
        if len(key) != 32:
            raise ValueError('len(key) != 32')
        if len(nonce) != 8:
            raise ValueError('len(nonce) != 8')
        self.key = key
        self.nonce = nonce
        self.first_time = True

    def encrypt(self, message):
        if not self.first_time:
            self.nonce = salsa20.Salsa20_keystream(8, self.nonce, self.key)
        self.first_time = False
        return salsa20.Salsa20_xor(message, self.nonce, self.key)

    decrypt = encrypt

    def encrypt_check(self, message):
        return self.encrypt(message+struct.pack('>L', binascii.crc32(message) & 0xffffffff))

    def decrypt_check(self, message):
        message = self.decrypt(message)
        message_body = message[:-4]
        if len(message) < 4 or struct.unpack('>L', message[-4:])[0] != binascii.crc32(message_body) & 0xffffffff:
            raise ValueError('Corrupted message. Wrong encryption key?')
        return message_body


def self_test():
    try:
        key = os.urandom(32)
        enc = HTEncrypt(key)
        if enc.key != key:
            raise ValueError('enc.key != key')
        dec = HTEncrypt(key, enc.nonce)
        for i in range(4):
            message = os.urandom(i)
            message_enc = enc.encrypt_check(message)
            message_dec = dec.decrypt_check(message_enc)
            if message != message_dec:
                raise ValueError('message != message_dec')
    except ValueError as e:
        raise ValueError('Encryption module is not working') from e


self_test()
