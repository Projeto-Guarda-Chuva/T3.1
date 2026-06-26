from audio_processor.command_recognizer import CommandRecognizer
from audio_processor.config import AppConfig
from audio_processor.models.vosk_speech_model import VoskSpeechModel
from audio_processor.pcm_buffer import PcmBuffer
from audio_processor.services.audio_processor_service import AudioProcessorService
from audio_processor.services.gateway_service import GatewayService
from audio_processor.services.http_server_service import HttpServerService 
from audio_processor.services.pcm_stream_service import PcmStreamService

config = AppConfig.load_from_file("config.json")

pcm_buffer = PcmBuffer(
    config.audio.buffer_max_size_seconds,
    config.audio.sample_rate,
    config.audio.sample_with,
)

speech_model = VoskSpeechModel(
    model_path=config.speech_recognition.model_path,
    sample_rate=config.audio.sample_rate,
    stability_interval_ms=config.speech_recognition.stability_window_ms,
    word_memory_size=config.speech_recognition.word_memory_size,
)

# Services

command_recognizer = CommandRecognizer(
    config.command_recognition.available_commands,
    config.command_recognition.similarity_margin,
    config.command_recognition.command_cooldown_ms,
)

pcm_stream = PcmStreamService(
    config.audio.stream_host,
    config.audio.stream_port,
    pcm_buffer,
)

gateway = GatewayService(config.gateway.host, config.gateway.port)

audio_processor = AudioProcessorService(
    pcm_buffer,
    speech_model,
    command_recognizer,
    gateway,
)

http_server = HttpServerService(           
    host=config.http_server.host,          
    port=config.http_server.port,
    gateway=gateway,
    pcm_buffer=pcm_buffer,
)

pcm_stream.start()
gateway.start()
audio_processor.start()
http_server.start()

http_server.wait_for_ready(timeout=3.0)

try:
    while True:
        pass
except KeyboardInterrupt:
    print("\nLoop stopped by user.")

http_server.stop()
pcm_stream.stop()
gateway.stop()
audio_processor.stop()

http_server.join() 
pcm_stream.join()
gateway.join()
audio_processor.join()
