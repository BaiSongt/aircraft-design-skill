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
        images_map = [
            ("aero_cl_alpha.png", "Lift Curve (CL-alpha)"),
            ("aero_drag_polar.png", "Drag Polar"),
            ("perf_thrust_curves.png", "Thrust Curves"),
            ("perf_flight_envelope.png", "Flight Envelope"),
            ("struct_vn_diagram.png", "V-n Diagram"),
            ("view_top_static.png", "Top View (2D)"),
            ("view_side_static.png", "Side View (2D)"),
            ("vsp_iso.png", "VSP Iso View"), # Sometimes named differently
            ("vsp_top.png", "VSP Top View"),
            ("vsp_side.png", "VSP Side View")
        ]
        
        # Scan for matching files
        found_files = []
        for filename, title in images_map:
            img_path = path / filename
            if img_path.exists():
                found_files.append((img_path, title))
            
        # Also check for other pngs not in the map?
        # Maybe just stick to the map to avoid clutter
        
        if not found_files:
            lbl = QLabel("No report images found in this directory.")
            self.grid.addWidget(lbl, 0, 0)
            return
            
        row = 0
        col = 0
        max_cols = 2
        
        for img_path, title in found_files:
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            vbox = QVBoxLayout(frame)
            
            lbl_title = QLabel(title)
            lbl_title.setAlignment(Qt.AlignCenter)
            font = lbl_title.font()
            font.setBold(True)
            lbl_title.setFont(font)
            vbox.addWidget(lbl_title)
            
            lbl_img = QLabel()
            pixmap = QPixmap(str(img_path))
            if not pixmap.isNull():
                # Scale to reasonable size for gallery
                scaled = pixmap.scaled(700, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl_img.setPixmap(scaled)
                lbl_img.setAlignment(Qt.AlignCenter)
                vbox.addWidget(lbl_img)
                
                self.grid.addWidget(frame, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
