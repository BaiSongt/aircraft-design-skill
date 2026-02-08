import sys
import socket
import threading
import queue
import pickle
import struct
from PySide6.QtWidgets import QApplication
from .main_window import MainWindow


class VisualizationServer:
    def __init__(self, host="localhost", port=9999):
        self.host = host
        self.port = port
        self.data_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.server_socket = None
        self.running = True

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
                    msg = pickle.loads(data_bytes)

                    # Route message
                    if isinstance(msg, dict):
                        msg_type = msg.get("type")
                        if msg_type in ["save", "export"]:  # Command types
                            self.command_queue.put(msg)
                        else:  # Data types (update, constraints, reset)
                            self.data_queue.put(msg)

                except Exception as e:
                    print(f"Error decoding message: {e}")

        except Exception as e:
            print(f"Client connection error: {e}")
        finally:
            client_socket.close()
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


def run_server_app():
    # Setup Server
    server = VisualizationServer()
    server.start_server()

    # Setup GUI
    app = QApplication(sys.argv)
    window = MainWindow(server.data_queue, server.command_queue)
    window.show()

    exit_code = app.exec()

    # Cleanup
    server.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    run_server_app()
