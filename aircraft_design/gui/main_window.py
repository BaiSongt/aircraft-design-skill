from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QSplitter,
)
from PySide6.QtCore import QTimer, Slot, Qt
import datetime
import csv
import queue
from .widgets.convergence_plot import ConvergencePlot
from .widgets.constraint_plot import ConstraintPlot
from .widgets.payload_range_plot import PayloadRangePlot

# from .widgets.geometry_view_3d import GeometryView3D
from .widgets.pyvista_widget import PyVistaWidget
from .widgets.report_gallery import ReportGallery


class MainWindow(QMainWindow):
    def __init__(self, data_queue, command_queue):
        super().__init__()
        self.data_queue = data_queue
        self.command_queue = command_queue

        self.setWindowTitle("Aircraft Design Sizing - Realtime Visualization (PySide6)")
        self.resize(1600, 900)

        # Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        open_action = file_menu.addAction("Open Result Folder")
        open_action.triggered.connect(self.open_result_folder)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Controls Area (Top)
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

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

        # Main Splitter Container
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)

        # --- Left Panel: Dynamic Plots (Vertical Splitter) ---
        left_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(left_splitter)

        # 1. MTOW Iteration
        self.conv_plot = ConvergencePlot()
        self.conv_plot.clicked.connect(self.on_plot_clicked)
        left_splitter.addWidget(self.conv_plot)

        # 2. Constraint Analysis
        self.const_plot = ConstraintPlot()
        self.const_plot.clicked.connect(self.on_plot_clicked)
        left_splitter.addWidget(self.const_plot)

        # 3. Payload-Range
        self.pr_plot = PayloadRangePlot()
        self.pr_plot.clicked.connect(self.on_plot_clicked)
        left_splitter.addWidget(self.pr_plot)

        # --- Center Panel: 3D Model & 3-View (Vertical Splitter) ---
        center_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(center_splitter)

        # 3D View (Top Center)
        self.geo_view = PyVistaWidget(view_mode="iso")
        center_splitter.addWidget(self.geo_view)

        # 3-View (Bottom Center) - Using PyVista for Top/Side views
        views_widget = QWidget()
        views_layout = QHBoxLayout(views_widget)
        views_layout.setContentsMargins(0, 0, 0, 0)

        self.top_view = PyVistaWidget(view_mode="top")
        views_layout.addWidget(self.top_view)

        self.side_view = PyVistaWidget(view_mode="side")
        views_layout.addWidget(self.side_view)

        center_splitter.addWidget(views_widget)

        # Center Splitter Proportions (3D View larger)
        center_splitter.setStretchFactor(0, 3)
        center_splitter.setStretchFactor(1, 1)

        # --- Right Panel: Report Gallery ---
        self.report_gallery = ReportGallery()
        self.main_splitter.addWidget(self.report_gallery)

        # Main Splitter Proportions
        self.main_splitter.setStretchFactor(0, 1)  # Left
        self.main_splitter.setStretchFactor(1, 2)  # Center
        self.main_splitter.setStretchFactor(2, 1)  # Right

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
        self.timer.start(100)  # 100ms
        QTimer.singleShot(0, self.bring_to_front)
        QTimer.singleShot(500, self.bring_to_front)

    def bring_to_front(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.showNormal()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

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
        msg_type = msg.get("type")

        if msg_type == "update":
            if not self.paused:
                self.history.append({"iteration": msg["iteration"], "mtow": msg["mtow"], "error": msg["error"]})
                self.conv_plot.update_data(self.history)
                self.status_label.setText(f"Iteration: {msg['iteration']} | MTOW: {msg['mtow']:.1f} kg")

                if "geometry" in msg:
                    self.geometry = msg["geometry"]
                    # Update all 3 views with linked data
                    self.geo_view.update_mesh(self.geometry)
                    self.top_view.update_mesh(self.geometry)
                    self.side_view.update_mesh(self.geometry)

        elif msg_type == "constraints":
            self.constraints = msg["data"]
            self.design_point = msg["design_point"]
            self.const_plot.update_data(self.constraints, self.design_point)

        elif msg_type == "payload_range":
            ranges = msg["ranges"]
            payloads = msg["payloads"]
            self.pr_plot.update_data(ranges, payloads)

        elif msg_type == "report_generated":
            path = msg["path"]
            self.report_gallery.load_images(path)
            self.status_label.setText(f"Report loaded from {path}")

            # Try to load detailed OBJ if available for linked views
            import os

            obj_path = os.path.join(path, "model.obj")
            if os.path.exists(obj_path):
                self.geo_view.load_file(obj_path)
                self.top_view.load_file(obj_path)
                self.side_view.load_file(obj_path)
                self.status_label.setText(f"Loaded detailed model from {obj_path}")
            else:
                self.status_label.setText("No OBJ model found, keeping parametric view.")

        elif msg_type == "reset":
            self.history = []
            self.conv_plot.update_data([])
            self.pr_plot.update_data([], [])
            self.geo_view.clear()
            self.top_view.clear()
            self.side_view.clear()
            self.status_label.setText("Reset")

    @Slot()
    def open_result_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.report_gallery.load_images(folder)
            # self.tab_widget.setCurrentIndex(1) # Tab removed
            self.status_label.setText(f"Report loaded from {folder}")

    @Slot()
    def toggle_pause(self):
        self.paused = self.btn_pause.isChecked()
        if self.paused:
            self.btn_pause.setText("Resume")
            self.status_label.setText("Paused")
        else:
            self.btn_pause.setText("Pause")
            self.status_label.setText("Resumed")

    @Slot(float, float, object)
    def on_plot_clicked(self, x, y, data):
        sender = self.sender()
        name = "Unknown Plot"
        if sender == self.conv_plot:
            name = "Convergence Plot"
        elif sender == self.const_plot:
            name = "Constraint Plot"
        elif sender == self.pr_plot:
            name = "Payload-Range Plot"

        self.status_label.setText(f"Clicked {name} at ({x:.2f}, {y:.2f})")
        # In a future update, this could highlight specific results in the Report Gallery

    @Slot()
    def save_image(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"viz_snapshot_{timestamp}.png"

        # Save the full window
        screen = self.grab()
        screen.save(filename)
        self.status_label.setText(f"Saved screenshot {filename}")

    @Slot()
    def export_data(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"design_history_{timestamp}.csv"
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Iteration", "MTOW_kg", "Error"])
                for item in self.history:
                    writer.writerow([item["iteration"], item["mtow"], item["error"]])
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
        # Reset 3D cameras
        self.geo_view.reset_camera()
        self.top_view.reset_camera()
        self.side_view.reset_camera()
