#!/usr/bin/env python3
import hashlib

"""Hand-made cipher function. Expected to be pretty safe,
as long as HASHFUNC is know safe and BLOCK_SIZE long enough"""

HASHFUNC = hashlib.sha256
BLOCK_SIZE = 16

def _kiter(key:bytes):
    """Iterates on the key : hashes the key (using HASHFUNC), then yields the beginning of the hash.
    The full hash is used as subsequent key. Re-hashes after BLOCK_SIZE bytes yielded.
    yields : int"""
    while True :
        key = HASHFUNC(key).digest()
        yield from key[:BLOCK_SIZE]

def cipher(string:bytes, key:bytes):
    """Kind of Vernam mask : xors the text with the key hashed n times (as yielded by _kiter)
    yields : int"""
    yield from (s^b for s,b in zip(string, _kiter(key)))

decipher = cipher

# chat-specific utilities


class BytesPipe :

    __slots__ = "content"

    def __init__(self, initialvalue=tuple()):
        self.content = bytearray(initialvalue)

    def __iadd__(self, what:"iterable_of_ints"):
        self.content.extend(what)
        return self

    feed = __iadd__

    def __iter__(self):
        return self

    def __next__(self) :
        if len(self.content):
            return self.content.pop(0)
        else :
            raise StopIteration

    def __len__(self):
        return len(self.content)


class Cipherer :

    __slots__ = ("_pipe", "_ciph")

    def __init__(self, key):
        self._pipe = BytesPipe()
        self._ciph = cipher(iter(self._pipe), key)

    def cipher(self, message):
        self._pipe.feed(message)
        return bytes(next(self._ciph) for m in message)

    decipher = cipher
    decipher.__name__ = "decipher"
