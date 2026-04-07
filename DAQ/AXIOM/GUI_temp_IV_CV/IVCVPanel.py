from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QGroupBox, QDoubleSpinBox, QSpinBox, QGridLayout, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.Plot.IVCVPlot import IVCVPlot
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from DAQ.AXIOM.GUI_temp_IV_CV.VoltageSettings import VoltageSettings
from config import COMPLIANCE_VALUE_DEFAULT, IV_MEASURE_DELAY_DEFAULT, CV_MEASURE_DELAY_DEFAULT, SAMPLE_NUMBER_DEFAULT, RAMPING_SPEED_DEFAULT, LCR_VOLTAGE_DEFAULT, LCR_FREQ_DEFAULT


class IVCVPanel(QWidget):
     
    def __init__(self, measurement_type: str, start_measurement_thread, open_correction, check_previous_voltage_settings=None
                 # , only_one_start_after_finished_measurement_checkbox_active
                 ):
    # def __init__(self, measurement_type: str, start_measurement_thread):
        if measurement_type not in ['IV', 'CV']:
            raise ValueError('The mode of the panel must be "IV" or "CV"!')
        self.measurement_type = measurement_type

        super().__init__()

        self.check_previous_voltage_settings = check_previous_voltage_settings

        grid_layout_indicator_filename_layout = QGridLayout()
        grid_layout_indicator_filename_layout.setContentsMargins(20, 0, 0, 0)
        grid_layout_indicator_filename_layout.setSpacing(5)
        grid_layout_indicator_filename_layout.setVerticalSpacing(10)
        grid_layout_indicator_filename_layout.setColumnStretch(0, 1)
        grid_layout_indicator_filename_layout.setColumnStretch(1, 0)

        self.measurement_indicator = QLabel('')
        self.measurement_indicator.setFixedSize(15, 15)
        self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.measurement_info = QLabel('')
        self.measurement_info.setFixedWidth(250)
        self.measurement_info.setContentsMargins(3, 3, 3, 3)
        self.measurement_info.setStyleSheet('background-color: #FBFBFB;')
        indicator_layout = QHBoxLayout()
        indicator_layout.setContentsMargins(0, 0, 0, 0)
        indicator_layout.addStretch(1)
        indicator_layout.addWidget(self.measurement_indicator)
        indicator_layout.setAlignment(self.measurement_indicator, Qt.AlignmentFlag.AlignVCenter)
        indicator_layout.addWidget(self.measurement_info)
        indicator_layout.addStretch(1)
        indicator_layout.setSpacing(5)
        indicator_widget = QWidget()
        indicator_widget.setLayout(indicator_layout)
        indicator_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        grid_layout_indicator_filename_layout.addWidget(indicator_widget, 0, 0, Qt.AlignmentFlag.AlignLeft)

        self.set_measurement_indicator(mode=2)


        filename_label = QLabel('Filename:')
        label_font = QFont()
        label_font.setBold(True)
        filename_label.setFont(label_font)
        self.filename_field = QLineEdit()
        self.filename_field.setFixedWidth(200)

        filename_suffix = QLabel(' .csv')

        filename_layout = QHBoxLayout()
        filename_layout.setSpacing(0)
        filename_layout.addWidget(filename_label)
        filename_layout.addSpacing(5)
        filename_layout.addWidget(self.filename_field)
        filename_layout.addWidget(filename_suffix)
        filename_layout.setAlignment(filename_label, Qt.AlignmentFlag.AlignLeft)
        filename_layout.setAlignment(self.filename_field, Qt.AlignmentFlag.AlignLeft)
        filename_layout.setAlignment(filename_suffix, Qt.AlignmentFlag.AlignLeft)

        # Add label to indicate if the filename already exists
        if measurement_type == 'CV':
            self.filename_status_label_CV = QLabel('')
            filename_layout.addSpacing(10)
            filename_layout.addWidget(self.filename_status_label_CV)
            filename_layout.setAlignment(self.filename_status_label_CV, Qt.AlignmentFlag.AlignVCenter)
            
            # Add checkbox to start measurement after current measurement is finished
            self.start_after_finished_measurement_checkbox_CV = QCheckBox('Start CV after finished meas.')
            self.start_after_finished_measurement_checkbox_CV.setFixedWidth(170)
            self.start_after_finished_measurement_checkbox_CV.setChecked(False)
            grid_layout_indicator_filename_layout.addWidget(self.start_after_finished_measurement_checkbox_CV, 0, 1, Qt.AlignmentFlag.AlignLeft)
            
            # Connect signal to only have one available checkbox at a time
            # self.start_after_current_measurement_checkbox_CV.stateChanged.connect(lambda: only_one_start_after_finished_measurement_checkbox_active(tab = "CV"))
            
            # Add ramp to -600V option checkbox
            self.ramp_to_neg600V_CV_checkbox = QCheckBox('Ramp to -600V after CV')
            self.ramp_to_neg600V_CV_checkbox.setFixedWidth(170)
            self.ramp_to_neg600V_CV_checkbox.setChecked(False)
            grid_layout_indicator_filename_layout.addWidget(self.ramp_to_neg600V_CV_checkbox, 1, 1, Qt.AlignmentFlag.AlignLeft)
            
        elif measurement_type == 'IV':
            self.filename_status_label_IV = QLabel('')
            filename_layout.addSpacing(10)
            filename_layout.addWidget(self.filename_status_label_IV)
            filename_layout.setAlignment(self.filename_status_label_IV, Qt.AlignmentFlag.AlignVCenter)
            
            # Add checkbox to start measurement after current measurement is finished
            self.start_after_finished_measurement_checkbox_IV = QCheckBox('Start IV after finished meas.')
            self.start_after_finished_measurement_checkbox_IV.setFixedWidth(170)
            self.start_after_finished_measurement_checkbox_IV.setChecked(False)
            grid_layout_indicator_filename_layout.addWidget(self.start_after_finished_measurement_checkbox_IV, 0, 1, Qt.AlignmentFlag.AlignLeft)
            
            # Connect signal to only have one available checkbox at a time
            # self.start_after_current_measurement_checkbox_IV.stateChanged.connect(lambda: only_one_start_after_finished_measurement_checkbox_active(tab = "IV"))
            
            # Add ramp to -600V option checkbox
            self.ramp_to_neg600V_IV_checkbox = QCheckBox('Ramp to -600V after IV')
            self.ramp_to_neg600V_IV_checkbox.setFixedWidth(170)
            self.ramp_to_neg600V_IV_checkbox.setChecked(False)
            grid_layout_indicator_filename_layout.addWidget(self.ramp_to_neg600V_IV_checkbox, 1, 1, Qt.AlignmentFlag.AlignLeft)
            
        grid_layout_indicator_filename_layout.addLayout(filename_layout, 1, 0, Qt.AlignmentFlag.AlignLeft)

        
        if measurement_type == 'CV':
            self.voltage_settings = VoltageSettings(CV_settings=True, check_previous_voltage_settings=self.check_previous_voltage_settings)
        else:
            self.voltage_settings = VoltageSettings()

        self.advanced_settings = QGroupBox(title='Advanced Settings')
        self.advanced_settings.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.compliance_value = QDoubleSpinBox()
        self.compliance_value.setRange(0, 1000)
        self.compliance_value.setDecimals(1)
        self.compliance_value.setValue(COMPLIANCE_VALUE_DEFAULT)
        self.compliance_value.setSingleStep(1)
        self.compliance_value.setFixedSize(100, 25)
        self.compliance_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compliance_value_labelbox = add_label_to_input(self.compliance_value, 'Compliance (uA)')

        self.measure_delay = QSpinBox()
        self.measure_delay.setRange(0, 100)
        if measurement_type == 'IV':
            self.measure_delay.setValue(IV_MEASURE_DELAY_DEFAULT)
        else:
            self.measure_delay.setValue(CV_MEASURE_DELAY_DEFAULT)
        self.measure_delay.setSingleStep(1)
        self.measure_delay.setFixedSize(100, 25)
        self.measure_delay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        measure_delay_labelbox = add_label_to_input(self.measure_delay, 'Measure Delay (s)')

        self.sample_number = QSpinBox()
        self.sample_number.setRange(0, 100)
        self.sample_number.setValue(SAMPLE_NUMBER_DEFAULT)
        self.sample_number.setSingleStep(1)
        self.sample_number.setFixedSize(100, 25)
        self.sample_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sample_number_labelbox = add_label_to_input(self.sample_number, 'Number of Samples')

        adv_set_layout_top = QHBoxLayout()
        adv_set_layout_top.addWidget(compliance_value_labelbox)
        adv_set_layout_top.addWidget(measure_delay_labelbox)
        adv_set_layout_top.addWidget(sample_number_labelbox)

        self.ramping_speed = QSpinBox()
        self.ramping_speed.setRange(0, 100)
        self.ramping_speed.setValue(RAMPING_SPEED_DEFAULT)
        self.ramping_speed.setSingleStep(1)
        self.ramping_speed.setFixedSize(100, 25)
        self.ramping_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ramping_speed_labelbox = add_label_to_input(self.ramping_speed, 'Ramping Speed (V/s)')

        adv_set_layout_bottom = QHBoxLayout()
        adv_set_layout_bottom.addWidget(ramping_speed_labelbox)

        all_adv_layout = QVBoxLayout()
        all_adv_layout.addLayout(adv_set_layout_top)
        # all_adv_layout.addSpacing(10)
        all_adv_layout.addLayout(adv_set_layout_bottom)
        self.advanced_settings.setLayout(all_adv_layout)

        # --- Add option for timer before starting measurement --- #
        self.timer_start_measurement_checkbox = QCheckBox()
        self.timer_start_measurement_checkbox.setFixedSize(25, 25)
        self.timer_start_measurement_checkbox.setChecked(False)
        timer_start_measurement_checkbox_labelbox = add_label_to_input(self.timer_start_measurement_checkbox, 'Start Timer')
        self.timer_start_measurement_checkbox.stateChanged.connect(self.timer_checkbox_changed)
        
        self.timer_value_start_measurement = QSpinBox()
        self.timer_value_start_measurement.setRange(0, 100)
        self.timer_value_start_measurement.setValue(0)
        self.timer_value_start_measurement.setSingleStep(1)
        self.timer_value_start_measurement.setFixedSize(50, 25)
        self.timer_value_start_measurement.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_value_start_measurement.setEnabled(False)
        timer_value_start_measurement_labelbox = add_label_to_input(self.timer_value_start_measurement, 'Timer Value [min]')
        
        
        self.start_button = QPushButton('Start {} Measurement'.format(self.measurement_type))
        self.start_button.setFixedWidth(180)
        self.abort_button = QPushButton('Abort {} Measurement'.format(self.measurement_type))
        self.abort_button.setFixedWidth(180)
        self.abort_button.setEnabled(False)
        grid_button_layout = QGridLayout()
        # grid_button_layout.setSpacing(20)
        grid_button_layout.addWidget(timer_start_measurement_checkbox_labelbox, 0, 0)
        grid_button_layout.addWidget(timer_value_start_measurement_labelbox, 0, 1, Qt.AlignmentFlag.AlignBottom)
        grid_button_layout.addWidget(self.start_button, 0, 2, Qt.AlignmentFlag.AlignBottom)
        grid_button_layout.addWidget(self.abort_button, 0, 3, Qt.AlignmentFlag.AlignBottom)

        self.results_canvas = IVCVPlot(measurement_type=self.measurement_type)

        self.start_button.clicked.connect(start_measurement_thread)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(10)
        layout.addLayout(grid_layout_indicator_filename_layout)
        layout.addWidget(self.voltage_settings)
        layout.addWidget(self.advanced_settings)
        
        if measurement_type == 'CV':
            self.vol_amplitude = QDoubleSpinBox()
            self.vol_amplitude.setRange(0, 10)
            self.vol_amplitude.setDecimals(2)
            self.vol_amplitude.setValue(LCR_VOLTAGE_DEFAULT)
            self.vol_amplitude.setSingleStep(0.1)
            self.vol_amplitude.setFixedSize(100, 25)
            self.vol_amplitude.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vol_amplitude_labelbox = add_label_to_input(self.vol_amplitude, 'LCR Voltage (V)')

            self.lcr_frequency = QDoubleSpinBox()
            self.lcr_frequency.setRange(0, 100)
            self.lcr_frequency.setDecimals(2)
            self.lcr_frequency.setValue(LCR_FREQ_DEFAULT)
            self.lcr_frequency.setSingleStep(1)
            self.lcr_frequency.setFixedSize(100, 25)
            self.lcr_frequency.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lcr_frequency_labelbox = add_label_to_input(self.lcr_frequency, 'LCR Frequency (kHz)')

            adv_set_layout_bottom.addWidget(vol_amplitude_labelbox)
            adv_set_layout_bottom.addWidget(lcr_frequency_labelbox)
            
            # Monitor the leakage current during CV measurements
            self.leakage_current_monitor = QLabel("nan")
            self.leakage_current_monitor.setFixedSize(100, 22)
            self.leakage_current_monitor.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.leakage_current_monitor.setStyleSheet("""
                QLabel {
                    border: 1px solid gray;
                    border-radius: 2px;
                    background: white;
                    padding: 2px;
                    font: 12px;
                }
            """)
            
            leakage_current_monitor_labelbox = add_label_to_input(self.leakage_current_monitor, "Leakage Current")
            
            self.open_correction = QPushButton('Open Correction')
            self.open_correction.setFixedWidth(180)
            self.open_correction.clicked.connect(open_correction)

            self.open_c_label = QLabel("Open Correction: Not Performed")

            grid_button_layout.addWidget(leakage_current_monitor_labelbox, 1, 1)
            grid_button_layout.addWidget(self.open_correction, 1, 2, Qt.AlignmentFlag.AlignBottom)
            grid_button_layout.addWidget(self.open_c_label, 1, 3, Qt.AlignmentFlag.AlignBottom)
        
        layout.addLayout(grid_button_layout)    
        layout.addStretch(1)
        layout.addWidget(self.results_canvas)
        self.setLayout(layout)

    def set_measurement_indicator(self, mode: int):
        if mode == 1:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.measurement_info.setText('{} Measurement in operation'.format(self.measurement_type))
        elif mode == 2:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.measurement_info.setText('Ready for {} Measurement'.format(self.measurement_type))
        elif mode == 3:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.measurement_info.setText('Ramping down {} Measurement'.format(self.measurement_type))
        elif mode == 4:
            self.measurement_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.measurement_info.setText('Wait for other Measurement to be finished')
        else:
            raise ValueError('The parameter "mode" must be 1, 2, 3 or 4!')

    def timer_checkbox_changed(self):
        if self.timer_start_measurement_checkbox.isChecked():
            self.timer_value_start_measurement.setEnabled(True)
        else:
            self.timer_value_start_measurement.setEnabled(False)