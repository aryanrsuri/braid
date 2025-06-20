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
        """
        Generate a new version stamp.
        A version stamp is a 16-byte value consisting of:
        - 8 bytes for the current time in microseconds since the epoch.
        - 2 bytes for a counter that increments with each call within the same microsecond.
        - 2 bytes for a random value to ensure uniqueness in case of multiple calls within the same microsecond.
        This method is thread-safe and ensures that each call generates a unique version stamp even if called concurrently.
        :return: A version stamp as a hex string.
        """
        now = time_ns() // 1_000
        with self._lock:
            if now != self._prev_time:
                self._prev_time = now
                self._count = 0
            else:
                self._count += 1
            packed = pack(">QHH", self._prev_time, self._count, getrandbits(16))
            return packed.hex()
    

