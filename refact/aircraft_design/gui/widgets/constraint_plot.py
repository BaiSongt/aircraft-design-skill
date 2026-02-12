from .mpl_widget import MplWidget
import numpy as np


class ConstraintPlot(MplWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.axes.set_title("Constraint Analysis")
        self.axes.set_xlabel("Wing Loading (W/S) [Pa]")
        self.axes.set_ylabel("Thrust-to-Weight (T/W)")
        self.axes.grid(True, linestyle="--", alpha=0.6)

        # Store plot objects
        (self.line_takeoff,) = self.axes.plot([], [], "g-", label="Takeoff")
        (self.line_turn,) = self.axes.plot([], [], "b-", label="Turn")
        (self.line_climb,) = self.axes.plot([], [], "k-", label="Climb")
        self.line_landing = None
        self.fill_landing = None
        (self.point_design,) = self.axes.plot([], [], "r*", markersize=15, label="Design Point")
        self.axes.legend()

    def update_data(self, constraints, design_point):
        try:
            if not constraints:
                self.show_content()
                return

            self.axes.clear()
            self.axes.set_title("Constraint Analysis")
            self.axes.set_xlabel("Wing Loading (W/S) [Pa]")
            self.axes.set_ylabel("Thrust-to-Weight (T/W)")
            self.axes.grid(True, linestyle="--", alpha=0.6)

            # Unpack
            ws = np.array(constraints.get("ws_range", []))
            if len(ws) == 0:
                self.draw()
                self.show_content()
                return

            # Plot lines
            if "takeoff" in constraints:
                self.axes.plot(ws, constraints["takeoff"], "g-", label="Takeoff")

            if "landing" in constraints:
                ws_max = constraints["landing"]
                self.axes.axvline(x=ws_max, color="orange", linestyle="--", label="Landing")
                # Shade invalid region (right side is invalid for max loading)
                self.axes.axvspan(ws_max, max(ws) * 1.1, alpha=0.2, color="orange")

            if "turn" in constraints:
                self.axes.plot(ws, constraints["turn"], "b-", label="Turn")

            if "climb" in constraints:
                self.axes.plot(ws, constraints["climb"], "k-", label="Climb")

            # Plot Design Point
            if design_point:
                self.axes.plot(design_point["ws"], design_point["tw"], "r*", markersize=15, label="Design Point")

            self.axes.legend()
            self.axes.relim()
            self.axes.autoscale_view()
            self.draw()
            self.show_content()
        except Exception as e:
            self.show_error(f"Failed to update Constraint Plot: {str(e)}")
