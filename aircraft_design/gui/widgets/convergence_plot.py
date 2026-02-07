from .mpl_widget import MplWidget
import numpy as np

class ConvergencePlot(MplWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.axes.set_title("MTOW Convergence")
        self.axes.set_xlabel("Iteration")
        self.axes.set_ylabel("MTOW (kg)")
        self.axes.grid(True)
        self.line, = self.axes.plot([], [], 'b-o', label='MTOW')
        self.axes.legend()

    def update_data(self, history):
        if not history:
            return

        iterations = [d['iteration'] for d in history]
        mtows = [d['mtow'] for d in history]

        self.line.set_data(iterations, mtows)
        self.axes.relim()
        self.axes.autoscale_view()
        self.draw()
