import wave
import requests
import io
import struct

def fetch_pcm(audio_url, sample_rate):
    resp = requests.get(audio_url, timeout=10)
    resp.raise_for_status()

    with wave.open(io.BytesIO(resp.content), "rb") as w:
        src_rate = w.getframerate()
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        raw = w.readframes(w.getnframes())

    if n_channels == 2:
        samples = struct.unpack(f"<{len(raw)//2}h", raw)
        raw = struct.pack(f"<{len(samples)//2}h", *samples[::2])

    if sampwidth != 2:
        return None, "unsupported sample width"

    if src_rate != sample_rate:
        samples = struct.unpack(f"<{len(raw)//2}h", raw)
        ratio = src_rate / sample_rate
        new_len = int(len(samples) / ratio)
        resampled = []
        for i in range(new_len):
            src_idx = i * ratio
            idx = int(src_idx)
            if idx + 1 < len(samples):
                frac = src_idx - idx
                val = int(samples[idx] * (1 - frac) + samples[idx + 1] * frac)
            else:
                val = samples[idx]
            resampled.append(max(-32768, min(32767, val)))
        raw = struct.pack(f"<{len(resampled)}h", *resampled)

    return raw, None