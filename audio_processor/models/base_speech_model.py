from abc import ABC, abstractmethod


class BaseSpeechModel(ABC):
    """Abstract interface for any streaming Speech-to-Text engine."""

    @abstractmethod
    def feed(self, chunk: bytes) -> bool:
        """
        Feeds a raw audio chunk to the engine.
        Returns True if a final utterance/sentence boundary was detected.
        """
        pass

    @abstractmethod
    def get_partial_text(self) -> str:
        """Returns the current live, unfinalized transcription preview."""
        pass

    @abstractmethod
    def get_final_text(self) -> str:
        """Returns the definitive finalized transcription text."""
        pass
