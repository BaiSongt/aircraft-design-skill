from pathlib import Path


class AdvancedVisualizer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.pv = None
        try:
            import pyvista as pv

            self.pv = pv
            print("PyVista is available for advanced visualization.")
        except ImportError:
            print("PyVista not found. Advanced visualization (OBJ rendering) will be skipped.")
            print("To enable, install pyvista: pip install pyvista qtpy")

    def visualize_obj(self, obj_path: Path):
        """
        Loads and displays the OBJ file using PyVista.
        """
        if not self.pv:
            return

        if not obj_path.exists():
            print(f"OBJ file not found: {obj_path}")
            return

        try:
            print(f"Loading 3D model from {obj_path}...")
            mesh = self.pv.read(str(obj_path))

            pl = self.pv.Plotter()
            pl.add_mesh(mesh, color="white", show_edges=True)
            pl.add_axes()
            pl.add_text("Aircraft Geometry (OpenVSP Export)", position="upper_left")

            # Set camera view
            pl.view_isometric()

            print("Opening 3D Visualization Window...")
            pl.show()

        except Exception as e:
            print(f"Error visualizing OBJ: {e}")

    def create_visualization_script(self, obj_path: Path) -> Path:
        """
        Creates a standalone Python script to visualize the OBJ file,
        useful if the main environment cannot run the GUI loop or for portability.
        """
        script_content = f"""
import sys
from pathlib import Path

try:
    import pyvista as pv
except ImportError:
    print("Error: PyVista is required. Install with: pip install pyvista qtpy")
    sys.exit(1)

def show_model():
    obj_path = Path(r"{obj_path}")
    if not obj_path.exists():
        print(f"File not found: {{obj_path}}")
        return

    print(f"Loading {{obj_path}}...")
    mesh = pv.read(str(obj_path))
    
    pl = pv.Plotter(title="Aircraft Design - Advanced Visualization")
    pl.add_mesh(mesh, color='lightgray', show_edges=True, pbr=True, metallic=0.5)
    pl.add_axes()
    pl.add_text("Detailed Geometry", font_size=12)
    pl.view_isometric()
    pl.show()

if __name__ == "__main__":
    show_model()
"""
        script_path = self.output_dir / "visualize_model.py"
        with open(script_path, "w") as f:
            f.write(script_content)

        return script_path
