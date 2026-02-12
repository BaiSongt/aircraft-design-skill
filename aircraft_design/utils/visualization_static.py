import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from ..common.atmosphere import isa_tropopause


class StaticPlotter:
    def __init__(self, output_dir: str = "output/plots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Set style for professional publication quality
        plt.style.use("seaborn-v0_8-paper" if "seaborn-v0_8-paper" in plt.style.available else "default")
        plt.rcParams.update(
            {
                "font.family": "sans-serif",
                "font.size": 10,
                "axes.labelsize": 11,
                "axes.titlesize": 12,
                "xtick.labelsize": 9,
                "ytick.labelsize": 9,
                "legend.fontsize": 9,
                "figure.figsize": (6, 4),
                "figure.dpi": 300,
            }
        )

    def plot_lift_curve(self, alpha_deg: List[float], cl: List[float], cl_max: float, alpha_stall: float) -> str:
        """Generates CL-alpha curve."""
        fig, ax = plt.subplots()
        ax.plot(alpha_deg, cl, label="Lift Coefficient", color="blue", linewidth=2)
        ax.axhline(y=cl_max, color="red", linestyle="--", label=f"CLmax = {cl_max:.2f}")
        ax.axvline(x=alpha_stall, color="orange", linestyle=":", label=f"Stall Angle = {alpha_stall:.1f}°")

        ax.set_xlabel("Angle of Attack $\\alpha$ (deg)")
        ax.set_ylabel("Lift Coefficient $C_L$")
        ax.set_title("Lift Coefficient vs Angle of Attack")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        filename = "aero_cl_alpha.png"
        path = self.output_dir / filename
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_drag_polar(self, cd: List[float], cl: List[float], cd0: float, k: float) -> str:
        """Generates Drag Polar."""
        fig, ax = plt.subplots()
        ax.plot(cd, cl, label="Drag Polar", color="green", linewidth=2)

        # Theoretical polar
        cl_theory = np.linspace(min(cl), max(cl), 100)
        cd_theory = cd0 + k * cl_theory**2
        ax.plot(cd_theory, cl_theory, "k--", alpha=0.5, label="Theoretical Parabolic")

        ax.set_xlabel("Drag Coefficient $C_D$")
        ax.set_ylabel("Lift Coefficient $C_L$")
        ax.set_title("Drag Polar ($C_L$ vs $C_D$)")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        filename = "aero_drag_polar.png"
        path = self.output_dir / filename
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_thrust_curves(
        self, velocity_ms: List[float], thrust_req_n: List[float], thrust_avail_n: List[float], altitude_m: float
    ) -> str:
        """Generates Thrust Required vs Available."""
        fig, ax = plt.subplots()

        # Determine Unit based on Max Speed
        max_v = max(velocity_ms) if velocity_ms else 0
        atm = isa_tropopause(altitude_m)
        max_mach = max_v / atm.a_m_s

        if max_mach < 0.6:
            x_vals = np.array(velocity_ms) * 3.6
            x_label = "Velocity (km/h)"
        else:
            x_vals = np.array(velocity_ms) / atm.a_m_s
            x_label = "Mach Number"

        ax.plot(x_vals, np.array(thrust_req_n) / 1000, label="Thrust Required", color="red", linewidth=2)
        ax.plot(x_vals, np.array(thrust_avail_n) / 1000, label="Thrust Available", color="blue", linewidth=2)

        ax.set_xlabel(x_label)
        ax.set_ylabel("Thrust (kN)")
        ax.set_title(f"Thrust Curves at Altitude = {altitude_m} m")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        filename = "perf_thrust_curves.png"
        path = self.output_dir / filename
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_flight_envelope(self, v_stall_curve: dict, v_max_curve: dict, ceiling_m: float) -> str:
        """Generates Flight Envelope (H-V diagram)."""
        fig, ax = plt.subplots()

        # Helper arrays
        h_stall = np.array(v_stall_curve["altitude_m"])
        v_stall_ms = np.array(v_stall_curve["velocity_ms"])

        h_max = np.array(v_max_curve["altitude_m"])
        v_max_ms = np.array(v_max_curve["velocity_ms"])

        # Check max mach in v_max curve (right boundary)
        max_mach_global = 0.0
        for v, h in zip(v_max_ms, h_max):
            if v is None:
                continue
            a = isa_tropopause(h).a_m_s
            m = v / a
            if m > max_mach_global:
                max_mach_global = m

        use_mach = max_mach_global >= 0.6

        if use_mach:
            # Convert to Mach
            v_stall_plot = []
            for v, h in zip(v_stall_ms, h_stall):
                v_stall_plot.append(v / isa_tropopause(h).a_m_s)

            v_max_plot = []
            for v, h in zip(v_max_ms, h_max):
                v_max_plot.append(v / isa_tropopause(h).a_m_s)

            x_label = "Mach Number"
            title = "Flight Envelope (Altitude vs Mach)"
        else:
            v_stall_plot = (v_stall_ms * 3.6).tolist()
            v_max_plot = (v_max_ms * 3.6).tolist()
            x_label = "Velocity (km/h)"
            title = "Flight Envelope (Altitude vs Velocity)"

        ax.plot(v_stall_plot, h_stall, color="orange", linewidth=2, label="Stall Limit")
        ax.plot(v_max_plot, h_max, color="blue", linewidth=2, label="Max Speed Limit")

        # Ceiling
        ax.axhline(y=ceiling_m, color="gray", linestyle="--", label=f"Ceiling = {ceiling_m} m")

        ax.set_xlabel(x_label)
        ax.set_ylabel("Altitude (m)")
        ax.set_title(title)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        filename = "perf_flight_envelope.png"
        path = self.output_dir / filename
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_vn_diagram(self, v_ms: List[float], n_pos: List[float], n_neg: List[float]) -> str:
        """Generates V-n Diagram."""
        fig, ax = plt.subplots()

        # Assume SL for Mach check
        atm = isa_tropopause(0.0)
        max_v = max(v_ms) if v_ms else 0
        max_mach = max_v / atm.a_m_s

        if max_mach < 0.6:
            x_vals = np.array(v_ms) * 3.6
            x_label = "Velocity (km/h)"
        else:
            x_vals = np.array(v_ms) / atm.a_m_s
            x_label = "Mach Number"

        ax.plot(x_vals, n_pos, color="black", linewidth=2, label="Positive Limit")
        ax.plot(x_vals, n_neg, color="black", linewidth=2, linestyle="--", label="Negative Limit")

        ax.set_xlabel(x_label)
        ax.set_ylabel("Load Factor (g)")
        ax.set_title("V-n Diagram (Maneuver Envelope)")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        filename = "struct_vn_diagram.png"
        path = self.output_dir / filename
        plt.savefig(path, bbox_inches="tight")
        plt.close()
        return str(path)

    def plot_3view(self, geom: Dict[str, Any]) -> Dict[str, str]:
        """Generates 3-view plots (Iso, Top, Side)."""
        # Extract components
        fus = geom.get("fuselage", {})
        wing = geom.get("wing", {})
        ht = geom.get("horizontal_tail", {})
        vt = geom.get("vertical_tail", {})

        # Helper to generate wireframe data
        def get_rect_wireframe(length, width, x, y, z):
            # Simple rectangle for wing/tail
            # x, y, z is LE root
            # Assume constant chord for simplicity or simple taper
            # This is a conceptual visualization
            pts = [[x, y, z], [x + length, y, z], [x + length, y + width, z], [x, y + width, z], [x, y, z]]
            return zip(*pts)

        def get_fus_wireframe(length, diameter):
            # Cylinder approx
            xs = [0, length, length, 0, 0]
            ys = [diameter / 2, diameter / 2, -diameter / 2, -diameter / 2, diameter / 2]
            return xs, ys

        # Prepare figure
        fig = plt.figure(figsize=(10, 6))

        # --- TOP VIEW (X-Y) ---
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Fuselage
        fl, fd = fus.get("length_m", 10), fus.get("diameter_m", 1)
        fx, fy = fus.get("x_m", 0), fus.get("y_m", 0)
        # Draw fuselage outline
        ax.add_patch(
            plt.Rectangle((fx, fy - fd / 2), fl, fd, fill=False, edgecolor="black", linewidth=2, label="Fuselage")
        )

        # Wing (Right)
        ws, war = wing.get("s_ref_m2", 20), wing.get("aspect_ratio", 5)
        wb = np.sqrt(ws * war)
        wcr = 2 * ws / (wb * (1 + wing.get("taper_ratio", 1)))  # approx
        wct = wcr * wing.get("taper_ratio", 1)
        wx, wy = wing.get("x_m", 0), wing.get("y_m", 0)
        sweep = np.radians(wing.get("sweep_deg", 0))
        span = wb / 2
        tip_x_off = span * np.tan(sweep)

        # Right Wing Polygon
        # LE Root, LE Tip, TE Tip, TE Root
        rw_pts = [[wx, wy], [wx + tip_x_off, wy + span], [wx + tip_x_off + wct, wy + span], [wx + wcr, wy]]
        ax.add_patch(plt.Polygon(rw_pts, fill=False, edgecolor="blue", linewidth=2, label="Wing"))

        # Left Wing (Mirror)
        lw_pts = [[wx, wy], [wx + tip_x_off, wy - span], [wx + tip_x_off + wct, wy - span], [wx + wcr, wy]]
        ax.add_patch(plt.Polygon(lw_pts, fill=False, edgecolor="blue", linewidth=2))

        # Horizontal Tail
        if ht:
            hts, htar = ht.get("s_ref_m2", 5), ht.get("aspect_ratio", 4)
            htb = np.sqrt(hts * htar)
            htcr = 2 * hts / (htb * (1 + ht.get("taper_ratio", 0.5)))
            htct = htcr * ht.get("taper_ratio", 0.5)
            htx = ht.get("x_m", fl * 0.9)
            htspan = htb / 2
            htsweep = np.radians(ht.get("sweep_deg", 10))
            httip_x = htspan * np.tan(htsweep)

            rht_pts = [[htx, 0], [htx + httip_x, htspan], [htx + httip_x + htct, htspan], [htx + htcr, 0]]
            lht_pts = [[htx, 0], [htx + httip_x, -htspan], [htx + httip_x + htct, -htspan], [htx + htcr, 0]]
            ax.add_patch(plt.Polygon(rht_pts, fill=False, edgecolor="green", linewidth=1.5, label="Tail"))
            ax.add_patch(plt.Polygon(lht_pts, fill=False, edgecolor="green", linewidth=1.5))

        ax.set_title("Aircraft Top View")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")
        ax.grid(True)
        ax.legend()

        path_top = self.output_dir / "view_top_static.png"
        plt.savefig(path_top, bbox_inches="tight")
        plt.close()

        # --- SIDE VIEW (X-Z) ---
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")

        # Fuselage
        ax.add_patch(plt.Rectangle((fx, -fd / 2), fl, fd, fill=False, edgecolor="black", linewidth=2))

        # Wing (Approx thickness)
        wz = wing.get("z_m", 0)
        ax.add_patch(plt.Rectangle((wx, wz - 0.2), wcr, 0.4, fill=False, edgecolor="blue", linewidth=2))  # schematic

        # Vertical Tail
        if vt:
            vts, vtar = vt.get("s_ref_m2", 3), vt.get("aspect_ratio", 1.5)
            vtb = np.sqrt(vts * vtar)  # Height
            vtcr = 2 * vts / (vtb * (1 + vt.get("taper_ratio", 0.6)))
            vtct = vtcr * vt.get("taper_ratio", 0.6)
            vtx = vt.get("x_m", fl * 0.85)
            vtz = vt.get("z_m", fd / 2)
            vtsweep = np.radians(vt.get("sweep_deg", 30))
            vttip_x = vtb * np.tan(vtsweep)

            vt_pts = [[vtx, vtz], [vtx + vttip_x, vtz + vtb], [vtx + vttip_x + vtct, vtz + vtb], [vtx + vtcr, vtz]]
            ax.add_patch(plt.Polygon(vt_pts, fill=False, edgecolor="green", linewidth=1.5))

        ax.set_title("Aircraft Side View")
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Z (m)")
        ax.grid(True)
        ax.invert_yaxis()  # Z down? Standard Aero is Z down, but for plot Z up is better for humans.
        # Let's keep Z up (positive up).
        ax.set_ylim(-5, 5)  # Adjust

        path_side = self.output_dir / "view_side_static.png"
        plt.savefig(path_side, bbox_inches="tight")
        plt.close()

        # Iso view is hard in 2D static plotter without 3D projection, skipping for now or using side/top
        # Return paths
        return {
            "vsp_top": str(path_top),
            "vsp_side": str(path_side),
            "vsp_iso": str(path_top),  # Reuse top for iso placeholder
        }
