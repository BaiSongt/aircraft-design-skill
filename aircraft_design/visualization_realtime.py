import multiprocessing
import queue
from typing import Dict, Optional
from aircraft_design.gui.app import run_pyside_visualization

class VisualizationProcess(multiprocessing.Process):
    """
    Process that runs the PySide6 GUI for real-time visualization.
    """
    def __init__(self, data_queue: multiprocessing.Queue, command_queue: multiprocessing.Queue):
        super().__init__()
        self.data_queue = data_queue
        self.command_queue = command_queue
        self.daemon = True  # Ensure it dies if parent dies
        
    def run(self):
        run_pyside_visualization(self.data_queue, self.command_queue)

class RealTimeVisualizer:
    def __init__(self):
        self.data_queue = multiprocessing.Queue()
        self.command_queue = multiprocessing.Queue()
        self.process = None
        
    def start(self):
        if self.process is None or not self.process.is_alive():
            self.process = VisualizationProcess(self.data_queue, self.command_queue)
            self.process.start()
            
    def update_iteration(self, iteration: int, mtow: float, error: float, geometry: Optional[Dict] = None):
        if self.process and self.process.is_alive():
            msg = {
                'type': 'update',
                'iteration': iteration,
                'mtow': mtow,
                'error': error
            }
            if geometry:
                msg['geometry'] = geometry
            self.data_queue.put(msg)
            
    def update_constraints(self, constraints_data: Dict, design_point: Dict):
        if self.process and self.process.is_alive():
            self.data_queue.put({
                'type': 'constraints',
                'data': constraints_data,
                'design_point': design_point
            })
            
    def reset(self):
        if self.process and self.process.is_alive():
            self.data_queue.put({'type': 'reset'})
            
    def save_screenshot(self, filename: str):
        if self.process and self.process.is_alive():
            self.command_queue.put({'type': 'save', 'filename': filename})

    def stop(self):
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join()
