FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH=/app/src

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    portaudio19-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY models/vosk-model-small-pt-0.3 /app/models/vosk-model-small-pt-0.3
COPY audio_processor /app
COPY config.json /app
WORKDIR /app

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install .

CMD ["python3", "-m", "audio_processor.main"]
#CMD ["pytest"]
