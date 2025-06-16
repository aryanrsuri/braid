"""
Author: Aryan Suri
Utility function for generating a new version stamp, validating a version stamp, editing a version stamp
"""
from time import time_ns
from threading import Lock
from struct import pack, unpack
from random import getrandbits

type versionid = str  # Type alias for version stamp, represented as a hex string

class versionstamp:
    def __init__(self) -> None:
        self._prev_time = 0
        self._count = 0
        self._lock = Lock()

    def __call__(self) -> versionid:
        now = time_ns() // 1_000
        with self._lock:
            if now != self._prev_time:
                self._prev_time = now
                self._count = 0
            else:
                self._count += 1
            packed = pack(">QHH", self._prev_time, self._count, getrandbits(16))
        return packed.hex()

    def update(self, version: versionid) -> versionid:
        if not self.validate(version):
            raise ValueError("Poisoned version stamp")
        packed = bytes.fromhex(version)
        time, _, rand = unpack(">QHH", packed)
        with self._lock:
            if time > self._prev_time:
                self._prev_time = time
                self._count = 0
            elif time == self._prev_time:
                self._count += 1
            else:
                raise ValueError("Version stamp is out of order")
            packed = pack(">QHH", self._prev_time, self._count, rand)
        return packed.hex()
    
    def validate(self, version: versionid) -> bool:
        if len(version) != 24 or not all(c in "0123456789abcdef" for c in version):
            return False
        try:
            packed = bytes.fromhex(version)
            if len(packed) != 12:
                return False
            return True
        except Exception:
            return False


