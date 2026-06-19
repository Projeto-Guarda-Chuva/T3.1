from audio_processor.pcm_buffer import PcmBuffer

def test_write_and_read_basic():
    # Configurando um buffer pequeno: 1 segundo, sample_rate de 1000Hz, 1 byte por sample = max 1000 bytes
    buffer = PcmBuffer(max_seconds=1, sample_rate=1000, sample_with=1)

    audio_data = b"\x01\x02\x03\x04\x05"
    buffer.write(audio_data)

    # Lendo exatamente o tamanho que escrevemos
    assert buffer.read(5) == b"\x01\x02\x03\x04\x05"


def test_read_insufficient_data():
    buffer = PcmBuffer(max_seconds=1, sample_rate=1000, sample_with=1)

    buffer.write(b"\x01\x02")

    # Tentando ler 5 bytes quando só existem 2 no buffer
    # Deve retornar vazio e NÃO apagar o que está lá dentro
    assert buffer.read(5) == b""

    # Provando que os 2 bytes originais ainda continuam guardados
    assert buffer.read(2) == b"\x01\x02"


def test_buffer_partial_reads():
    buffer = PcmBuffer(max_seconds=1, sample_rate=1000, sample_with=1)

    buffer.write(b"\x01\x02\x03\x04\x05")

    # Lê os primeiros 2 bytes
    assert buffer.read(2) == b"\x01\x02"
    # Lê os próximos 3 bytes restantes
    assert buffer.read(3) == b"\x03\x04\x05"


def test_buffer_overflow_limits_bytes():
    # Criamos um buffer que suporta no MÁXIMO 4 bytes
    # Ex: 2 segundos * 1 Hz * 2 bytes_per_sample = 4 bytes
    buffer = PcmBuffer(max_seconds=2, sample_rate=1, sample_with=2)

    # Escrevemos 6 bytes (passou do limite de 4)
    buffer.write(b"\x11\x22\x33\x44\x55\x66")

    # Como o limite é 4, os bytes mais antigos (\x11\x22) devem ter sido descartados
    # Restando apenas os 4 últimos enviados
    assert buffer.read(4) == b"\x33\x44\x55\x66"
