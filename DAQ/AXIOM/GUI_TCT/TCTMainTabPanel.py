from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QGroupBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.Plot.TCTPlot import TCTPlot
from config import TCT_TEMPERATURE_VALUES, LASER_NAME_DEFAULT, USER_NAME_DEFAULT

class TCTMainTabPanel(QWidget):
    def __init__(self, start_measurement, default_settings, abort_measurement, disconnect_TCT_devices, connect_TCT_devices, apply_sensor_name_change):
        super().__init__()
        layout = QVBoxLayout()
        
        status_TCT = QGroupBox(title='TCT Status')
        status_TCT.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        status_TCT.setFixedHeight(250)
        
        # Measurement indicator and default settings
        self.measurement_indicator = QLabel('')
        self.measurement_indicator.setFixedSize(15, 15)
        self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        
        self.measurement_info = QLabel('')
        self.measurement_info.setFixedWidth(250)
        self.measurement_info.setContentsMargins(3, 3, 3, 3)
        self.measurement_info.setStyleSheet('background-color: #FBFBFB;')

        indicator_layout = QHBoxLayout()
        indicator_layout.addStretch(1)
        indicator_layout.addWidget(self.measurement_indicator)
        indicator_layout.setAlignment(self.measurement_indicator, Qt.AlignmentFlag.AlignVCenter)
        indicator_layout.addWidget(self.measurement_info)
        indicator_layout.addStretch(1)
        indicator_layout.setSpacing(20)
        indicator_widget = QWidget()
        indicator_widget.setLayout(indicator_layout)
        indicator_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.set_measurement_indicator(mode=2)

        self.default_checkbox = QCheckBox("Default Settings")
        self.default_checkbox.setChecked(True)
        self.default_checkbox.stateChanged.connect(default_settings)

        # Add start after finished measurement checkbox
        self.start_after_finished_measurement_checkbox_TCT = QCheckBox("Start TCT after finished meas.")
        self.start_after_finished_measurement_checkbox_TCT.setFixedWidth(180)
        self.start_after_finished_measurement_checkbox_TCT.setChecked(False)

        # Vertical layout for default settings and start after finished measurement checkbox
        default_settings_start_after_finished_measurement_checkbox_layout = QVBoxLayout()
        default_settings_start_after_finished_measurement_checkbox_layout.setContentsMargins(0, 0, 0, 0)
        default_settings_start_after_finished_measurement_checkbox_layout.addWidget(self.default_checkbox)
        default_settings_start_after_finished_measurement_checkbox_layout.addWidget(self.start_after_finished_measurement_checkbox_TCT)

        # Horizontal layout for measurement indicator and default settings
        indicator_default_settings_layout = QHBoxLayout()
        indicator_default_settings_layout.setContentsMargins(0, 0, 0, 0)
        indicator_default_settings_layout.addWidget(indicator_widget)
        indicator_default_settings_layout.addLayout(default_settings_start_after_finished_measurement_checkbox_layout)
        indicator_default_settings_layout.setAlignment(indicator_widget, Qt.AlignmentFlag.AlignLeft)

        label_font = QFont()
        label_font.setBold(True)
        
        self.connect_TCT = QPushButton('Connect TCT devices')
        self.connect_TCT.setFixedSize(140, 25)
        self.connect_TCT.clicked.connect(connect_TCT_devices)

        self.start_measurement = QPushButton('Start')
        self.start_measurement.setFixedSize(70, 25)
        self.start_measurement.clicked.connect(start_measurement)

        self.abort_measurement = QPushButton('Abort')
        self.abort_measurement.setFixedSize(70, 25)
        self.abort_measurement.clicked.connect(abort_measurement)

        self.disconnect_TCT = QPushButton('Disconnect TCT devices')
        self.disconnect_TCT.setFixedSize(140, 25)
        self.disconnect_TCT.clicked.connect(disconnect_TCT_devices)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.connect_TCT)
        buttons_layout.setAlignment(self.connect_TCT, Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.start_measurement)
        buttons_layout.setAlignment(self.start_measurement, Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.abort_measurement)
        buttons_layout.setAlignment(self.abort_measurement, Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.disconnect_TCT)
        buttons_layout.setAlignment(self.disconnect_TCT, Qt.AlignmentFlag.AlignCenter)

        measurement_label = QLabel('Filename:')
        measurement_label.setFont(label_font)

        self.sensor_name = QLineEdit()
        self.sensor_name.setPlaceholderText("Sensor Name")
        self.sensor_name.setFixedWidth(170)

        self.sensor_temp = QLineEdit()
        self.sensor_temp.setPlaceholderText("Temp (K)")
        self.sensor_temp.setText(TCT_TEMPERATURE_VALUES)
        self.sensor_temp.setFixedWidth(50)

        self.additional_text = QLineEdit()
        self.additional_text.setPlaceholderText("Additional Text")
        self.additional_text.setText(LASER_NAME_DEFAULT)
        self.additional_text.setFixedWidth(170)

        # Add a button to change iv and cv names from sensor name, temp and additional text
        self.change_names_button = QPushButton('Apply')
        self.change_names_button.setFixedSize(60, 25)
        self.change_names_button.clicked.connect(apply_sensor_name_change)

        file_name = QHBoxLayout()
        file_name.addStretch(0)
        file_name.addWidget(measurement_label, alignment=Qt.AlignmentFlag.AlignLeft)
        file_name.addStretch(1)
        file_name.addWidget(self.sensor_name)
        file_name.addStretch(1)
        file_name.addWidget(self.sensor_temp)
        file_name.addStretch(1)
        file_name.addWidget(self.additional_text)
        file_name.addStretch(1)
        file_name.addWidget(self.change_names_button)
        file_name.addStretch(0)

        # Add folder name label and checkmark to see if it already exist
        self.directory_label_TCT = QLabel('<b>Directory: </b>')
        self.directory_label_TCT.setFixedWidth(420)

        self.directory_status_label_TCT = QLabel('')

        directory_layout = QHBoxLayout()
        directory_layout.addStretch(0)
        directory_layout.addWidget(self.directory_label_TCT)
        directory_layout.addStretch(0)
        directory_layout.addWidget(self.directory_status_label_TCT)
        directory_layout.addStretch(1)
        directory_layout.setAlignment(self.directory_label_TCT, Qt.AlignmentFlag.AlignLeft)
        directory_layout.setAlignment(self.directory_status_label_TCT, Qt.AlignmentFlag.AlignLeft)
        directory_layout.setSpacing(0)

        extra_label = QLabel('Extra:')
        extra_label.setFont(label_font)

        self.user_name = QLineEdit()
        self.user_name.setPlaceholderText("User Name")
        self.user_name.setText(USER_NAME_DEFAULT)
        self.user_name.setFixedWidth(200)

        self.comments = QLineEdit()
        self.comments.setPlaceholderText("Comments")
        self.comments.setFixedWidth(200)

        extra_layout = QHBoxLayout()
        extra_layout.addWidget(extra_label)
        extra_layout.setAlignment(extra_label, Qt.AlignmentFlag.AlignLeft)
        extra_layout.addWidget(self.user_name)
        extra_layout.setAlignment(self.user_name, Qt.AlignmentFlag.AlignCenter)
        extra_layout.addWidget(self.comments)
        extra_layout.setAlignment(self.comments, Qt.AlignmentFlag.AlignCenter)

        status_layout = QVBoxLayout()
        status_layout.addLayout(buttons_layout)
        # status_layout.addWidget(indicator_widget)
        status_layout.addSpacing(5)
        status_layout.addLayout(file_name)
        status_layout.addLayout(extra_layout)
        status_layout.addLayout(directory_layout)
        status_TCT.setLayout(status_layout)

        self.results_canvas = TCTPlot()
        self.results_canvas.ax.set_title('TCT Plot')
        self.results_canvas.ax.set_xlabel('Time (s)')
        self.results_canvas.ax.set_ylabel('Voltage (V)')

        self.display_event = QLabel("Event: " + "-", self)
        self.display_volt = QLabel("Voltage(V): " + "-", self)
        self.display_curr = QLabel("Current(A): " + "-", self)

        # Align the labels to the left
        self.display_event.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.display_volt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.display_curr.setAlignment(Qt.AlignmentFlag.AlignLeft)

        horizontal_layout_event_volt_curr = QHBoxLayout()
        horizontal_layout_event_volt_curr.addWidget(self.display_event, stretch=1)
        horizontal_layout_event_volt_curr.addWidget(self.display_volt, stretch=1)
        horizontal_layout_event_volt_curr.addWidget(self.display_curr, stretch=1)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addLayout(indicator_default_settings_layout)
        layout.addWidget(status_TCT)
        layout.setAlignment(status_TCT, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(horizontal_layout_event_volt_curr)
        layout.addWidget(self.results_canvas)
        self.setLayout(layout)

        self.abort_measurement.setEnabled(False)

    def set_measurement_indicator(self, mode: int):
        if mode == 1:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.measurement_info.setText('TCT Measurement in operation')
        elif mode == 2:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.measurement_info.setText('Ready for TCT Measurement')
        elif mode == 4:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.measurement_info.setText('Wait for other Measurement to be finished')
        else:
            raise ValueError('The parameter "mode" must be 1, 2, or 4!')