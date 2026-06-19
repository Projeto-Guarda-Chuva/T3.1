import socket
from unittest.mock import MagicMock, patch
import pytest

from audio_processor.services.pcm_stream_service import PcmStreamService


def test_pcm_stream_service_initialization():
    """Testa se o serviço inicializa o socket UDP corretamente na porta desejada."""
    mock_buffer = MagicMock()
    host = "127.0.0.1"
    port = 12345

    # Isolamos a criação do socket usando patch
    with patch("socket.socket") as mock_socket_class:
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value = mock_sock_instance

        service = PcmStreamService(host, port, mock_buffer)

        # Garante que ele criou um socket IPv4 (AF_INET) e UDP (SOCK_DGRAM)
        mock_socket_class.assert_called_once_with(
            socket.AF_INET, socket.SOCK_DGRAM)
        # Garante que ele deu bind no endereço e porta corretos
        mock_sock_instance.bind.assert_called_once_with((host, port))


def test_pcm_stream_service_stop():
    """Testa se o método stop fecha o socket adequadamente."""
    mock_buffer = MagicMock()

    with patch("socket.socket") as mock_socket_class:
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value = mock_sock_instance

        service = PcmStreamService("127.0.0.1", 12345, mock_buffer)
        service.stop()

        # Garante que o método close() do socket foi acionado para liberar a porta
        mock_sock_instance.close.assert_called_once()


def test_pcm_stream_service_run_once():
    """Testa se o loop lê dados do socket e escreve corretamente no pcm_buffer."""
    mock_buffer = MagicMock()

    with patch("socket.socket") as mock_socket_class:
        mock_sock_instance = MagicMock()
        mock_socket_class.return_value = mock_sock_instance

        # Simula o socket recebendo um pacote de áudio "fake_audio_data" de um IP qualquer
        fake_data = b"fake_audio_data"
        fake_addr = ("127.0.0.1", 55555)
        mock_sock_instance.recvfrom.return_value = (fake_data, fake_addr)

        service = PcmStreamService("127.0.0.1", 12345, mock_buffer)

        # Como _run tem um loop 'while self.is_running', alteramos o estado
        # logo após a primeira execução para o loop não ficar infinito no teste.
        def side_effect(*args, **kwargs):
            service.stop()  # Desliga o 'is_running' após ler a primeira vez
            return fake_data, fake_addr

        mock_sock_instance.recvfrom.side_effect = side_effect

        # Executa a lógica de recebimento
        service._run()

        # Validações cruciais:
        # 1. Ele tentou ler do socket com o buffer de 4096 bytes?
        mock_sock_instance.recvfrom.assert_called_with(4096)
        # 2. Ele pegou o dado recebido e mandou salvar no PcmBuffer?
        mock_buffer.write.assert_called_once_with(fake_data)
