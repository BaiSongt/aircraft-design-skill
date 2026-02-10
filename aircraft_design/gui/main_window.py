from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QSplitter,
    QComboBox,
    QDoubleSpinBox,
)
from PySide6.QtCore import QTimer, Slot, Qt, QUrl
from PySide6.QtGui import QGuiApplication
import datetime
import csv
import queue
import time
import importlib
from pathlib import Path
from .widgets.convergence_plot import ConvergencePlot
from .widgets.constraint_plot import ConstraintPlot
from .widgets.payload_range_plot import PayloadRangePlot

from .widgets.report_gallery import ReportGallery
from ..visualization_3d import (
    build_mesh_parts_from_geometry,
    mesh_to_obj,
    parse_obj_to_parts,
    render_three_view_html_from_geometry,
    render_three_view_html_from_parts,
)
from ..geometry_shape import geometry_shape_from_inputs

SKY_PRESETS = {
    "天蓝": "linear-gradient(180deg, #7cc6ff 0%, #cbe9ff 45%, #f6fbff 100%)",
    "日落": "linear-gradient(180deg, #f97316 0%, #fb7185 45%, #fef3c7 100%)",
    "深蓝": "linear-gradient(180deg, #0f172a 0%, #1e3a8a 55%, #0b1220 100%)",
    "浅灰": "linear-gradient(180deg, #e2e8f0 0%, #f8fafc 60%, #ffffff 100%)",
}

RESOURCE_CONFIG = {
    "prefer_local": True,
    "local_base_url": "assets",
    "cdn_base_url": "https://unpkg.com/three@0.147.0",
    "use_unminified": True,
}

# Determine project root for reliable asset loading
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_webengine_view():
    try:
        module = importlib.import_module("PySide6.QtWebEngineWidgets")
        return getattr(module, "QWebEngineView", None)
    except Exception:
        return None


def _load_webengine_settings():
    try:
        module = importlib.import_module("PySide6.QtWebEngineCore")
        return getattr(module, "QWebEngineSettings", None)
    except Exception:
        return None


class Web3DView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_class = _load_webengine_view()
        self._available = self._view_class is not None
        self._last_geometry = None
        self._last_update_ts = 0.0
        self._last_parts = None
        self._min_interval = 0.4
        self._config = {
            "layout": {"columns": [1, 1], "rows": [1, 1]},
            "grid_enabled": True,
            "default_zoom": 1.0,
            "sky": "linear-gradient(180deg, #7cc6ff 0%, #cbe9ff 45%, #f6fbff 100%)",
        }
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if not self._available:
            label = QLabel("Qt WebEngine 未安装，无法显示 Web 3D 视图", self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            self._view = label
            return
        self._view = self._view_class(self)
        settings_class = _load_webengine_settings()
        if settings_class is not None:
            settings = self._view.settings()
            settings.setAttribute(settings_class.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(settings_class.WebAttribute.WebGLEnabled, True)
            settings.setAttribute(settings_class.WebAttribute.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(settings_class.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self._view)

    def is_available(self):
        return self._available

    def set_html(self, html: str):
        if not self._available:
            if isinstance(self._view, QLabel):
                self._view.setText("Qt WebEngine 未安装，无法显示 Web 3D 视图")
            return
        base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
        self._view.setHtml(html, base_url)

    def update_geometry(self, geometry: dict):
        if not geometry:
            return
        self._last_geometry = geometry
        self._last_parts = None
        if not self._available:
            return
        now = time.monotonic()
        if now - self._last_update_ts < self._min_interval:
            return
        self._last_update_ts = now
        html = render_three_view_html_from_geometry(geometry, resource_config=RESOURCE_CONFIG, web_config=self._config)
        base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
        self._view.setHtml(html, base_url)

    def update_parts(self, parts: list):
        if not parts:
            return
        self._last_geometry = None
        self._last_parts = parts
        if not self._available:
            return
        html = render_three_view_html_from_parts(parts, resource_config=RESOURCE_CONFIG, web_config=self._config)
        base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
        self._view.setHtml(html, base_url)

    def reset_view(self):
        if not self._available:
            return
        if self._last_parts:
            html = render_three_view_html_from_parts(
                self._last_parts, resource_config=RESOURCE_CONFIG, web_config=self._config
            )
            base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
            self._view.setHtml(html, base_url)
        elif self._last_geometry:
            html = render_three_view_html_from_geometry(
                self._last_geometry, resource_config=RESOURCE_CONFIG, web_config=self._config
            )
            base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
            self._view.setHtml(html, base_url)

    def update_config(self, config: dict):
        if not isinstance(config, dict):
            return
        self._config.update(config)
        if self._last_parts:
            html = render_three_view_html_from_parts(
                self._last_parts, resource_config=RESOURCE_CONFIG, web_config=self._config
            )
            base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
            self._view.setHtml(html, base_url)
        elif self._last_geometry:
            html = render_three_view_html_from_geometry(
                self._last_geometry, resource_config=RESOURCE_CONFIG, web_config=self._config
            )
            base_url = QUrl.fromLocalFile(str(PROJECT_ROOT) + "/")
            self._view.setHtml(html, base_url)


class MainWindow(QMainWindow):
    def __init__(self, data_queue, command_queue):
        super().__init__()
        self.data_queue = data_queue
        self.command_queue = command_queue
        self._loaded_obj_parts = None
        self._last_obj_dir = ""

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

        self.btn_demo = QPushButton("加载示例模型")
        self.btn_demo.clicked.connect(self.load_demo_geometry)
        controls_layout.addWidget(self.btn_demo)

        self.btn_import_obj = QPushButton("导入OBJ")
        self.btn_import_obj.clicked.connect(self.import_obj_model)
        controls_layout.addWidget(self.btn_import_obj)

        self.btn_export_obj = QPushButton("导出OBJ")
        self.btn_export_obj.clicked.connect(self.export_obj_model)
        controls_layout.addWidget(self.btn_export_obj)

        self.label_layout = QLabel("布局")
        controls_layout.addWidget(self.label_layout)
        self.web_layout = QComboBox()
        self.web_layout.addItems(["2x2 均分", "Top置顶", "Side置顶", "Front置顶", "Iso置顶"])
        self.web_layout.currentIndexChanged.connect(self.on_web_layout_changed)
        controls_layout.addWidget(self.web_layout)

        self.label_zoom = QLabel("缩放")
        controls_layout.addWidget(self.label_zoom)
        self.web_zoom = QDoubleSpinBox()
        self.web_zoom.setRange(0.2, 5.0)
        self.web_zoom.setSingleStep(0.1)
        self.web_zoom.setDecimals(2)
        self.web_zoom.setValue(1.0)
        self.web_zoom.valueChanged.connect(self.on_web_zoom_changed)
        controls_layout.addWidget(self.web_zoom)

        self.label_sky = QLabel("天空")
        controls_layout.addWidget(self.label_sky)
        self.web_sky = QComboBox()
        self.web_sky.addItems(["天蓝", "日落", "深蓝", "浅灰"])
        self.web_sky.currentIndexChanged.connect(self.on_web_sky_changed)
        controls_layout.addWidget(self.web_sky)

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

        self.web_view = Web3DView()
        self.main_splitter.addWidget(self.web_view)

        # --- Right Panel: Report Gallery ---
        self.report_gallery = ReportGallery()
        self.main_splitter.addWidget(self.report_gallery)

        # Main Splitter Proportions
        self.main_splitter.setStretchFactor(0, 1)  # Left
        self.main_splitter.setStretchFactor(1, 2)  # Center
        self.main_splitter.setStretchFactor(2, 1)  # Right
        QTimer.singleShot(0, self.apply_default_splitter_sizes)

        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        if not self.web_view.is_available():
            self.status_label.setText("Qt WebEngine 未安装，Web 3D 视图不可用")

        # Data State
        self.history = []
        self.constraints = {}
        self.design_point = {}
        self.geometry_data = {}
        self.web_config = {
            "layout": {"type": "2x2"},
            "grid_enabled": True,
            "default_zoom": 1.0,
            "sky": SKY_PRESETS["天蓝"],
        }
        self.paused = False
        self.apply_web_config()
        self.load_demo_geometry()

        # Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(100)  # 100ms
        QTimer.singleShot(0, self.bring_to_front)
        QTimer.singleShot(500, self.bring_to_front)
        QTimer.singleShot(600, self.apply_default_splitter_sizes)

    def bring_to_front(self):
        screen = QGuiApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            frame = self.frameGeometry()
            if frame.width() > available.width() or frame.height() > available.height():
                self.resize(
                    min(self.width(), max(800, int(available.width() * 0.8))),
                    min(self.height(), max(600, int(available.height() * 0.8))),
                )
                frame = self.frameGeometry()
            frame.moveCenter(available.center())
            self.move(frame.topLeft())
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.showNormal()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

    def apply_default_splitter_sizes(self):
        total = max(900, self.width())
        left = min(350, int(total * 0.25))
        # Collapse right panel by default to give maximum space to 3D view
        right = 0
        center = max(420, total - left - right)
        self.main_splitter.setSizes([left, center, right])

    def apply_web_config(self):
        self.web_view.update_config(self.web_config)

    def on_web_layout_changed(self, index: int):
        mapping = {
            0: "2x2",
            1: "top_first",
            2: "side_first",
            3: "front_first",
            4: "iso_first",
        }
        layout_type = mapping.get(index, "2x2")
        self.web_config["layout"] = {"type": layout_type}
        self.apply_web_config()

    def on_web_zoom_changed(self, value: float):
        self.web_config["default_zoom"] = float(value)
        self.apply_web_config()

    def on_web_sky_changed(self, index: int):
        name = self.web_sky.currentText()
        self.web_config["sky"] = SKY_PRESETS.get(name, SKY_PRESETS["天蓝"])
        self.apply_web_config()

    def build_demo_geometry(self) -> dict | None:
        inputs = {
            "project_name": "GUI Demo Geometry",
            "geometry_shape": {
                "layout": {"views": ["top", "side", "front", "iso"]},
                "fuselage": {
                    "axis": {"length_m": 12.0},
                    "profile": {
                        "mode": "parametric",
                        "max_radius_m": 1.2,
                        "nose_fineness_ratio": 1.8,
                        "tail_fineness_ratio": 3.0,
                        "nose_shape": "ellipsoid",
                        "tail_shape": "conical",
                    },
                    "modifiers": {
                        "canopy": {"x_rel": 0.18, "length_rel": 0.15, "height_m": 0.35},
                        "wing_fairing": {"radius_m": 0.2},
                    },
                },
                "wing": {
                    "planform": {
                        "s_ref_m2": 24.0,
                        "aspect_ratio": 6.0,
                        "taper_ratio": 0.5,
                        "sweep_quarter_chord_deg": 15.0,
                        "x_offset_m": 4.5,
                        "dihedral_deg": 3.0,
                    },
                    "sections": {
                        "root_airfoil": {"type": "naca4", "code": "2412"},
                        "tip_airfoil": {"type": "naca4", "code": "0010"},
                    },
                },
                "tail": {
                    "layout": {"type": "conventional"},
                    "horizontal": {
                        "planform": {
                            "s_ref_m2": 5.0,
                            "aspect_ratio": 4.0,
                            "taper_ratio": 0.6,
                            "sweep_quarter_chord_deg": 10.0,
                        }
                    },
                    "vertical": {
                        "planform": {
                            "s_ref_m2": 3.0,
                            "aspect_ratio": 1.5,
                            "taper_ratio": 0.6,
                            "sweep_quarter_chord_deg": 20.0,
                        }
                    },
                },
            },
        }
        return geometry_shape_from_inputs(inputs)

    def load_demo_geometry(self):
        if self.geometry_data:
            return
        demo = self.build_demo_geometry()
        if not demo:
            return
        self.geometry_data = demo
        self._loaded_obj_parts = None
        self.web_view.update_geometry(self.geometry_data)

    def import_obj_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入 OBJ 模型", self._last_obj_dir, "OBJ Files (*.obj)")
        if not path:
            return
        parts = parse_obj_to_parts(path)
        if not parts:
            self.status_label.setText("OBJ 文件解析失败")
            return
        self._loaded_obj_parts = parts
        self._last_obj_dir = str(Path(path).parent)
        self.web_view.update_parts(parts)
        self.status_label.setText(f"已加载 OBJ: {path}")

    def export_obj_model(self):
        parts = self._loaded_obj_parts
        if not parts and self.geometry_data:
            parts = build_mesh_parts_from_geometry(self.geometry_data)
        if not parts:
            self.status_label.setText("当前无可导出的模型")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 OBJ 模型", self._last_obj_dir, "OBJ Files (*.obj)")
        if not path:
            return
        if not path.lower().endswith(".obj"):
            path = f"{path}.obj"
        obj_text = mesh_to_obj(parts)
        with open(path, "w", encoding="utf-8") as f:
            f.write(obj_text)
        self._last_obj_dir = str(Path(path).parent)
        self.status_label.setText(f"已导出 OBJ: {path}")

    @Slot()
    def check_queue(self):
        # Process commands (if any directed to GUI, though mostly GUI sends commands)
        # Process Data
        while not self.data_queue.empty():
            try:
                msg = self.data_queue.get_nowait()
                try:
                    self.process_message(msg)
                except Exception as e:
                    self.status_label.setText(f"UI Error: {e}")
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
                    self.geometry_data = msg["geometry"]
                    self._loaded_obj_parts = None
                    self.web_view.update_geometry(self.geometry_data)

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

            import os

            obj_path = os.path.join(path, "model.obj")
            if os.path.exists(obj_path):
                self.status_label.setText(f"Loaded detailed model from {obj_path}")
            else:
                self.status_label.setText("No OBJ model found, keeping parametric view.")
            if self.geometry_data:
                self.web_view.update_geometry(self.geometry_data)

        elif msg_type == "reset":
            self.history = []
            self.conv_plot.update_data([])
            self.pr_plot.update_data([], [])
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
        self.web_view.reset_view()
