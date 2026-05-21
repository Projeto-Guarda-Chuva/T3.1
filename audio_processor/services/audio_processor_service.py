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
    ):
        super().__init__()

        self._pcm_buffer = pcm_buffer
        self._model = model
        self._command_recognizer = command_recognizer
        self._gateway_service = gateway_service

    @override
    def _run(self) -> None:
        while self.is_running:
            chunk = self._pcm_buffer.read(4096)

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
