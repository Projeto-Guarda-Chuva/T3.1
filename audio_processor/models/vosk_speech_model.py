import json
import time
from dataclasses import dataclass, field

from typing_extensions import override
from vosk import KaldiRecognizer, Model, SetLogLevel

from audio_processor.models.base_speech_model import BaseSpeechModel

SetLogLevel(1)


class VoskSpeechModel(BaseSpeechModel):
    @dataclass
    class _State:
        last_stable_text: str = field(default="")
        last_emitted_words: list = field(default_factory=lambda: [])
        stability_window_begin: float = field(default_factory=time.time)

    def __init__(
        self,
        model_path: str,
        sample_rate: int,
        stability_interval_ms: int,
        word_memory_size: int,
    ):
        self._model = Model(model_path)
        self._recognizer = KaldiRecognizer(self._model, sample_rate)
        self._stability_interval_ms = stability_interval_ms
        self._word_memory_size = word_memory_size
        self._state = self._State()

    @override
    def feed(self, chunk: bytes) -> bool:
        return self._recognizer.AcceptWaveform(chunk)

    @override
    def get_partial_text(self) -> str:
        """Returns only the *new, stable* words, ignoring ghost words and duplicates."""
        res = json.loads(self._recognizer.PartialResult())
        current_partial = res.get("partial", "").strip()
        now = time.time()

        if not current_partial:
            return ""

        if current_partial != self._state.last_stable_text:
            self._state.last_stable_text = current_partial
            self._state.stability_window_begin = now
            return ""

        stability_time_ms = int((now - self._state.stability_window_begin) * 1000)

        if stability_time_ms < self._stability_interval_ms:
            return ""

        current_words = current_partial.split()
        new_words = [
            word for word in current_words if word not in self._state.last_emitted_words
        ]

        self._state.last_emitted_words.extend(new_words)

        if len(self._state.last_emitted_words) > self._word_memory_size:
            self._state.last_emitted_words = self._state.last_emitted_words[
                -self._word_memory_size :
            ]

        return " ".join(new_words)

    @override
    def get_final_text(self) -> str:
        """Handles the true silence break, resetting the stream state."""
        res = json.loads(self._recognizer.Result())
        final_text = res.get("text", "").strip()

        self._state.last_stable_text = ""
        self._state.last_emitted_words = []
        self._state.stability_window_begin = time.time()

        return final_text


# class VoskSpeechModel(BaseSpeechModel):
#     """Vosk implementation of the generic speech to text interface."""

#     def __init__(self, model_path: str, sample_rate: int):
#         self.model = Model(model_path)
#         self.recognizer = KaldiRecognizer(self.model, sample_rate)

#     @override
#     def feed(self, chunk: bytes) -> bool:
#         return self.recognizer.AcceptWaveform(chunk)

#     @override
#     def get_partial_text(self) -> str:
#         res = json.loads(self.recognizer.PartialResult())
#         return res.get("partial", "")

#     @override
#     def get_final_text(self) -> str:
#         res = json.loads(self.recognizer.Result())
#         return res.get("text", "")
