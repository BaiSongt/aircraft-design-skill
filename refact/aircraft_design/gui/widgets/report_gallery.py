from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QSizePolicy, QLayout
from pathlib import Path
import json
import numpy as np
from aircraft_design.common.atmosphere import isa_tropopause
from .mpl_widget import MplWidget


class ReportImageWidget(MplWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent, with_toolbar=True)
        self.image_key = None
        self.image_title = None
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def load_data(self, key: str, title: str, data: dict):
        try:
            self.image_key = key
            self.image_title = title
            self.axes.clear()
            if key == "aero_cl_alpha":
                alpha_deg = data.get("alpha_deg", [])
                cl = data.get("cl", [])
                cl_max = data.get("cl_max", 0.0)
                alpha_stall = data.get("alpha_stall", 0.0)
                self.axes.plot(alpha_deg, cl, label="Lift Coefficient", color="blue", linewidth=2)
                self.axes.axhline(y=cl_max, color="red", linestyle="--", label=f"CLmax = {cl_max:.2f}")
                self.axes.axvline(
                    x=alpha_stall, color="orange", linestyle=":", label=f"Stall Angle = {alpha_stall:.1f}°"
                )
                self.axes.set_xlabel("Angle of Attack $\\alpha$ (deg)")
                self.axes.set_ylabel("Lift Coefficient $C_L$")
                self.axes.set_title("Lift Coefficient vs Angle of Attack")
                self.axes.grid(True, linestyle="--", alpha=0.7)
                self.axes.legend()
            elif key == "aero_drag_polar":
                cd = data.get("cd", [])
                cl = data.get("cl", [])
                cd0 = data.get("cd0", 0.0)
                k = data.get("k", 0.0)
                self.axes.plot(cd, cl, label="Drag Polar", color="green", linewidth=2)
                if cl:
                    cl_theory = np.linspace(min(cl), max(cl), 100)
                    cd_theory = cd0 + k * cl_theory**2
                    self.axes.plot(cd_theory, cl_theory, "k--", alpha=0.5, label="Theoretical Parabolic")
                self.axes.set_xlabel("Drag Coefficient $C_D$")
                self.axes.set_ylabel("Lift Coefficient $C_L$")
                self.axes.set_title("Drag Polar ($C_L$ vs $C_D$)")
                self.axes.grid(True, linestyle="--", alpha=0.7)
                self.axes.legend()
            elif key == "perf_thrust_curves":
                velocity_ms = data.get("velocity_ms", [])
                thrust_req_n = data.get("thrust_req_n", [])
                thrust_avail_n = data.get("thrust_avail_n", [])
                altitude_m = data.get("altitude_m", 0.0)
                max_v = max(velocity_ms) if velocity_ms else 0.0
                atm = isa_tropopause(altitude_m)
                max_mach = max_v / atm.a_m_s if atm.a_m_s else 0.0
                if max_mach < 0.6:
                    x_vals = np.array(velocity_ms) * 3.6
                    x_label = "Velocity (km/h)"
                else:
                    x_vals = np.array(velocity_ms) / atm.a_m_s
                    x_label = "Mach Number"
                self.axes.plot(x_vals, np.array(thrust_req_n) / 1000, label="Thrust Required", color="red", linewidth=2)
                self.axes.plot(
                    x_vals, np.array(thrust_avail_n) / 1000, label="Thrust Available", color="blue", linewidth=2
                )
                self.axes.set_xlabel(x_label)
                self.axes.set_ylabel("Thrust (kN)")
                self.axes.set_title(f"Thrust Curves at Altitude = {altitude_m} m")
                self.axes.grid(True, linestyle="--", alpha=0.7)
                self.axes.legend()
            elif key == "perf_flight_envelope":
                v_stall_curve = data.get("v_stall_curve", {})
                v_max_curve = data.get("v_max_curve", {})
                ceiling_m = data.get("ceiling_m", 0.0)
                h_stall = np.array(v_stall_curve.get("altitude_m", []))
                v_stall_ms = np.array(v_stall_curve.get("velocity_ms", []))
                h_max = np.array(v_max_curve.get("altitude_m", []))
                v_max_ms = np.array(v_max_curve.get("velocity_ms", []))
                max_mach_global = 0.0
                for v, h in zip(v_max_ms, h_max):
                    if v is None:
                        continue
                    a = isa_tropopause(float(h)).a_m_s
                    m = v / a if a else 0.0
                    if m > max_mach_global:
                        max_mach_global = m
                use_mach = max_mach_global >= 0.6
                if use_mach:
                    v_stall_plot = [v / isa_tropopause(float(h)).a_m_s for v, h in zip(v_stall_ms, h_stall)]
                    v_max_plot = [v / isa_tropopause(float(h)).a_m_s for v, h in zip(v_max_ms, h_max)]
                    x_label = "Mach Number"
                    title = "Flight Envelope (Altitude vs Mach)"
                else:
                    v_stall_plot = (v_stall_ms * 3.6).tolist()
                    v_max_plot = (v_max_ms * 3.6).tolist()
                    x_label = "Velocity (km/h)"
                    title = "Flight Envelope (Altitude vs Velocity)"
                self.axes.plot(v_stall_plot, h_stall, color="orange", linewidth=2, label="Stall Limit")
                self.axes.plot(v_max_plot, h_max, color="blue", linewidth=2, label="Max Speed Limit")
                self.axes.axhline(y=ceiling_m, color="gray", linestyle="--", label=f"Ceiling = {ceiling_m} m")
                self.axes.set_xlabel(x_label)
                self.axes.set_ylabel("Altitude (m)")
                self.axes.set_title(title)
                self.axes.grid(True, linestyle="--", alpha=0.7)
                self.axes.legend()
            elif key == "struct_vn_diagram":
                v_ms = data.get("v_ms", [])
                n_pos = data.get("n_pos", [])
                n_neg = data.get("n_neg", [])
                atm = isa_tropopause(0.0)
                max_v = max(v_ms) if v_ms else 0.0
                max_mach = max_v / atm.a_m_s if atm.a_m_s else 0.0
                if max_mach < 0.6:
                    x_vals = np.array(v_ms) * 3.6
                    x_label = "Velocity (km/h)"
                else:
                    x_vals = np.array(v_ms) / atm.a_m_s
                    x_label = "Mach Number"
                self.axes.plot(x_vals, n_pos, color="black", linewidth=2, label="Positive Limit")
                self.axes.plot(x_vals, n_neg, color="black", linewidth=2, linestyle="--", label="Negative Limit")
                self.axes.set_xlabel(x_label)
                self.axes.set_ylabel("Load Factor (g)")
                self.axes.set_title("V-n Diagram (Maneuver Envelope)")
                self.axes.grid(True, linestyle="--", alpha=0.7)
                self.axes.legend()
            self.draw()
            self.show_content()
        except Exception as e:
            self.show_error(f"Failed to load plot data: {e}")


class ReportGallery(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.scroll.setWidget(self.content_widget)

        self.layout.addWidget(self.scroll)

    def load_images(self, directory: str):
        # Clear existing
        # Note: Removing widgets from layout is tricky in Qt, simpler to delete items
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        path = Path(directory)
        if not path.exists():
            lbl = QLabel(f"Directory not found: {directory}")
            self.content_layout.addWidget(lbl)
            return

        # Define expected images and titles
        # Exclude 3-view images as requested for the Right Panel
        images_map = [
            ("aero_cl_alpha", "Lift Curve (CL-alpha)"),
            ("aero_drag_polar", "Drag Polar"),
            ("perf_thrust_curves", "Thrust Curves"),
            ("perf_flight_envelope", "Flight Envelope"),
            ("struct_vn_diagram", "V-n Diagram"),
        ]

        plot_data = None
        data_path = path / "report_plot_data.json"
        if data_path.exists():
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    plot_data = json.load(f)
            except Exception:
                plot_data = None
        if not plot_data:
            lbl = QLabel("No plot data found in this directory.")
            self.content_layout.addWidget(lbl)
            return

        found_files = []
        for key, title in images_map:
            if key in plot_data:
                found_files.append((key, title))

        if not found_files:
            lbl = QLabel("No report images found in this directory.")
            self.content_layout.addWidget(lbl)
            return

        for item, title in found_files:
            widget = ReportImageWidget()
            widget.load_data(item, title, plot_data.get(item, {}))
            self.content_layout.addWidget(widget)
