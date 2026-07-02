import math
import struct
import time
from typing import Callable

from typing_extensions import override

from audio_processor.command_recognizer import CommandRecognizer
from audio_processor.models.base_speech_model import BaseSpeechModel
from audio_processor.pcm_buffer import PcmBuffer
from audio_processor.services.base_service import BaseService


class AudioProcessorService(BaseService):
    def __init__(
        self,
        pcm_buffer: PcmBuffer,
        model: BaseSpeechModel,
        command_recognizer: CommandRecognizer,
        command_callback: Callable[[str], None],
        noise_threshold: float = 0.0,
        noise_gate_enabled: bool = False,
        broadcast_interval_ms: int = 100,
    ):
        super().__init__()

        self._pcm_buffer = pcm_buffer
        self._model = model
        self._command_recognizer = command_recognizer
        self._command_callback = command_callback
        self._noise_threshold = noise_threshold
        self._noise_gate_enabled = noise_gate_enabled
        self._rms = 0

    def get_rms(self) -> float:
        return self._rms

    def _calculate_rms(self, data: bytes) -> float:
        count = len(data) // 2
        if count == 0:
            return 0.0

        samples = struct.unpack(f"<{count}h", data)
        sum_squares = sum(s * s for s in samples)
        return math.sqrt(sum_squares / count)

    @override
    def _run(self) -> None:
        while self.is_running:
            chunk = self._pcm_buffer.read(4096)

            if not chunk:
                # Sleep briefly if there is no audio chunk to avoid spinning CPU
                time.sleep(0.01)
                continue

            self._rms = self._calculate_rms(chunk)

            if self._rms > 0:
                self._rms = 20 * math.log(self._rms / 32767)
            else:
                self._rms = -100

            # # Noise gate check
            # if self._noise_gate_enabled and rms < self._noise_threshold:
            # (caso o comando for dito em um tom de voz muito baixo ele não é enviado)
            # Necessario equilibrar e definir "silêncio"
            #     continue

            if self._model.feed(chunk):
                _ = self._model.get_final_text()
            else:
                partial_text = self._model.get_partial_text()

                for word in partial_text.split():
                    command = self._command_recognizer.recognize(word)

                    if command:
                        print(command)
                        self._command_callback(command)
