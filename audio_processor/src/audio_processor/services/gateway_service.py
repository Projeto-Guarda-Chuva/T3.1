import asyncio
from typing import Any, Callable

import aiohttp
from aiohttp import web
from typing_extensions import override

from audio_processor.services.base_service import BaseService


class GatewayService(BaseService):
    def __init__(
        self,
        host: str,
        port: int,
        target_host: str,
        target_port: int,
    ):
        super().__init__()

        self._host = host
        self._port = port
        self._target_host = target_host
        self._target_port = target_port
        self._noise_callback = None

        self._loop = asyncio.new_event_loop()
        self._runner = None

    @override
    def stop(self) -> None:
        super().stop()

        if self._loop and self._loop.is_running():
            print("[GatewayService] Sinalizando encerramento do event loop...")
            self._loop.call_soon_threadsafe(self._loop.stop)

    def deliver_command(self, payload: Any) -> None:
        """Recebe o payload, encapsula como comando e agenda o POST."""
        if not self.is_running:
            return

        asyncio.run_coroutine_threadsafe(self._post_command(payload), self._loop)

    def set_noise_callback(self, callback: Callable[[], float]):
        self._noise_callback = callback

    @override
    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)

        async def start_server():
            app = web.Application()
            app.router.add_get("/noise", self._handle_get_noise)

            self._runner = web.AppRunner(app)
            await self._runner.setup()

            site = web.TCPSite(self._runner, self._host, self._port)
            await site.start()

            print(
                "[GatewayService] Entrypoint web ouvindo em "
                f"http://{self._host}:{self._port}"
            )

        try:
            self._loop.run_until_complete(start_server())
            self._loop.run_forever()
        finally:
            print("[GatewayService] Encerrando servidor HTTP e limpando recursos...")

            if self._runner:
                self._loop.run_until_complete(self._runner.cleanup())

            self._loop.close()

            print("[GatewayService] Event loop assíncrono encerrado de forma limpa.")

    async def _handle_get_noise(self, request: web.Request) -> web.Response:
        """Lida com as requisições GET retornando o nível de ruído atual."""
        try:
            if self._noise_callback is None:
                raise Exception("No noise callback provided")

            current_noise = self._noise_callback()
            return web.json_response({"noise_level": current_noise})
        except Exception as e:
            print(f"[GatewayService] Erro ao executar o callback de ruído: {e}")
            return web.json_response({"error": "Internal Server Error"}, status=500)

    async def _post_command(self, payload: Any) -> None:
        """Executa a requisição POST com o payload JSON."""
        url = f"http://{self._target_host}:{self._target_port}"

        message = {"type": "command", "payload": payload}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=message) as response:
                    if response.status >= 400:
                        print(
                            f"[GatewayService] Falha no POST. Status code: {response.status}"
                        )
        except TypeError as e:
            print(
                f"[GatewayService] Falha na formatação do Payload (Não serializável): {e}"
            )
        except aiohttp.ClientError as e:
            print(f"[GatewayService] Erro de conexão ao tentar fazer o POST: {e}")
        except Exception as e:
            print(f"[GatewayService] Erro inesperado ao enviar comando: {e}")
