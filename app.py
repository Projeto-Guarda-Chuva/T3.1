import io
import json
import math
import struct
import threading
import time
from vosk import Model, KaldiRecognizer
from flask import Flask, jsonify, render_template_string
from fetch import fetch_pcm
from commands import VALID_COMMANDS

app = Flask(__name__)

AUDIO_URL = "http://localhost:8080/audio.wav"
MAX_SECONDS = 2
NOISE_POLL_INTERVAL = 1.0
NOISE_HISTORY_MINUTES = 5
NOISE_OUTLIER_FACTOR = 2.0
SAMPLE_RATE = 16000
DASHBOARD_HTML_MODEL = "dashboard.model"

# Note: You are checking for Portuguese words ("SIM", "NÃO"), 
# but loading an English model. Consider grabbing a PT-BR vosk model!
model = Model("vosk-model-small-pt-0.3")

with open(DASHBOARD_HTML_MODEL, 'r') as file:
    dashboard_html = file.read()

# --- Shared State ---
shared_state_lock = threading.Lock()
noise_history = []
latest_raw_pcm = b""


def classify_text(text):
    text = text.strip().upper()
    if not text:
        return "NONE"
    cmd = reversed(text.split())
    for id in cmd:
        if id in VALID_COMMANDS:
            return id
    return "UNKNOWN"


def compute_rms(raw_pcm):
    samples = struct.unpack(f"<{len(raw_pcm)//2}h", raw_pcm)
    if not samples:
        return 0.0
    mean_sq = sum(s * s for s in samples) / len(samples)
    return math.sqrt(mean_sq)


# --- Unified Background Loop ---
def background_audio_loentry = {"timestamp": time.time(), "rms": round(rms, 2)}op():
    global latest_raw_pcm
    max_entries = int(NOISE_HISTORY_MINUTES * 60 / NOISE_POLL_INTERVAL)

    while True:
        try:
            raw, err = fetch_pcm(AUDIO_URL, SAMPLE_RATE)
            if err or raw is None:
                print(f"Audio fetch error: {err}")
            else:
                rms = compute_rms(raw)
                entry = {"timestamp": time.time(), "rms": round(rms, 2)}
                
                max_bytes = MAX_SECONDS * SAMPLE_RATE * 2
                if len(raw) > max_bytes:
                    raw = raw[-max_bytes:]

                with shared_state_lock:
                    noise_history.append(entry)
                    while len(noise_history) > max_entries:
                        noise_history.pop(0)
                    
                    latest_raw_pcm = raw

        except Exception as e:
            print(f"Background loop error: {e}")

        time.sleep(NOISE_POLL_INTERVAL)


# --- API Endpoints ---
@app.route("/command", methods=["GET"])
def get_command():
    try:
        with shared_state_lock:
            raw = latest_raw_pcm
            
        if not raw:
            return jsonify({"error": "No audio fetched yet"}), 503

        rec = KaldiRecognizer(model, SAMPLE_RATE)
        rec.AcceptWaveform(raw)
        result = json.loads(rec.FinalResult())
        text = result.get("text", "")
        print(f"Vosk: '{text}' (from {len(raw)} bytes)")

        cmd = classify_text(text) if text.strip() else "NONE"
        return jsonify({"command": cmd, "text": text})
        
    except Exception as e:
        print(f"Recognition error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/noise", methods=["GET"])
def get_noise():
    with shared_state_lock:
        history = list(noise_history)

    if not history:
        return jsonify({"error": "no data yet"}), 503

    rms_values = [e["rms"] for e in history]
    current_rms = rms_values[-1]
    avg_rms = sum(rms_values) / len(rms_values)
    max_rms = max(rms_values)
    min_rms = min(rms_values)

    if len(rms_values) >= 2:
        variance = sum((v - avg_rms) ** 2 for v in rms_values) / len(rms_values)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    threshold = avg_rms + NOISE_OUTLIER_FACTOR * std_dev
    outliers = [e for e in history if e["rms"] > threshold] if std_dev > 0 else []

    return jsonify({
        "current_rms": current_rms,
        "average_rms": round(avg_rms, 2),
        "max_rms": max_rms,
        "min_rms": min_rms,
        "std_dev": round(std_dev, 2),
        "outlier_threshold": round(threshold, 2),
        "outliers": outliers,
        "samples_count": len(history),
    })

@app.route("/view", methods=["GET"])
def view_dashboard():
    """
    Serves a frontend interface to visualize the waveform
    """
    return render_template_string(dashboard_html, poll_interval=NOISE_POLL_INTERVAL)


if __name__ == "__main__":
    t = threading.Thread(target=background_audio_loop, daemon=True)
    t.start()
    
    print(f"Audio source: {AUDIO_URL}")
    print(f"Max audio: {MAX_SECONDS}s, sample rate: {SAMPLE_RATE}")
    print(f"Unified monitor loop: every {NOISE_POLL_INTERVAL}s, {NOISE_HISTORY_MINUTES} min history")
    app.run(host="0.0.0.0", port=5000)