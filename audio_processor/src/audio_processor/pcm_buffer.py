import threading


class PcmBuffer:
    def __init__(self, max_seconds, sample_rate, sample_with):
        self._buffer = bytearray()
        self._lock = threading.Lock()
        self._max_bytes = int(max_seconds * sample_rate * sample_with)

    def write(self, data: bytes) -> None:
        with self._lock:
            self._buffer.extend(data)
            if len(self._buffer) > self._max_bytes:
                self._buffer = self._buffer[-self._max_bytes :]

    def read(self, chunk_size: int) -> bytes:
        with self._lock:
            if len(self._buffer) < chunk_size:
                return b""
            chunk = bytes(self._buffer[:chunk_size])
            del self._buffer[:chunk_size]
            return chunk
