from .mpl_widget import MplWidget


class PayloadRangePlot(MplWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.axes.set_title("Payload-Range Diagram")
        self.axes.set_xlabel("Range (km)")
        self.axes.set_ylabel("Payload (kg)")
        self.axes.grid(True)
        (self.line,) = self.axes.plot([], [], "g-", linewidth=2)
        self.fill = None

    def update_data(self, ranges, payloads):
        try:
            if not ranges or not payloads:
                self.show_content()
                return

            self.line.set_data(ranges, payloads)

            if self.fill:
                try:
                    self.fill.remove()
                except Exception:
                    pass
            self.fill = self.axes.fill_between(ranges, payloads, color="green", alpha=0.1)

            self.axes.relim()
            self.axes.autoscale_view()
            self.draw()
            self.show_content()
        except Exception as e:
            self.show_error(f"Failed to update Payload-Range Plot: {str(e)}")
