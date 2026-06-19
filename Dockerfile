FROM nvidia/cuda:12.6.0-runtime-ubuntu24.04
ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    portaudio19-dev \
    python3-dev \
    build-essential \
    python3.12-venv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

COPY requirements.txt /app/
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install -r /app/requirements.txt

COPY models/vosk-model-small-pt-0.3 /app/models/vosk-model-small-pt-0.3
COPY audio_processor /app
COPY config.json /app

RUN pip3 install .

# CMD ["python3", "-m", "audio_processor.main"]
#CMD ["pytest"]
