import subprocess

from audio_processor.services.base_service import BaseService


class FFmpegStreamService(BaseService):
    """A background service that streams audio via UDP using ffmpeg."""

    def __init__(self, sample_rate, stream_port):
        super().__init__()
        self.sample_rate = sample_rate
        self.stream_port = stream_port

    def _run(self) -> None:
        print(f"Starting stream to: udp://127.0.0.1:{self.stream_port}")
        print(f"Sample Rate: {self.sample_rate} Hz")

        cmd = f"""
            ffmpeg
            -loglevel quiet
            -fflags nobuffer
            -flags low_delay
            -f pulse
            -i default
            -ar {self.sample_rate}
            -ac 1
            -c:a pcm_s16le
            -f s16le
            udp://127.0.0.1:{self.stream_port}
        """.split()

        try:
            process = subprocess.Popen(cmd, stdout=None, stderr=None)
        except FileNotFoundError:
            print("Error: ffmpeg is not installed or not found in system PATH.")
            return

        while self.is_running:
            if process.poll() is not None:
                print("ffmpeg process terminated unexpectedly.")
                break

            self._stop_event.wait(timeout=0.5)

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                process.kill()

            print("FFmpeg stream successfully stopped.")
