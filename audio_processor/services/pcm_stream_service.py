import socket

from typing_extensions import override

from audio_processor.pcm_buffer import PcmBuffer
from audio_processor.services.base_service import BaseService


class PcmStreamService(BaseService):
    def __init__(self, host: str, port: int, pcm_buffer: PcmBuffer):
        super().__init__()

        self._pcm_buffer = pcm_buffer
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((host, port))

    @override
    def stop(self) -> None:
        super().stop()
        self._sock.close()

    @override
    def _run(self) -> None:
        while self.is_running:
            data, addr = self._sock.recvfrom(4096)
            self._pcm_buffer.write(data)
