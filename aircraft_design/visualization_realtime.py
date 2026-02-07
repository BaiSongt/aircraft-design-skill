import socket
import pickle
import struct
import time
import subprocess
import os
import sys
from typing import Dict, Optional

class RealTimeVisualizer:
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.client_socket = None
        
    def start(self):
        """
        Connect to the visualization server. 
        If connection fails, attempt to start the server in a separate process.
        """
        if not self._connect():
            print("Visualization Server not running. Starting new instance...")
            self._start_server_process()
            # Wait for server to initialize
            for _ in range(20): # Try for 2 seconds
                time.sleep(0.1)
                if self._connect():
                    break
            else:
                print("Failed to connect to Visualization Server.")

    def _connect(self) -> bool:
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to Visualization Server at {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            self.client_socket = None
            return False

    def _start_server_process(self):
        # Start as module to handle imports correctly
        # We assume the CWD is the project root (where run_sizing.py usually runs)
        # If not, we might need to adjust env or cwd
        
        # Get project root (assuming this file is in aircraft_design/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Start as independent process
        # Use Popen with start_new_session to detach (on POSIX)
        cmd = [sys.executable, "-m", "aircraft_design.gui.server"]
        
        if sys.platform != 'win32':
            subprocess.Popen(cmd, cwd=project_root, start_new_session=True)
        else:
            subprocess.Popen(cmd, cwd=project_root, creationflags=subprocess.CREATE_NEW_CONSOLE)

    def _send_message(self, msg: Dict):
        if self.client_socket:
            try:
                data = pickle.dumps(msg)
                length = struct.pack('>I', len(data))
                self.client_socket.sendall(length + data)
            except (BrokenPipeError, ConnectionResetError):
                print("Connection to Visualization Server lost.")
                self.client_socket = None

    def update_iteration(self, iteration: int, mtow: float, error: float, geometry: Optional[Dict] = None):
        msg = {
            'type': 'update',
            'iteration': iteration,
            'mtow': mtow,
            'error': error
        }
        if geometry:
            msg['geometry'] = geometry
        self._send_message(msg)
            
    def update_constraints(self, constraints_data: Dict, design_point: Dict):
        self._send_message({
            'type': 'constraints',
            'data': constraints_data,
            'design_point': design_point
        })
            
    def update_payload_range(self, ranges: list, payloads: list):
        self._send_message({
            'type': 'payload_range',
            'ranges': ranges,
            'payloads': payloads
        })

    def reset(self):
        self._send_message({'type': 'reset'})
            
    def save_screenshot(self, filename: str):
        self._send_message({'type': 'save', 'filename': filename})

    def stop(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
