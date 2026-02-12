from .mpl_widget import MplWidget
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class GeometryView3D(MplWidget):
    def __init__(self, parent=None):
        super().__init__(parent, projection_3d=True)
        self.axes.set_title("Aircraft Geometry (3D)")
        self.axes.set_xlabel("X (m)")
        self.axes.set_ylabel("Y (m)")
        self.axes.set_zlabel("Z (m)")

        # Set equal aspect ratio trick for 3D
        self.axes.set_box_aspect([1, 1, 1])

    def update_data(self, geom):
        if not geom:
            return

        self.axes.clear()
        self.axes.set_title("Aircraft Geometry (3D)")
        self.axes.set_xlabel("X (m)")
        self.axes.set_ylabel("Y (m)")
        self.axes.set_zlabel("Z (m)")

        # Check for mesh format (vertices/faces)
        is_mesh = False
        if "wing" in geom and isinstance(geom["wing"], dict) and "vertices" in geom["wing"]:
            is_mesh = True

        if is_mesh:
            max_dim = 10.0
            # Iterate over components
            for part_name in ["fuselage", "wing", "htail", "vtail"]:
                part = geom.get(part_name)
                if not part:
                    continue

                vertices = part.get("vertices")
                faces = part.get("faces")
                color = part.get("color", "gray")

                if vertices and faces:
                    # Construct polygons
                    # Poly3DCollection expects a list of (N, 3) arrays, where each array is a polygon
                    polys = []
                    for face in faces:
                        # face is a list of indices
                        poly_verts = [vertices[idx] for idx in face]
                        polys.append(poly_verts)

                    # Update max_dim for scaling
                    # Simple check of max x
                    max_x = max([v[0] for v in vertices]) if vertices else 0
                    if max_x > max_dim:
                        max_dim = max_x

                    collection = Poly3DCollection(polys, alpha=0.8, facecolor=color, edgecolor="k", linewidths=0.2)
                    self.axes.add_collection3d(collection)

            # Set limits based on max_dim
            self.axes.set_xlim(0, max_dim)
            self.axes.set_ylim(-max_dim / 2, max_dim / 2)
            self.axes.set_zlim(-max_dim / 2, max_dim / 2)

        else:
            # Legacy/Simplified parameter-based drawing
            # Fuselage (Cylinder approximation)
            fus = geom.get("fuselage", {})
            # Handle different key names if coming from simplified dict
            L = fus.get("length_m") or geom.get("fuselage_length_m", 10.0)
            D = fus.get("diameter_m") or geom.get("fuselage_diameter_m", 1.0)

            # Draw fuselage line for simplicity or a cylinder
            # Line
            self.axes.plot([0, L], [0, 0], [0, 0], "k-", linewidth=2)

            # Wing
            wing = geom.get("wing", {})
            # Handle flattened dict
            S = wing.get("s_ref_m2") or geom.get("s_wing", 20.0)
            AR = wing.get("aspect_ratio") or geom.get("aspect_ratio", 3.0)
            sweep = np.radians(wing.get("sweep_deg") or geom.get("sweep_deg", 0))
            taper = wing.get("taper_ratio") or geom.get("taper_ratio", 1.0)

            if S > 0 and AR > 0:
                b = np.sqrt(S * AR)
                # Simple trapezoidal wing
                # Root chord approx
                cr = 2 * S / (b * (1 + taper))
                ct = cr * taper

                x_le_root = L * 0.4
                y_root = 0
                z_root = 0

                # Tip coordinates
                y_tip = b / 2
                x_le_tip = x_le_root + (b / 2) * np.tan(sweep)
                z_tip = 0  # Flat wing

                # Vertices for right wing
                verts_right = [
                    [x_le_root, y_root, z_root],
                    [x_le_tip, y_tip, z_tip],
                    [x_le_tip + ct, y_tip, z_tip],
                    [x_le_root + cr, y_root, z_root],
                ]

                # Vertices for left wing
                verts_left = [
                    [x_le_root, -y_root, z_root],
                    [x_le_tip, -y_tip, z_tip],
                    [x_le_tip + ct, -y_tip, z_tip],
                    [x_le_root + cr, -y_root, z_root],
                ]

                # Add collection
                poly = Poly3DCollection([verts_right, verts_left], alpha=0.6, facecolor="cyan", edgecolor="b")
                self.axes.add_collection3d(poly)

            # Set limits
            max_dim = max(L, b if "b" in locals() else 10)
            self.axes.set_xlim(0, max_dim)
            self.axes.set_ylim(-max_dim / 2, max_dim / 2)
            self.axes.set_zlim(-max_dim / 2, max_dim / 2)

        self.draw()
