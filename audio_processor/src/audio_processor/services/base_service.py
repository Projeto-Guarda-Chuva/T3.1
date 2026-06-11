import threading
from abc import ABC, abstractmethod


class BaseService(ABC):
    """A thread-safe base class for background services."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

    def start(self) -> None:
        """Spawns the background thread and begins execution."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signals the background thread to gracefully shut down."""
        self._stop_event.set()

    def join(self) -> None:
        """Waits for the background thread to completely finish."""
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

    @property
    def is_running(self) -> bool:
        """Helper to easily check if the service should keep looping."""
        return not self._stop_event.is_set()

    @abstractmethod
    def _run(self) -> None:
        pass
