from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedLayout, QSizePolicy, QApplication
from PySide6.QtCore import Qt, Signal, QSize
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure


class MplWidget(QWidget):
    # Signal emitted when a point/area is clicked: x, y, extra_data
    clicked = Signal(float, float, object)

    def __init__(self, parent=None, width=5, height=4, dpi=100, projection_3d=False, with_toolbar=True):
        super().__init__(parent)

        # Main Layout (Stacked to show Loading/Error overlays)
        self.stack_layout = QStackedLayout()
        self.setLayout(self.stack_layout)

        # --- Layer 1: Plot Canvas ---
        self.plot_container = QWidget()
        plot_layout = QVBoxLayout(self.plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        self.canvas = FigureCanvas(Figure(figsize=(width, height), dpi=dpi))
        # Set size policy to expanding to ensure it fills the splitter
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()

        if with_toolbar:
            self.toolbar = NavigationToolbar2QT(self.canvas, self)
            self.toolbar.setIconSize(QSize(16, 16))
            self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
            self.toolbar.setStyleSheet("QToolBar { spacing: 2px; padding: 2px; } QToolButton { padding: 2px; }")
            self.toolbar.setFixedHeight(28)
            plot_layout.addWidget(self.toolbar)
        else:
            self.toolbar = None

        plot_layout.addWidget(self.canvas)
        self.stack_layout.addWidget(self.plot_container)

        if projection_3d:
            self.axes = self.canvas.figure.add_subplot(111, projection="3d")
        else:
            self.axes = self.canvas.figure.add_subplot(111)
        self._default_facecolor = self.axes.get_facecolor()
        self._highlighted = False

        # Connect click event
        self.canvas.mpl_connect("button_press_event", self.on_click)

        # --- Layer 2: Loading Overlay ---
        self.loading_widget = QLabel("Loading...", self)
        self.loading_widget.setAlignment(Qt.AlignCenter)
        self.loading_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); font-size: 16px; color: #333;")
        self.stack_layout.addWidget(self.loading_widget)

        # --- Layer 3: Error Overlay ---
        self.error_widget = QLabel(self)
        self.error_widget.setAlignment(Qt.AlignCenter)
        self.error_widget.setStyleSheet(
            "background-color: rgba(255, 200, 200, 200); font-size: 14px; color: #d00; padding: 20px;"
        )
        self.error_widget.setWordWrap(True)
        self.stack_layout.addWidget(self.error_widget)

        # Initial State
        self.show_content()

    def on_click(self, event):
        if event.inaxes == self.axes:
            # Emit signal with coordinates
            self.clicked.emit(event.xdata, event.ydata, None)

    def show_content(self):
        """Show the plot canvas."""
        self.stack_layout.setCurrentWidget(self.plot_container)

    def show_loading(self, message="Processing..."):
        """Show loading overlay."""
        self.loading_widget.setText(message)
        self.stack_layout.setCurrentWidget(self.loading_widget)
        # Process events to ensure UI updates immediately
        QApplication.processEvents()

    def show_error(self, message):
        """Show error overlay."""
        self.error_widget.setText(f"Error: {message}")
        self.stack_layout.setCurrentWidget(self.error_widget)

    def draw(self):
        """Thread-safe draw call."""
        try:
            self.canvas.draw_idle()
        except Exception as e:
            self.show_error(str(e))

    def clear(self):
        """Clear axes and refresh."""
        self.axes.clear()
        self.draw()

    def set_highlighted(self, highlighted: bool):
        self._highlighted = highlighted
        if highlighted:
            self.axes.set_facecolor("#fff4d6")
        else:
            self.axes.set_facecolor(self._default_facecolor)
        self.draw()
