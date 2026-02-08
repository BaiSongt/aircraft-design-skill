import pyvista as pv
from pyvistaqt import QtInteractor
import numpy as np


class PyVistaWidget(QtInteractor):
    def __init__(self, parent=None, view_mode="iso"):
        super().__init__(parent)
        self.view_mode = view_mode
        self.mesh = None

        # Setup camera/background
        self.set_background("white")
        self.show_axes()

        if view_mode == "top":
            self.view_xy()
            self.enable_parallel_projection()
            self.add_text("Top View", position="upper_left", color="black", font_size=10)
        elif view_mode == "side":
            self.view_xz()  # Side view (X-Z) - check coordinate system
            self.enable_parallel_projection()
            self.add_text("Side View", position="upper_left", color="black", font_size=10)
        else:
            self.view_isometric()
            self.add_text("3D View", position="upper_left", color="black", font_size=10)

    def update_mesh(self, geom_dict):
        """
        Updates the scene with new geometry.
        geom_dict: Dictionary containing component data (vertices/faces or parameters)
        """
        self.clear()

        # Re-add axes and text after clear
        self.show_axes()
        if self.view_mode == "top":
            self.add_text("Top View", position="upper_left", color="black", font_size=10)
        elif self.view_mode == "side":
            self.add_text("Side View", position="upper_left", color="black", font_size=10)
        else:
            self.add_text("3D View", position="upper_left", color="black", font_size=10)

        # Parse geometry and build meshes
        # This logic mirrors GeometryView3D but builds pyvista meshes

        # 1. Mesh-based components (if available)
        # We look for 'vertices' and 'faces' in components
        components = ["fuselage", "wing", "htail", "vtail", "horizontal_tail", "vertical_tail"]

        has_mesh_data = False

        for name in components:
            comp = geom_dict.get(name)
            if not comp:
                # Handle alias keys like 'horizontal_tail' vs 'htail'
                if name == "htail":
                    comp = geom_dict.get("horizontal_tail")
                if name == "vtail":
                    comp = geom_dict.get("vertical_tail")

            if not comp:
                continue

            if "vertices" in comp and "faces" in comp:
                has_mesh_data = True
                verts = np.array(comp["vertices"])
                faces = comp["faces"]

                # PyVista faces format: [n_nodes, node1, node2, ..., n_nodes, node1, ...]
                # Assuming input faces are list of lists of indices
                pv_faces = []
                for f in faces:
                    pv_faces.append(len(f))
                    pv_faces.extend(f)

                mesh = pv.PolyData(verts, pv_faces)

                # Color
                color = comp.get("color", "gray")
                self.add_mesh(mesh, color=color, show_edges=True, edge_color="black", line_width=1)

        if not has_mesh_data:
            # Fallback to parametric approximation
            # Fuselage (Cylinder)
            fus = geom_dict.get("fuselage", {})
            L = fus.get("length_m") or geom_dict.get("fuselage_length_m", 10.0)
            D = fus.get("diameter_m") or geom_dict.get("fuselage_diameter_m", 1.0)

            # Create a simple cylinder (oriented along X)
            # PyVista cylinder is along Y by default, need rotation
            cyl = pv.Cylinder(center=(L / 2, 0, 0), direction=(1, 0, 0), radius=D / 2, height=L)
            self.add_mesh(cyl, color="lightgray", show_edges=False)

            # Wing
            wing = geom_dict.get("wing", {})
            S = wing.get("s_ref_m2") or geom_dict.get("s_wing", 20.0)
            AR = wing.get("aspect_ratio") or geom_dict.get("aspect_ratio", 3.0)
            sweep = wing.get("sweep_deg") or geom_dict.get("sweep_deg", 0)
            taper = wing.get("taper_ratio") or geom_dict.get("taper_ratio", 1.0)

            if S > 0:
                b = np.sqrt(S * AR)
                cr = 2 * S / (b * (1 + taper))
                ct = cr * taper

                # Create a simple flat wing surface
                # Root LE at (0.4*L, 0, 0) approx
                x_le_root = L * 0.4
                y_root = 0
                z_root = 0

                # Right Wing
                tip_y = b / 2
                tip_x = x_le_root + (b / 2) * np.tan(np.radians(sweep))

                # 4 points: LE_root, LE_tip, TE_tip, TE_root
                pts = np.array(
                    [
                        [x_le_root, y_root, z_root],  # LE Root
                        [tip_x, tip_y, z_root],  # LE Tip
                        [tip_x + ct, tip_y, z_root],  # TE Tip
                        [x_le_root + cr, y_root, z_root],  # TE Root
                    ]
                )
                faces = [4, 0, 1, 2, 3]
                wing_mesh = pv.PolyData(pts, faces)

                # Left Wing (Mirror)
                pts_l = pts.copy()
                pts_l[:, 1] *= -1  # Invert Y
                # Reorder for correct normal?
                pts_l = pts_l[[0, 3, 2, 1]]
                wing_mesh_l = pv.PolyData(pts_l, faces)

                self.add_mesh(wing_mesh, color="lightblue", show_edges=True)
                self.add_mesh(wing_mesh_l, color="lightblue", show_edges=True)

        # Reset camera to fit bounds
        self.reset_camera()

        # Restore view orientation
        if self.view_mode == "top":
            self.view_xy()
        elif self.view_mode == "side":
            self.view_xz()  # Note: Z up? Standard Aero Z is down, but visualization usually Z up.
            # If Z is down, side view X-Z might need inversion.
            # Let's assume standard visualization frame: X back, Y right, Z up.
            # If input data is aero frame (X back, Y right, Z down), we might need to flip Z.
            # Assuming input data is already visualization-friendly or we adjust.
            pass

    def load_file(self, file_path):
        """Loads a mesh file (obj, stl, etc.)"""
        self.clear()
        self.show_axes()

        try:
            mesh = pv.read(file_path)
            self.add_mesh(mesh, show_edges=True, edge_color="black", line_width=0.5, color="white")
            self.reset_camera()

            if self.view_mode == "top":
                self.view_xy()
                self.add_text("Top View (Detailed)", position="upper_left", color="black", font_size=10)
            elif self.view_mode == "side":
                self.view_xz()
                self.add_text("Side View (Detailed)", position="upper_left", color="black", font_size=10)
            else:
                self.add_text("3D View (Detailed)", position="upper_left", color="black", font_size=10)

        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
