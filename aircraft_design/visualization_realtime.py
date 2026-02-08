import socket
import json
import struct
from typing import Dict, Optional


class RealTimeVisualizer:
    def __init__(self, host="localhost", port=9999):
        self.host = host
        self.port = port
        self.client_socket = None

    def start(self, *, require_server: bool = True) -> bool:
        if self._connect():
            return True
        if require_server:
            print("Visualization Server not running. Start it first: python -m aircraft_design.gui.server")
            return False
        return False

    def _connect(self) -> bool:
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to Visualization Server at {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            self.client_socket = None
            return False

    def _send_message(self, msg: Dict):
        if self.client_socket:
            try:
                payload = dict(msg)
                payload.setdefault("__protocol__", "json")
                payload.setdefault("__version__", 1)
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                length = struct.pack(">I", len(data))
                self.client_socket.sendall(length + data)
            except (BrokenPipeError, ConnectionResetError):
                print("Connection to Visualization Server lost.")
                self.client_socket = None

    def update_iteration(self, iteration: int, mtow: float, error: float, geometry: Optional[Dict] = None):
        msg = {"type": "update", "iteration": iteration, "mtow": mtow, "error": error}
        if geometry:
            msg["geometry"] = geometry
        self._send_message(msg)

    def update_constraints(self, constraints_data: Dict, design_point: Dict):
        self._send_message({"type": "constraints", "data": constraints_data, "design_point": design_point})

    def update_payload_range(self, ranges: list, payloads: list):
        self._send_message({"type": "payload_range", "ranges": ranges, "payloads": payloads})

    def reset(self):
        self._send_message({"type": "reset"})

    def save_screenshot(self, filename: str):
        self._send_message({"type": "save", "filename": filename})

    def stop(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except Exception:
                pass
            self.client_socket = None
