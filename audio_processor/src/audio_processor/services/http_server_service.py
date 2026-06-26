
import logging
import threading
from typing import Any
from flask import Flask, jsonify, request
from typing_extensions import override
from werkzeug.serving import make_server
from audio_processor.output_message_type import OutputMessageType
from audio_processor.pcm_buffer import PcmBuffer
from audio_processor.services.base_service import BaseService
from audio_processor.services.gateway_service import GatewayService

logging.getLogger("werkzeug").setLevel(logging.ERROR)


class HttpServerService(BaseService):

    def __init__(
        self,
        host: str,
        port: int,
        gateway: GatewayService,
        pcm_buffer: PcmBuffer,
    ) -> None:
        super().__init__()

        self._host = host
        self._port = port
        self._gateway = gateway
        self._pcm_buffer = pcm_buffer

        self._app = Flask(__name__)
        self._werkzeug_server = None          
        self._server_ready = threading.Event() 

        self._register_routes()


    @override
    def stop(self) -> None:
        """Signal the Werkzeug serve_forever() loop to exit cleanly."""
        super().stop()

        if self._werkzeug_server is not None:
            self._werkzeug_server.shutdown()
            print("[HttpServerService] Shutdown signal sent to Werkzeug.")

    @override
    def _run(self) -> None:

        try:
            self._werkzeug_server = make_server(
                self._host,
                self._port,
                self._app,
                threaded=False,  
            )
            print(
                f"[HttpServerService] Listening on "
                f"http://{self._host}:{self._port}"
            )
            self._server_ready.set()
            self._werkzeug_server.serve_forever()
        except Exception as exc:
            print(f"[HttpServerService] Fatal error: {exc}")
            self._server_ready.set()   
        finally:
            print("[HttpServerService] Server thread exited.")

    def wait_for_ready(self, timeout: float = 5.0) -> bool:
        """
        Optional helper — blocks until the socket is bound and the server
        is accepting connections, or until `timeout` seconds have elapsed.
        Returns True if the server is ready, False on timeout.
        """
        return self._server_ready.wait(timeout)


    def _register_routes(self) -> None:

        app = self._app

        @app.get("/health")
        def health():
            """
            Lightweight liveness probe.
            Useful for Docker health-checks, load balancers, or PM2.
            """
            return jsonify({"status": "ok"}), 200

        @app.get("/status")
        def status():

            return jsonify({
                "gateway": {
                    "host": self._gateway._host,
                    "port": self._gateway._port,
                    "connected_clients": len(self._gateway._clients),
                    "running": self._gateway.is_running,
                },
                "pcm_buffer": {
                    "buffered_bytes": len(self._pcm_buffer._buffer)
                    if hasattr(self._pcm_buffer, "_buffer") else "n/a",
                },
                "http_server": {
                    "host": self._host,
                    "port": self._port,
                },
            }), 200

        @app.post("/command")
        def inject_command():

            body: Any = request.get_json(silent=True)

            if not body or "command" not in body:
                return jsonify({
                    "error": "Request body must be JSON with a 'command' key."
                }), 400

            command_value: str = str(body["command"]).strip()

            if not command_value:
                return jsonify({"error": "'command' must not be empty."}), 400

            self._gateway.deliver(OutputMessageType.COMMAND, command_value)

            return jsonify({
                "delivered": True,
                "command": command_value,
            }), 200

        @app.post("/config/reload")
        def reload_config():

            body: Any = request.get_json(silent=True)

            if not body:
                return jsonify({"error": "Empty or non-JSON body."}), 400

            applied: dict = {}

            if "log_level" in body:
                level = str(body["log_level"]).upper()
                logging.getLogger().setLevel(getattr(logging, level, logging.INFO))
                applied["log_level"] = level

            return jsonify({
                "reloaded": True,
                "applied": applied,
            }), 200
