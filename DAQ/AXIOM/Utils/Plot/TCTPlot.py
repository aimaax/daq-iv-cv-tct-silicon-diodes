import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

class TCTPlot(FigureCanvasQTAgg):
    def __init__(self):
        """
        This constructor initializes the live plot for the TCT measurements.
        """

        self.x_data = []
        self.y_data = []
        self.line = None

        # Here we are creating subplots
        self.figure, self.ax = plt.subplots(figsize=(6, 6))
        self.cb = None
        self.axim1 = None
        self.matrix_init = None

        # Setting alternative text 
        self.ax.legend(loc='center', title='No data available at the moment', handles=[])

        self.figure.tight_layout()

        super().__init__(self.figure)

    def plot_graph(self, scaled_time, scaled_wave):
        self.x_data = scaled_time
        self.y_data = scaled_wave
        if self.ax.get_legend():
                self.ax.get_legend().remove()
        self.line = self.ax.plot(self.x_data, self.y_data, color='blue')[0]
        plot_space = (max(self.y_data) - min(self.y_data)) * 0.1
        self.ax.set_ylim((min(self.y_data)-plot_space, max(self.y_data)+plot_space))
        self.figure.tight_layout()
        self.figure.canvas.draw()

    def plot_graph_analysis(self, scaled_time, scaled_wave):
        self.x_data = scaled_time
        self.y_data = scaled_wave
        if self.ax.get_legend():
                self.ax.get_legend().remove()
        self.line = self.ax.plot(self.x_data, self.y_data, color='blue', linestyle='none', marker='o')[0]
        # plot_space = (max(self.y_data) - min(self.y_data)) * 0.1
        # self.ax.set_ylim((min(self.y_data)-plot_space, max(self.y_data)+plot_space))
        self.ax.grid(visible=True, axis='both', linestyle='--', alpha=0.7)
        self.figure.tight_layout()
        self.figure.canvas.draw() 

    def update_graph(self, new_voltage: float, new_data: float,
                     voltage_range: tuple = (0, -1000)):
        """
        This method updates the live plot by appending the given data values.

        :param new_voltage: float; The voltage value of a new data point.
        :param new_data: float; The data value of a new data point.
        :param voltage_range: tuple; The minimum and maximum voltage value on the x-axis.
        """

        # Appending data
        self.x_data.append(new_voltage)
        self.y_data.append(new_data)

        # Plot line or update plot if it already exists
        if self.line is None:
            if self.ax.get_legend():
                self.ax.get_legend().remove()
            self.line = self.ax.plot(self.x_data, self.y_data, color='blue', linestyle='none', marker='o')[0]
            self.ax.grid(visible=True, axis='both', linestyle='--', alpha=0.7)
            self.ax.set_xlim((voltage_range[0]+10, voltage_range[1]-10))
            self.figure.tight_layout()

        else:
            self.line.set_data(self.x_data, self.y_data)
            self.ax.set_xlim((voltage_range[0]+10, voltage_range[1]-10))

        plot_space = max((max(self.y_data) - min(self.y_data)) * 0.1, 1)
        self.ax.set_ylim((min(self.y_data)-plot_space, max(self.y_data)+plot_space))
        self.figure.canvas.draw()

    def clear_graph(self):
        if self.cb is not None:
            self.cb.remove()
            self.axim1.set_data(self.matrix_init)

        if self.line is not None:
            self.x_data = []
            self.y_data = []
            self.line.set_data(self.x_data, self.y_data)

