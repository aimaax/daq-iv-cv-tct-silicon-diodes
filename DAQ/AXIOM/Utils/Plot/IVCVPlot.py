import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


class IVCVPlot(FigureCanvasQTAgg):
    def __init__(self, measurement_type: str = 'IV'):
        """
        This constructor initializes the live plot for the IV and CV measurements.

        :param measurement_type: string; The measurement type can be "IV" or "CV".
        """

        if measurement_type not in ['IV', 'CV']:
            raise ValueError('The measurement type for the live plot must be "IV" or "CV"!')

        self.x_data = []
        self.y_data = []
        self.line = None

        # These are to change the unit with which you work
        self.multipl_vol = 1
        self.multipl_data = 1
        
        # Here we are creating subplots
        self.figure, self.ax = plt.subplots(figsize=(8, 6))

        # Setting title and labels
        self.ax.set_title(measurement_type + ' Diagram')
        self.ax.set_xlabel('Voltage (V)')
        if measurement_type == 'IV':
            self.ax.set_ylabel('Current (uA)')
            self.multipl_data = 1e6
        elif measurement_type == 'CV':
            self.ax.set_ylabel(r'$1/C^2$')

        # Setting alternative text
        self.ax.legend(loc='center', title='No data available at the moment', handles=[])

        self.figure.tight_layout()

        super().__init__(self.figure)

    def update_graph(self, new_voltage: float, new_data: float,
                     voltage_range: tuple = (0, -1000)):
        """
        This method updates the live plot by appending the given data values.

        :param new_voltage: float; The voltage value of a new data point.
        :param new_data: float; The data value of a new data point.
        :param voltage_range: tuple; The minimum and maximum voltage value on the x-axis.
        """

        # Appending data
        self.x_data.append(new_voltage * self.multipl_vol)
        self.y_data.append(new_data * self.multipl_data)

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

        # Handle error when values max/min are identical
        try: 
            plot_space = max((max(self.y_data) - min(self.y_data)) * 0.1, 0.01)
            self.ax.set_ylim((min(self.y_data)-plot_space, max(self.y_data)+plot_space))
        except ValueError as e:
            print(f"Failed to set ylim: {e}")
            print(f"self.y_data = {self.y_data}")
            self.ax.set_ylim(0, 1)
            
        self.figure.canvas.draw()

    def clear_graph(self):
        if self.line is not None:
            self.x_data = []
            self.y_data = []
            self.line.set_data(self.x_data, self.y_data)
