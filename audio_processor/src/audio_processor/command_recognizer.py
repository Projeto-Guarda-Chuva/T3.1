import time

import Levenshtein


class CommandRecognizer:
    def __init__(
        self,
        available_commands: list[str],
        command_similarity_margin: float,
        command_cooldown: int,
    ):
        self._command_similarity_margin = command_similarity_margin
        self._available_commands = available_commands
        self._command_cooldown = command_cooldown
        self._command_last_detection = dict()

    def recognize(self, word: str) -> str | None:
        command = self._get_closest_command(word)

        if command is None:
            return None

        now = time.time()

        if command in self._command_last_detection:
            last_detection = self._command_last_detection[command]
            detection_interval = int((now - last_detection) * 1000)

            if detection_interval < self._command_cooldown:
                return None

        # --- CORREÇÃO AQUI: Salva o momento exato em que o comando foi aceito ---
        self._command_last_detection[command] = now

        return command

    def _get_closest_command(self, word: str) -> str | None:
        best_command = None
        best_similarity = self._command_similarity_margin

        for command in self._available_commands:
            similarity = Levenshtein.ratio(command, word)

            if similarity >= best_similarity:
                best_command = command
                best_similarity = similarity

        return best_command
