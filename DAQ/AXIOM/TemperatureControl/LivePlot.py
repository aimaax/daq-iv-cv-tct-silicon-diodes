from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator
import matplotlib
matplotlib.use('Qt5Agg')


class LivePlot:
    def __init__(self, labels: list, line_colors: list = None,
                 max_time_range: int = 30, y_axis_range: tuple = (-35, 35)):
        """
        This constructor initializes the live plot for the temperature monitoring.

        :param labels: list of strings; The labels of the temperature measurement locations.
        :param line_colors: list of strings; The line colors of the temperature graphs.
        :param max_time_range: integer; The maximum time range in the live plot in minutes.
        :param y_axis_range: tuple; The minimum and maximum temperature value on the y-axis.
        """

        self.labels = labels
        if line_colors is not None and len(line_colors) == len(labels):
            self.line_colors = line_colors
        else:
            self.line_colors = ['C{}'.format(i) for i in range(len(labels))]
        self.max_time_range = timedelta(minutes=max_time_range)
        self.y_axis_range = y_axis_range
        self.time_axis = []
        self.data = [[] for _ in range(len(labels))]
        self.lines = None

        # To run GUI event loop
        plt.ion()

        # Here we are creating subplots
        self.figure, self.ax = plt.subplots(figsize=(8, 6))

        # Setting title and labels
        self.ax.set_title('Temperature Monitoring')
        self.ax.set_xlabel('Measurement Time (h:m:s)')
        self.ax.set_ylabel('Temperature (°C)')

        # Setting alternative text
        self.ax.legend(loc='center', title='No data available at the moment', handles=[])

    def update(self, new_temperatures: list):
        """
        This method updates the live plot by appending the given temperature values.

        :param new_temperatures: list of floats; A list which contains one temperature value per label
            (i.e. temperature measurement location).
        """

        if len(new_temperatures) != len(self.labels):
            raise ValueError('There must be as many temperature values as labels!')

        # Appending data
        for i, new_temp in enumerate(new_temperatures):
            self.data[i].append(new_temp)
        self.time_axis.append(datetime.now())

        # Remove values outside the time range
        min_time = self.time_axis[-1] - self.max_time_range
        if self.time_axis[0] < min_time:
            self.time_axis = [elem for elem in self.time_axis if elem > min_time]
            for i in range(len(self.data)):
                self.data[i] = self.data[i][-len(self.time_axis):]

        # Plot lines or update plot if it already exists
        if self.lines is None:
            self.lines = []
            for i in range(len(new_temperatures)):
                self.lines.append(self.ax.plot(self.time_axis, self.data[i], label=self.labels[i], color=self.line_colors[i])[0])
                self.ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
                self.ax.xaxis.set_major_locator(AutoDateLocator(maxticks=7))
                self.ax.set_xlim([0, 1])
                self.ax.set_ylim(self.y_axis_range)
                self.ax.grid(visible=True, axis='both', linestyle='--', alpha=0.7)
            self.figure.tight_layout()
            plt.show(block=False)

        else:
            for i, new_temp in enumerate(new_temperatures):
                if -50. < new_temp < 100.:
                    self.lines[i].set_label(self.labels[i] + ': {:.2f} °C'.format(new_temp))
                else:
                    self.lines[i].set_label(self.labels[i] + ': OFF')
                self.lines[i].set_data(self.time_axis, self.data[i])
                self.ax.set_xlim(min(self.time_axis), max(self.time_axis))
        self.ax.legend(loc='upper left', title=None)
        self.figure.canvas.flush_events()
