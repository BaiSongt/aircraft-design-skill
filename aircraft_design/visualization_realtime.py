
import multiprocessing
import queue
import time
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.gridspec as gridspec
import numpy as np

from matplotlib.widgets import Button
import datetime

class VisualizationProcess(multiprocessing.Process):
    """
    Process that runs the matplotlib GUI for real-time visualization.
    """
    def __init__(self, data_queue: multiprocessing.Queue, command_queue: multiprocessing.Queue):
        super().__init__()
        self.data_queue = data_queue
        self.command_queue = command_queue
        self.history = {
            'iteration': [],
            'mtow': [],
            'error': []
        }
        self.constraints = None
        self.design_point = None
        self.paused = False
        self.daemon = True  # Ensure it dies if parent dies
        
    def run(self):
        # Set style
        try:
            plt.style.use('seaborn-v0_8-darkgrid')
        except:
            plt.style.use('ggplot')
            
        self.fig = plt.figure(figsize=(14, 9))
        self.gs = gridspec.GridSpec(2, 2, figure=self.fig, height_ratios=[1, 1.2])
        
        # Adjust layout to make room for buttons at bottom
        plt.subplots_adjust(bottom=0.1)
        
        # 1. Convergence Plot (Top Left)
        self.ax_conv = self.fig.add_subplot(self.gs[0, 0])
        self.ax_err = self.ax_conv.twinx()
        
        self.line_mtow, = self.ax_conv.plot([], [], 'b-o', linewidth=2, label='MTOW')
        self.line_err, = self.ax_err.plot([], [], 'r--', linewidth=1.5, label='Error')
        
        self.ax_conv.set_title('Convergence History', fontsize=12, fontweight='bold')
        self.ax_conv.set_xlabel('Iteration')
        self.ax_conv.set_ylabel('MTOW (kg)', color='b')
        self.ax_err.set_ylabel('Relative Error', color='r')
        self.ax_err.set_yscale('log')
        
        lines = [self.line_mtow, self.line_err]
        labels = [l.get_label() for l in lines]
        self.ax_conv.legend(lines, labels, loc='upper right')
        
        # 2. Constraint Diagram (Top Right)
        self.ax_const = self.fig.add_subplot(self.gs[0, 1])
        self.ax_const.set_title('Constraint Analysis', fontsize=12, fontweight='bold')
        self.ax_const.set_xlabel('Wing Loading (W/S) [Pa]')
        self.ax_const.set_ylabel('Thrust-to-Weight (T/W)')
        self.ax_const.grid(True, linestyle='--', alpha=0.6)
        
        # 3. 3D View / Geometry (Bottom)
        self.ax_geom = self.fig.add_subplot(self.gs[1, :]) # 2D for now, easier to animate than 3D
        self.ax_geom.set_title('Aircraft Geometry (Top View)', fontsize=12, fontweight='bold')
        self.ax_geom.set_aspect('equal')
        self.ax_geom.grid(True)
        self.ax_geom.set_xlabel('X (m)')
        self.ax_geom.set_ylabel('Y (m)')
        
        # --- UI Controls ---
        # Add buttons
        ax_pause = plt.axes([0.7, 0.02, 0.1, 0.05])
        ax_save = plt.axes([0.81, 0.02, 0.1, 0.05])
        
        self.btn_pause = Button(ax_pause, 'Pause/Resume')
        self.btn_pause.on_clicked(self.toggle_pause)
        
        self.btn_save = Button(ax_save, 'Save Image')
        self.btn_save.on_clicked(self.save_image)
        
        # Setup Animation
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=200, blit=False, cache_frame_data=False)
        
        # Connect close event
        self.fig.canvas.mpl_connect('close_event', self.on_close)
        
        plt.show()

    def toggle_pause(self, event):
        self.paused = not self.paused
        if self.paused:
            self.ani.event_source.stop()
            self.ax_conv.set_title('Convergence History (PAUSED)', fontsize=12, fontweight='bold', color='red')
        else:
            self.ani.event_source.start()
            self.ax_conv.set_title('Convergence History', fontsize=12, fontweight='bold', color='black')
        plt.draw()

    def save_image(self, event):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"viz_snapshot_{timestamp}.png"
        self.fig.savefig(filename)
        print(f"Saved snapshot to {filename}")
        
    def on_close(self, event):
        pass

    def update_plot(self, frame):
        # Process commands
        while not self.command_queue.empty():
            try:
                cmd = self.command_queue.get_nowait()
                if cmd.get('type') == 'save':
                    filename = cmd.get('filename')
                    if filename:
                        self.fig.savefig(filename)
                        print(f"Auto-saved snapshot to {filename}")
            except queue.Empty:
                break

        # Process all pending messages
        while not self.data_queue.empty():
            try:
                msg = self.data_queue.get_nowait()
                self.process_message(msg)
            except queue.Empty:
                break
        
        # If no data yet, do nothing
        if not self.history['iteration']:
            return
            
        # Update Convergence Data
        x = self.history['iteration']
        mtow = self.history['mtow']
        error = self.history['error']
        
        self.line_mtow.set_data(x, mtow)
        self.line_err.set_data(x, error)
        
        self.ax_conv.relim()
        self.ax_conv.autoscale_view()
        self.ax_err.relim()
        self.ax_err.autoscale_view()
        
        # Update Geometry if design point exists
        if self.design_point:
             # Just a placeholder for geometry update if needed
             pass

    def process_message(self, msg):
        msg_type = msg.get('type')
        
        if msg_type == 'update':
            self.history['iteration'].append(msg['iteration'])
            self.history['mtow'].append(msg['mtow'])
            self.history['error'].append(msg['error'])
            
            # Update geometry if provided
            if 'geometry' in msg:
                self.plot_geometry(msg['geometry'])
                
        elif msg_type == 'constraints':
            self.constraints = msg['data']
            self.plot_constraints(msg['design_point'])
            
        elif msg_type == 'reset':
            self.history = {'iteration': [], 'mtow': [], 'error': []}
            self.ax_conv.cla()
            self.ax_err.cla()
            # Re-setup
            self.line_mtow, = self.ax_conv.plot([], [], 'b-o', linewidth=2, label='MTOW')
            self.line_err, = self.ax_err.plot([], [], 'r--', linewidth=1.5, label='Error')
            
    def plot_constraints(self, design_point):
        self.ax_const.clear()
        self.ax_const.set_title('Constraint Analysis', fontsize=12, fontweight='bold')
        self.ax_const.set_xlabel('Wing Loading (W/S) [Pa]')
        self.ax_const.set_ylabel('Thrust-to-Weight (T/W)')
        self.ax_const.grid(True, linestyle='--', alpha=0.6)
        
        if not self.constraints:
            return
            
        # Unpack
        ws = np.array(self.constraints.get('ws_range', []))
        
        # Plot lines
        if 'takeoff' in self.constraints:
            self.ax_const.plot(ws, self.constraints['takeoff'], 'g-', label='Takeoff')
        if 'landing' in self.constraints:
            # Vertical line for landing max WS
            ws_max = self.constraints['landing']
            self.ax_const.axvline(x=ws_max, color='orange', linestyle='--', label='Landing')
            # Shade invalid region
            self.ax_const.axvspan(ws_max, max(ws)*1.1, alpha=0.2, color='orange')
            
        if 'turn' in self.constraints:
            self.ax_const.plot(ws, self.constraints['turn'], 'b-', label='Turn')
        if 'climb' in self.constraints:
             self.ax_const.plot(ws, self.constraints['climb'], 'k-', label='Climb')
             
        # Plot Design Point
        if design_point:
            self.ax_const.plot(design_point['ws'], design_point['tw'], 'r*', markersize=15, label='Design Point')
            
        self.ax_const.legend()
        self.ax_const.relim()
        self.ax_const.autoscale_view()

    def plot_geometry(self, geom):
        self.ax_geom.clear()
        self.ax_geom.set_title('Aircraft Geometry (Top View)', fontsize=12, fontweight='bold')
        self.ax_geom.set_aspect('equal')
        self.ax_geom.grid(True)
        
        # Simple Visualization
        # Fuselage
        fus = geom.get('fuselage', {})
        L = fus.get('length_m', 0)
        D = fus.get('diameter_m', 0)
        self.ax_geom.add_patch(plt.Rectangle((0, -D/2), L, D, color='gray', alpha=0.5))
        
        # Wing
        wing = geom.get('wing', {})
        S = wing.get('s_ref_m2', 0)
        AR = wing.get('aspect_ratio', 0)
        if S > 0 and AR > 0:
            b = np.sqrt(S * AR)
            cr = 2 * S / b # Simple rectangular
            x_wing = L * 0.4
            
            # Simple trapezoid would be better but rectangle is fast
            self.ax_geom.add_patch(plt.Rectangle((x_wing, -b/2), cr, b, color='blue', alpha=0.5))
            
        self.ax_geom.relim()
        self.ax_geom.autoscale_view()


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

