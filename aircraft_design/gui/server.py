import sys
import socket
import threading
import queue
import pickle
import json
import struct
import argparse
import time
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from .main_window import MainWindow


class VisualizationServer:
    def __init__(self, host="localhost", port=9999):
        self.host = host
        self.port = port
        self.data_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.server_socket = None
        self.running = True
        self.subscribers = set()
        self.subscribers_lock = threading.Lock()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow address reuse
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"Visualization Server listening on {self.host}:{self.port}")

            # Start accept thread
            accept_thread = threading.Thread(target=self.accept_clients, daemon=True)
            accept_thread.start()

        except OSError as e:
            print(f"Failed to bind port {self.port}: {e}")
            sys.exit(1)

    def accept_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"Client connected from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True)
                client_thread.start()
            except OSError:
                break

    def handle_client(self, client_socket):
        try:
            while self.running:
                # Read message length (4 bytes big-endian)
                length_bytes = self.recv_all(client_socket, 4)
                if not length_bytes:
                    break

                length = struct.unpack(">I", length_bytes)[0]

                # Read message body
                data_bytes = self.recv_all(client_socket, length)
                if not data_bytes:
                    break

                try:
                    msg = self.decode_message(data_bytes)

                    # Route message
                    if isinstance(msg, dict):
                        msg_type = msg.get("type")
                        if msg_type == "__subscribe__":
                            with self.subscribers_lock:
                                self.subscribers.add(client_socket)
                            continue
                        if msg_type in ["save", "export"]:  # Command types
                            self.command_queue.put(msg)
                        else:  # Data types (update, constraints, reset)
                            self.data_queue.put(msg)
                            self.broadcast(msg)

                except Exception as e:
                    print(f"Error decoding message: {e}")

        except Exception as e:
            print(f"Client connection error: {e}")
        finally:
            client_socket.close()
            with self.subscribers_lock:
                self.subscribers.discard(client_socket)
            print("Client disconnected")

    def recv_all(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def broadcast(self, msg):
        payload = self.encode_message(msg)
        length_prefix = struct.pack(">I", len(payload))
        stale = []
        with self.subscribers_lock:
            for sock in self.subscribers:
                try:
                    sock.sendall(length_prefix + payload)
                except Exception:
                    stale.append(sock)
            for sock in stale:
                self.subscribers.discard(sock)

    def encode_message(self, msg):
        if isinstance(msg, dict):
            payload = dict(msg)
        else:
            payload = {"data": msg}
        payload.setdefault("__protocol__", "json")
        payload.setdefault("__version__", 1)
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def decode_message(self, data_bytes):
        try:
            text = data_bytes.decode("utf-8")
            msg = json.loads(text)
            if isinstance(msg, dict):
                return msg
        except Exception:
            pass
        try:
            msg = pickle.loads(data_bytes)
            if isinstance(msg, dict):
                return msg
        except Exception:
            pass
        return None


class VisualizationClient:
    def __init__(self, host="localhost", port=9999):
        self.host = host
        self.port = port
        self.sock = None
        self.running = True

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        subscribe_msg = {"type": "__subscribe__"}
        payload = self.encode_message(subscribe_msg)
        length_prefix = struct.pack(">I", len(payload))
        self.sock.sendall(length_prefix + payload)

    def recv_all(self, n):
        data = bytearray()
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def listen(self, data_queue):
        try:
            while self.running:
                length_bytes = self.recv_all(4)
                if not length_bytes:
                    break
                length = struct.unpack(">I", length_bytes)[0]
                data_bytes = self.recv_all(length)
                if not data_bytes:
                    break
                msg = self.decode_message(data_bytes)
                if isinstance(msg, dict):
                    data_queue.put(msg)
        except Exception as e:
            print(f"Client connection error: {e}")
        finally:
            self.close()

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()

    def encode_message(self, msg):
        if isinstance(msg, dict):
            payload = dict(msg)
        else:
            payload = {"data": msg}
        payload.setdefault("__protocol__", "json")
        payload.setdefault("__version__", 1)
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def decode_message(self, data_bytes):
        try:
            text = data_bytes.decode("utf-8")
            msg = json.loads(text)
            if isinstance(msg, dict):
                return msg
        except Exception:
            pass
        try:
            msg = pickle.loads(data_bytes)
            if isinstance(msg, dict):
                return msg
        except Exception:
            pass
        return None


def run_server_app(host="localhost", port=9999, start_server=True, start_gui=True):
    server = None
    if start_server:
        server = VisualizationServer(host=host, port=port)
        server.start_server()

    data_queue = server.data_queue if server else queue.Queue()
    command_queue = server.command_queue if server else queue.Queue()

    client = None
    client_thread = None

    if start_gui:
        app = QApplication(sys.argv)
        window = MainWindow(data_queue, command_queue)
        window.show()
        if not start_server:
            client = VisualizationClient(host=host, port=port)
            last_notice = 0.0

            def attempt_connect():
                nonlocal client_thread, last_notice
                try:
                    client.connect()
                except Exception:
                    now = time.time()
                    if now - last_notice > 10.0:
                        msg = QMessageBox(window)
                        msg.setIcon(QMessageBox.Warning)
                        msg.setWindowTitle("连接失败")
                        msg.setText("可视化服务未启动，将在 5 秒后自动重试。")
                        msg.show()
                        QTimer.singleShot(3000, msg.close)
                        last_notice = now
                    QTimer.singleShot(5000, attempt_connect)
                    return
                client_thread = threading.Thread(target=client.listen, args=(data_queue,), daemon=True)
                client_thread.start()

            QTimer.singleShot(0, attempt_connect)

        exit_code = app.exec()
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            exit_code = 0

    if client:
        client.close()
    if server:
        server.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Visualization Server and GUI")
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--server-only", action="store_true")
    parser.add_argument("--gui-only", action="store_true")
    args = parser.parse_args()

    start_server = not args.gui_only
    start_gui = not args.server_only

    run_server_app(host=args.host, port=args.port, start_server=start_server, start_gui=start_gui)
