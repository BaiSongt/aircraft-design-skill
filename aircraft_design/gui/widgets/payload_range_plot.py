from .mpl_widget import MplWidget

class PayloadRangePlot(MplWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.axes.set_title("Payload-Range Diagram")
        self.axes.set_xlabel("Range (km)")
        self.axes.set_ylabel("Payload (kg)")
        self.axes.grid(True)
        self.line, = self.axes.plot([], [], 'g-', linewidth=2)
        self.fill = None

    def update_data(self, ranges, payloads):
        if not ranges or not payloads:
            return

        self.line.set_data(ranges, payloads)
        
        if self.fill:
            self.fill.remove()
        self.fill = self.axes.fill_between(ranges, payloads, color='green', alpha=0.1)
        
        self.axes.relim()
        self.axes.autoscale_view()
        self.draw()
