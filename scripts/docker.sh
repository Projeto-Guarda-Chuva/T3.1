IMAGE_NAME=audio-processor-x86

function build {
    sudo docker build -t $IMAGE_NAME .
}

function run {
    sudo docker run \
        -it \
        --device /dev/snd \
        -v /run/user/$(id -u)/pulse/native:/tmp/pulse-socket \
        -v ~/.cache/huggingface:/root/.cache/huggingface \
        -e PULSE_SERVER=unix:/tmp/pulse-socket \
        $IMAGE_NAME:latest
}

$1