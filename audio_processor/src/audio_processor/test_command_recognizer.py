
import pytest
import time  
from unittest.mock import patch
from command_recognizer import CommandRecognizer


def test_recognize_success():
    # Cenário 1: Reconhecer um comando com sucesso dentro da margem
    commands = ["ligar", "desligar", "tocar"]
    # Colocamos um cooldown bem baixo aqui (10ms) para o teste rodar rápido
    recognizer = CommandRecognizer(
        available_commands=commands,
        command_similarity_margin=0.7,
        command_cooldown=10,
    )

    # "ligar" é idêntico a "ligar" (similaridade 1.0)
    assert recognizer.recognize("ligar") == "ligar"

    # Esperamos 15 milissegundos (0.015 segundos) para o cooldown liberar
    time.sleep(0.015)

    # Agora "liga" deve passar livremente pelo cooldown
    assert recognizer.recognize("liga") == "ligar"


def test_recognize_failed_similarity():
    # Cenário 2: Não reconhecer quando a palavra é muito diferente
    commands = ["ligar", "desligar"]
    recognizer = CommandRecognizer(
        available_commands=commands,
        command_similarity_margin=0.8,
        command_cooldown=1000,
    )

    # "abrir" não se parece com nenhum comando disponível
    assert recognizer.recognize("abrir") is None


def test_recognize_cooldown_blocking():
    # Cenário 3: Testar se o cooldown bloqueia detecções rápidas e libera após o tempo passar
    commands = ["ligar"]
    recognizer = CommandRecognizer(
        available_commands=commands,
        command_similarity_margin=0.7,
        command_cooldown=1000,  # 1000 ms = 1 segundo
    )

    # Usamos o "patch" para controlar o relógio do sistema (time.time)
    with patch("time.time") as mock_time:
        # 1. Simulamos que o tempo atual é 100.0 segundos
        mock_time.return_value = 100.0
        # Primeira tentativa deve funcionar
        assert recognizer.recognize("ligar") == "ligar"

        # 2. Simulamos que se passaram apenas 500ms (tempo vai para 100.5)
        mock_time.return_value = 100.5
        # Deve retornar None porque 500ms é menor que o cooldown de 1000ms
        assert recognizer.recognize("ligar") is None

        # 3. Simulamos que o tempo passou o suficiente (mais 1.5 segundos, tempo vai para 102.0)
        mock_time.return_value = 102.0
        # Agora deve aceitar o comando novamente
        assert recognizer.recognize("ligar") == "ligar"
