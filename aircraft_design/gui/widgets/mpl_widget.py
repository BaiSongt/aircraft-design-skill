import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class MplWidget(QWidget):
    def __init__(self, parent=None, width=5, height=4, dpi=100, projection_3d=False):
        super().__init__(parent)

        self.canvas = FigureCanvas(Figure(figsize=(width, height), dpi=dpi))
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

        if projection_3d:
            self.axes = self.canvas.figure.add_subplot(111, projection='3d')
        else:
            self.axes = self.canvas.figure.add_subplot(111)

    def draw(self):
        self.canvas.draw()
