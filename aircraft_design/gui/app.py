import sys
from PySide6.QtWidgets import QApplication
from .main_window import MainWindow


def run_pyside_visualization(data_queue, command_queue):
    app = QApplication(sys.argv)
    window = MainWindow(data_queue, command_queue)
    window.show()
    sys.exit(app.exec())
