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
        self.axes.set_box_aspect([1,1,1])

    def update_data(self, geom):
        if not geom:
            return
            
        self.axes.clear()
        self.axes.set_title("Aircraft Geometry (3D)")
        self.axes.set_xlabel("X (m)")
        self.axes.set_ylabel("Y (m)")
        self.axes.set_zlabel("Z (m)")

        # Fuselage (Cylinder approximation)
        fus = geom.get('fuselage', {})
        L = fus.get('length_m', 10.0)
        D = fus.get('diameter_m', 1.0)
        
        # Draw fuselage line for simplicity or a cylinder
        # Line
        self.axes.plot([0, L], [0, 0], [0, 0], 'k-', linewidth=2)
        
        # Wing
        wing = geom.get('wing', {})
        S = wing.get('s_ref_m2', 20.0)
        AR = wing.get('aspect_ratio', 3.0)
        sweep = np.radians(wing.get('sweep_deg', 0))
        
        if S > 0 and AR > 0:
            b = np.sqrt(S * AR)
            # Simple trapezoidal wing
            # Root chord approx
            cr = 2 * S / b 
            ct = cr * wing.get('taper_ratio', 1.0)
            
            x_le_root = L * 0.4
            y_root = 0
            z_root = 0
            
            # Tip coordinates
            y_tip = b/2
            x_le_tip = x_le_root + (b/2) * np.tan(sweep)
            z_tip = 0 # Flat wing
            
            # Vertices for right wing
            verts_right = [
                [x_le_root, y_root, z_root],
                [x_le_tip, y_tip, z_tip],
                [x_le_tip + ct, y_tip, z_tip],
                [x_le_root + cr, y_root, z_root]
            ]
            
            # Vertices for left wing
            verts_left = [
                [x_le_root, -y_root, z_root],
                [x_le_tip, -y_tip, z_tip],
                [x_le_tip + ct, -y_tip, z_tip],
                [x_le_root + cr, -y_root, z_root]
            ]
            
            # Add collection
            poly = Poly3DCollection([verts_right, verts_left], alpha=0.6, facecolor='cyan', edgecolor='b')
            self.axes.add_collection3d(poly)

        # Set limits
        max_dim = max(L, b if 'b' in locals() else 10)
        self.axes.set_xlim(0, max_dim)
        self.axes.set_ylim(-max_dim/2, max_dim/2)
        self.axes.set_zlim(-max_dim/2, max_dim/2)
        
        self.draw()
