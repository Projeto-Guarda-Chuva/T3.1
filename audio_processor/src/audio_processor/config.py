import json
from pathlib import Path

from pydantic import BaseModel


class AudioConfig(BaseModel):
    sample_rate: int
    sample_with: int
    buffer_max_size_seconds: int
    stream_host: str
    stream_port: int


class SpeechRecognitionConfig(BaseModel):
    model_path: str
    stability_window_ms: int
    word_memory_size: int


class CommandRecognitionConfig(BaseModel):
    available_commands: list[str]
    similarity_margin: float
    command_cooldown_ms: int


class GatewayConfig(BaseModel):
    host: str
    port: int
    command_output_host: str
    command_output_port: int


class NoiseDetectionConfig(BaseModel):
    noise_threshold: float
    noise_gate_enabled: bool
    broadcast_interval_ms: int


class AppConfig(BaseModel):
    audio: AudioConfig
    speech_recognition: SpeechRecognitionConfig
    command_recognition: CommandRecognitionConfig
    gateway: GatewayConfig
    noise_detection: NoiseDetectionConfig

    @classmethod
    def load_from_file(cls, filepath: str | Path) -> "AppConfig":
        """Factory method to read the JSON file and parse it into this object."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
