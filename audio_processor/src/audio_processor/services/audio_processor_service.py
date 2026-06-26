import math
import struct
import time
from typing_extensions import override

from audio_processor.command_recognizer import CommandRecognizer
from audio_processor.models.base_speech_model import BaseSpeechModel
from audio_processor.output_message_type import OutputMessageType
from audio_processor.pcm_buffer import PcmBuffer
from audio_processor.services.base_service import BaseService
from audio_processor.services.gateway_service import GatewayService


class AudioProcessorService(BaseService):
    def __init__(
        self,
        pcm_buffer: PcmBuffer,
        model: BaseSpeechModel,
        command_recognizer: CommandRecognizer,
        gateway_service: GatewayService,
        noise_threshold: float = 0.0,
        noise_gate_enabled: bool = False,
        broadcast_interval_ms: int = 100,
    ):
        super().__init__()

        self._pcm_buffer = pcm_buffer
        self._model = model
        self._command_recognizer = command_recognizer
        self._gateway_service = gateway_service
        self._noise_threshold = noise_threshold
        self._noise_gate_enabled = noise_gate_enabled
        self._broadcast_interval_ms = broadcast_interval_ms
        self._last_broadcast_time = 0.0

    def _calculate_rms(self, data: bytes) -> float:
        """Calculates Root Mean Square (RMS) of a 16-bit mono PCM chunk."""
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

            rms = self._calculate_rms(chunk)

            # Periodic noise level transmission to web gateway
            now = time.time()
            if (now - self._last_broadcast_time) * 1000 >= self._broadcast_interval_ms:
                self._gateway_service.deliver(
                    OutputMessageType.NOISE_LEVEL, rms
                )
                self._last_broadcast_time = now

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
                        self._gateway_service.deliver(
                            OutputMessageType.COMMAND, command
                        )
