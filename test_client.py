"""
mic_client.py — Captures microphone audio and streams it to the audio monitor server.

Requirements:
    pip install requests
    ffmpeg must be installed (sudo apt install ffmpeg / pacman -S ffmpeg / etc.)

Usage:
    python client.py                  # auto-detect mic, stream forever
    python client.py --duration 5     # record 5-second chunks (default)
    python client.py --device hw:1,0  # use a specific ALSA device
    python client.py --list           # list available input devices
    python client.py --server http://192.168.1.10:5000  # remote server
"""

import argparse
import io
import subprocess
import sys
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

WAV_PORT = 8080
SERVER_URL = "http://localhost:5000"
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 5       # seconds per capture window
FFMPEG_INPUT_FORMAT = None  # auto-detected below


# ── Device detection ──────────────────────────────────────────────────────────

def detect_audio_backend():
    """Return the best ffmpeg -f input format for this system."""
    # PipeWire / PulseAudio
    try:
        result = subprocess.run(
            ["pactl", "info"], capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return "pulse"
    except FileNotFoundError:
        pass

    # ALSA fallback
    try:
        result = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return "alsa"
    except FileNotFoundError:
        pass

    # Last resort: avfoundation (macOS) or dshow (Windows) won't match, but
    # at least ffmpeg will give a clear error message.
    return "alsa"


def list_devices(backend):
    """Print available capture devices and exit."""
    print(f"Audio backend: {backend}\n")
    if backend == "pulse":
        subprocess.run(["pactl", "list", "short", "sources"])
    elif backend == "alsa":
        subprocess.run(["arecord", "-l"])
    else:
        print("Cannot list devices for this backend.")
    sys.exit(0)


def default_device(backend):
    """Return the default capture device string for ffmpeg."""
    if backend == "pulse":
        return "default"      # PulseAudio/PipeWire default source
    elif backend == "alsa":
        return "default"      # ALSA default (usually hw:0,0 or plughw:0,0)
    return "default"


# ── Audio capture ─────────────────────────────────────────────────────────────

def capture_wav_bytes(device, backend, duration, sample_rate, channels):
    """
    Capture `duration` seconds of audio from `device` using ffmpeg.
    Returns raw WAV bytes (with header) suitable for serving over HTTP.
    """
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-f", backend,
        "-i", device,
        "-t", str(duration),
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-f", "wav",
        "pipe:1",           # write WAV to stdout
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg exited {result.returncode}: {result.stderr.decode().strip()}"
        )
    return result.stdout


# ── Shared state ──────────────────────────────────────────────────────────────

_lock = threading.Lock()
_latest_wav: bytes = b""
_capture_error: str = ""


def capture_loop(device, backend, duration, sample_rate, channels):
    """Continuously capture audio in a background thread."""
    global _latest_wav, _capture_error
    print(f"[mic] Starting capture: backend={backend}, device={device}, "
          f"{duration}s chunks @ {sample_rate}Hz")
    while True:
        try:
            wav = capture_wav_bytes(device, backend, duration, sample_rate, channels)
            with _lock:
                _latest_wav = wav
                _capture_error = ""
            print(f"[mic] Captured {len(wav):,} bytes")
        except Exception as e:
            with _lock:
                _capture_error = str(e)
            print(f"[mic] Capture error: {e}", file=sys.stderr)
            time.sleep(1)


# ── HTTP server (same interface the Flask app expects) ────────────────────────

class WavHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        with _lock:
            wav = _latest_wav
            err = _capture_error

        if not wav:
            msg = (err or "No audio captured yet").encode()
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(wav)))
        self.end_headers()
        self.wfile.write(wav)

    def log_message(self, fmt, *args):
        print(f"[wav-server] {args[0]}")


# ── One-shot command trigger (optional interactive mode) ──────────────────────

def trigger_command(server_url):
    print(f"\nCalling {server_url}/command ...")
    try:
        r = requests.get(f"{server_url}/command", timeout=15)
        print(f"Status   : {r.status_code}")
        print(f"Response : {r.json()}")
    except Exception as e:
        print(f"Error: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Mic client — streams microphone audio to the audio monitor server."
    )
    parser.add_argument("--device", default=None,
                        help="Input device (e.g. 'default', 'hw:1,0', 'alsa_input.pci...')")
    parser.add_argument("--duration", type=float, default=CHUNK_DURATION,
                        help=f"Seconds per capture chunk (default: {CHUNK_DURATION})")
    parser.add_argument("--rate", type=int, default=SAMPLE_RATE,
                        help=f"Sample rate in Hz (default: {SAMPLE_RATE})")
    parser.add_argument("--channels", type=int, default=CHANNELS,
                        help=f"Number of channels (default: {CHANNELS})")
    parser.add_argument("--server", default=SERVER_URL,
                        help=f"Flask server URL (default: {SERVER_URL})")
    parser.add_argument("--port", type=int, default=WAV_PORT,
                        help=f"Local WAV server port (default: {WAV_PORT})")
    parser.add_argument("--list", action="store_true",
                        help="List available audio input devices and exit")
    parser.add_argument("--once", action="store_true",
                        help="After starting, press Enter to trigger /command once")
    args = parser.parse_args()

    backend = detect_audio_backend()
    print(f"Detected audio backend: {backend}")

    if args.list:
        list_devices(backend)

    device = args.device or default_device(backend)

    # Start capture loop in background
    capture_thread = threading.Thread(
        target=capture_loop,
        args=(device, backend, args.duration, args.rate, args.channels),
        daemon=True,
    )
    capture_thread.start()

    # Wait for the first chunk before starting the HTTP server
    print("Waiting for first audio chunk...", end="", flush=True)
    for _ in range(int(args.duration * 10) + 20):
        with _lock:
            ready = bool(_latest_wav)
        if ready:
            break
        time.sleep(0.1)
        print(".", end="", flush=True)
    print()

    # Start WAV HTTP server
    httpd = HTTPServer(("0.0.0.0", args.port), WavHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"WAV server listening on http://localhost:{args.port}/audio.wav")
    print(f"Flask server target    : {args.server}")
    print("Streaming continuously. Ctrl+C to stop.\n")

    if args.once:
        input("Press Enter to call /command once...")
        trigger_command(args.server)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.shutdown()


if __name__ == "__main__":
    main()