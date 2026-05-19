SAMPLE_RATE=16000
STREAM_PORT=9999

echo "Starting stream to: udp://127.0.0.1:$STREAM_PORT"
echo "Sample Rate: $SAMPLE_RATE Hz"

ffmpeg -f pulse -i default \
    -ar 16000 \
    -ac 1 \
    -c:a pcm_s16le \
    -f s16le "udp://127.0.0.1:$STREAM_PORT"
