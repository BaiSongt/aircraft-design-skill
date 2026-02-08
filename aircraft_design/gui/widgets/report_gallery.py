from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QGridLayout, QFrame
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from pathlib import Path


class ReportGallery(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.grid = QGridLayout(self.content_widget)
        self.scroll.setWidget(self.content_widget)

        self.layout.addWidget(self.scroll)

    def load_images(self, directory: str):
        # Clear existing
        # Note: Removing widgets from layout is tricky in Qt, simpler to delete items
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        path = Path(directory)
        if not path.exists():
            lbl = QLabel(f"Directory not found: {directory}")
            self.grid.addWidget(lbl, 0, 0)
            return

        # Define expected images and titles
        # Exclude 3-view images as requested for the Right Panel
        images_map = [
            ("aero_cl_alpha.png", "Lift Curve (CL-alpha)"),
            ("aero_drag_polar.png", "Drag Polar"),
            ("perf_thrust_curves.png", "Thrust Curves"),
            ("perf_flight_envelope.png", "Flight Envelope"),
            ("struct_vn_diagram.png", "V-n Diagram"),
        ]

        # Scan for matching files
        found_files = []
        for filename, title in images_map:
            img_path = path / filename
            if img_path.exists():
                found_files.append((img_path, title))

        if not found_files:
            lbl = QLabel("No report images found in this directory.")
            self.grid.addWidget(lbl, 0, 0)
            return

        row = 0
        col = 0
        max_cols = 1  # Single column for side panel

        for img_path, title in found_files:
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            vbox = QVBoxLayout(frame)

            lbl_title = QLabel(title)
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = lbl_title.font()
            font.setBold(True)
            lbl_title.setFont(font)
            vbox.addWidget(lbl_title)

            lbl_img = QLabel()
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                # Scale to reasonable size for gallery - fit width
                # We can't easily get width here, use fixed reasonable width or use scaledcontents
                scaled = pixmap.scaled(
                    400,
                    300,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                lbl_img.setPixmap(scaled)
                lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
                vbox.addWidget(lbl_img)

                self.grid.addWidget(frame, row, col)

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
