from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


class TempHumPlot(FigureCanvasQTAgg):
    def __init__(self, labels_temp: list, labels_hum: list, line_colors_temp: list = None,
                 line_colors_hum: list = None, max_time_range: int = 30,
                 y_axis_range_temp: tuple = (-35, 35), y_axis_range_hum: tuple = (0, 100)):
        """
        This constructor initializes the live plot for the temperature and humidity monitoring.

        :param labels_temp: list of strings; The labels of the temperature measurement locations.
        :param labels_hum: list of strings; The labels of the humidity measurement locations.
        :param line_colors_temp: list of strings; The line colors of the temperature graphs.
        :param line_colors_hum: list of strings; The line colors of the humidity graphs.
        :param max_time_range: integer; The maximum time range in the live plot in minutes.
        :param y_axis_range_temp: tuple; The minimum and maximum temperature value on the y-axis.
        :param y_axis_range_hum: tuple; The minimum and maximum humidity value on the y-axis.
        """

        self.labels_temp = labels_temp
        self.labels_hum = labels_hum
        if line_colors_temp is not None and line_colors_hum is not None \
            and len(line_colors_temp) == len(labels_temp) and len(line_colors_hum) == len(labels_hum):
            self.line_colors_temp = line_colors_temp
            self.line_colors_hum = line_colors_hum
        else:
            self.line_colors_temp = ['C{}'.format(i) for i in range(len(labels_temp))]
            self.line_colors_hum = ['C{}'.format(i) for i in range(len(labels_hum))]
        self.max_time_range = timedelta(minutes=max_time_range)
        self.y_axis_range_temp = y_axis_range_temp
        self.y_axis_range_hum = y_axis_range_hum
        self.time_axis = []
        self.data_temp = [[] for _ in range(len(labels_temp))]
        self.data_hum = [[] for _ in range(len(labels_hum))]
        self.lines_temp = None
        self.lines_hum = None

        # Here we are creating subplots
        self.figure, (self.ax_temp, self.ax_hum) = plt.subplots(nrows=2, ncols=1, figsize=(8, 12))

        # Setting title and labels
        self.ax_temp.set_title('Temperature Monitoring')
        self.ax_hum.set_title('Humidity Monitoring')
        self.ax_temp.set_xlabel('Measurement Time (h:m:s)')
        self.ax_temp.set_ylabel('Temperature (°C)')
        self.ax_hum.set_xlabel('Measurement Time (h:m:s)')
        self.ax_hum.set_ylabel('Relative Humidity (%)')

        # Setting alternative text
        self.ax_temp.legend(loc='center', title='No data available at the moment', handles=[])
        self.ax_hum.legend(loc='center', title='No data available at the moment', handles=[])

        self.figure.tight_layout()

        super().__init__(self.figure)

    def update_graph(self, new_temperatures: list, new_humidities: list):
        """
        This method updates the live plot by appending the given temperature values.

        :param new_temperatures: list of floats; A list which contains one temperature value per label
            (i.e. temperature measurement location).
        :param new_humidities: list of floats; A list which contains one humidity value per label
            (i.e. humidity measurement location).
        """

        # The method self.update() must not be defined as it is already used in the parent class.

        if len(new_temperatures) != len(self.labels_temp):
            raise ValueError('There must be as many temperature values as temperature labels!')
        if len(new_humidities) != len(self.labels_hum):
            raise ValueError('There must be as many humidity values as humidity labels!')

        # Appending data
        for i, new_temp in enumerate(new_temperatures):
            self.data_temp[i].append(new_temp)
        for i, new_hum in enumerate(new_humidities):
            self.data_hum[i].append(new_hum)
        self.time_axis.append(datetime.now())

        # Remove values outside the time range
        min_time = self.time_axis[-1] - self.max_time_range
        if self.time_axis[0] < min_time:
            self.time_axis = [elem for elem in self.time_axis if elem > min_time]
            for i in range(len(self.data_temp)):
                self.data_temp[i] = self.data_temp[i][-len(self.time_axis):]
            for i in range(len(self.data_hum)):
                self.data_hum[i] = self.data_hum[i][-len(self.time_axis):]

        # Plot lines or update plot if it already exists
        if self.lines_temp is None or self.lines_hum is None:
            self.lines_temp = []
            for i in range(len(new_temperatures)):
                self.lines_temp.append(self.ax_temp.plot(self.time_axis, self.data_temp[i],
                                                         label=self.labels_temp[i], color=self.line_colors_temp[i])[0])
                self.ax_temp.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
                # To remove the AutoDateLocator error
                self.ax_temp.xaxis.set_major_locator(AutoDateLocator(maxticks=7, interval_multiples=False))
                self.ax_temp.set_xlim([0, 1]) 
                self.ax_temp.set_ylim(self.y_axis_range_temp)
                self.ax_temp.grid(visible=True, axis='both', linestyle='--', alpha=0.7)
            self.lines_hum = []
            for i in range(len(new_humidities)):
                self.lines_hum.append(self.ax_hum.plot(self.time_axis, self.data_hum[i],
                                                       label=self.labels_hum[i], color=self.line_colors_hum[i])[0])
                self.ax_hum.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
                self.ax_hum.xaxis.set_major_locator(AutoDateLocator(maxticks=7, interval_multiples=False))
                self.ax_hum.set_xlim([0, 1]) 
                self.ax_hum.set_ylim(self.y_axis_range_hum)
                self.ax_hum.grid(visible=True, axis='both', linestyle='--', alpha=0.7)

        else:
            for i, new_temp in enumerate(new_temperatures):
                if -50. < new_temp < 100.:
                    self.lines_temp[i].set_label(self.labels_temp[i] + ': {:.2f} °C'.format(new_temp))
                else:
                    self.lines_temp[i].set_label(self.labels_temp[i] + ': OFF')
                self.lines_temp[i].set_data(self.time_axis, self.data_temp[i])
                self.ax_temp.set_xlim(min(self.time_axis), max(self.time_axis))
            self.ax_temp.legend(loc='upper left', title=None)
            for i, new_hum in enumerate(new_humidities):
                if 0. < new_hum < 100.:
                    self.lines_hum[i].set_label(self.labels_hum[i] + ': {:.1f} %'.format(new_hum))
                else:
                    self.lines_hum[i].set_label(self.labels_hum[i] + ': OFF')
                self.lines_hum[i].set_data(self.time_axis, self.data_hum[i])
                self.ax_hum.set_xlim(min(self.time_axis), max(self.time_axis))
            self.ax_hum.legend(loc='upper left', title=None)
        # self.figure.tight_layout()
            
        self.figure.canvas.draw()
