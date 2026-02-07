from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTabWidget, QPushButton, QLabel, QFileDialog, QStatusBar)
from PySide6.QtCore import QTimer, Slot, Qt
import datetime
import csv
import queue
from .widgets.convergence_plot import ConvergencePlot
from .widgets.constraint_plot import ConstraintPlot
from .widgets.geometry_view_3d import GeometryView3D

class MainWindow(QMainWindow):
    def __init__(self, data_queue, command_queue):
        super().__init__()
        self.data_queue = data_queue
        self.command_queue = command_queue
        
        self.setWindowTitle("Aircraft Design Sizing - Realtime Visualization (PySide6)")
        self.resize(1200, 800)
        
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 1. Convergence Tab
        self.conv_plot = ConvergencePlot()
        self.tabs.addTab(self.conv_plot, "Convergence History")
        
        # 2. Constraints Tab
        self.const_plot = ConstraintPlot()
        self.tabs.addTab(self.const_plot, "Constraint Analysis")
        
        # 3. 3D View Tab
        self.geo_view = GeometryView3D()
        self.tabs.addTab(self.geo_view, "3D Geometry")
        
        # Controls Area
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)
        
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setCheckable(True)
        self.btn_pause.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.btn_pause)
        
        self.btn_save = QPushButton("Save Image")
        self.btn_save.clicked.connect(self.save_image)
        controls_layout.addWidget(self.btn_save)
        
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.clicked.connect(self.export_data)
        controls_layout.addWidget(self.btn_export)
        
        self.btn_reset = QPushButton("Reset View")
        self.btn_reset.clicked.connect(self.reset_view)
        controls_layout.addWidget(self.btn_reset)
        
        controls_layout.addStretch()
        
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Data State
        self.history = []
        self.constraints = {}
        self.design_point = {}
        self.geometry = {}
        self.paused = False
        
        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100) # 100ms
        
    @Slot()
    def check_queue(self):
        # Process commands (if any directed to GUI, though mostly GUI sends commands)
        # Process Data
        while not self.data_queue.empty():
            try:
                msg = self.data_queue.get_nowait()
                self.process_message(msg)
            except queue.Empty:
                break
                
    def process_message(self, msg):
        msg_type = msg.get('type')
        
        if msg_type == 'update':
            if not self.paused:
                self.history.append({
                    'iteration': msg['iteration'],
                    'mtow': msg['mtow'],
                    'error': msg['error']
                })
                self.conv_plot.update_data(self.history)
                self.status_label.setText(f"Iteration: {msg['iteration']} | MTOW: {msg['mtow']:.1f} kg")
                
                if 'geometry' in msg:
                    self.geometry = msg['geometry']
                    self.geo_view.update_data(self.geometry)
                    
        elif msg_type == 'constraints':
            self.constraints = msg['data']
            self.design_point = msg['design_point']
            self.const_plot.update_data(self.constraints, self.design_point)
            
        elif msg_type == 'reset':
            self.history = []
            self.conv_plot.update_data([])
            self.status_label.setText("Reset")

    @Slot()
    def toggle_pause(self):
        self.paused = self.btn_pause.isChecked()
        if self.paused:
            self.btn_pause.setText("Resume")
            self.status_label.setText("Paused")
        else:
            self.btn_pause.setText("Pause")
            self.status_label.setText("Resumed")

    @Slot()
    def save_image(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"viz_snapshot_{timestamp}.png"
        
        # Save the current tab widget
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'canvas'):
            current_widget.canvas.figure.savefig(filename)
            self.status_label.setText(f"Saved {filename}")
        else:
            # Fallback grab
            screen = current_widget.grab()
            screen.save(filename)
            self.status_label.setText(f"Saved screenshot {filename}")

    @Slot()
    def export_data(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"design_history_{timestamp}.csv"
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Iteration', 'MTOW_kg', 'Error'])
                for item in self.history:
                    writer.writerow([item['iteration'], item['mtow'], item['error']])
            self.status_label.setText(f"Exported {filename}")
        except Exception as e:
            self.status_label.setText(f"Export Error: {str(e)}")

    @Slot()
    def reset_view(self):
        # Reset plot limits
        self.conv_plot.axes.autoscale()
        self.conv_plot.draw()
        self.const_plot.axes.autoscale()
        self.const_plot.draw()
        self.geo_view.axes.autoscale()
        self.geo_view.draw()
