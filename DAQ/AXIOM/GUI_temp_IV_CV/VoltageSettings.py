from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QGroupBox, QSpinBox, QGridLayout, QCheckBox, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from config import TCT_START_VOLTAGE, IV_CV_START_VOLTAGE, TCT_STOP_VOLTAGE, IV_CV_STOP_VOLTAGE, TCT_VOLTAGE_STEP_SIZE, IV_CV_VOLTAGE_STEP_SIZE, CV_FINE_VOLTAGE_STOP, CV_FINE_VOLTAGE_STEP_SIZE, TCT_FINE_VOLTAGE_START, TCT_FINE_VOLTAGE_STEP_SIZE

class VoltageSettings(QGroupBox):
    def __init__(self, TCT_settings = False, CV_settings = False, check_previous_voltage_settings = None):
        super().__init__(title='Voltage Settings')

        self.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.check_previous_voltage_settings = check_previous_voltage_settings

        self.voltage_ramp_start = QSpinBox()
        self.voltage_ramp_start.setRange(-1000, 0)
        self.voltage_ramp_start.setValue(-900 if TCT_settings else -25)
        self.voltage_ramp_start.setValue(TCT_START_VOLTAGE if TCT_settings else IV_CV_START_VOLTAGE)
        self.voltage_ramp_start.setSingleStep(10)
        self.voltage_ramp_start.setFixedSize(100, 25)
        self.voltage_ramp_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voltage_ramp_start_labelbox = add_label_to_input(self.voltage_ramp_start, 'Start Voltage (V)')

        self.voltage_ramp_stop = QSpinBox()
        self.voltage_ramp_stop.setRange(-1000, 0)
        self.voltage_ramp_stop.setValue(TCT_STOP_VOLTAGE if TCT_settings else IV_CV_STOP_VOLTAGE)
        self.voltage_ramp_stop.setSingleStep(10)
        self.voltage_ramp_stop.setFixedSize(100, 25)
        self.voltage_ramp_stop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voltage_ramp_stop_labelbox = add_label_to_input(self.voltage_ramp_stop, 'Stop Voltage (V)')

        self.voltage_ramp_step = QSpinBox()
        self.voltage_ramp_step.setRange(0, 500)
        self.voltage_ramp_step.setValue(TCT_VOLTAGE_STEP_SIZE if TCT_settings else IV_CV_VOLTAGE_STEP_SIZE)
        self.voltage_ramp_step.setSingleStep(1)
        self.voltage_ramp_step.setFixedSize(100, 25)
        self.voltage_ramp_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voltage_ramp_step_labelbox = add_label_to_input(self.voltage_ramp_step, 'Voltage Step Size (V)')
        
        vol_set_layout = QGridLayout()
        vol_set_layout.addWidget(voltage_ramp_start_labelbox, 0, 0)
        vol_set_layout.addWidget(voltage_ramp_stop_labelbox, 0, 1)
        vol_set_layout.addWidget(voltage_ramp_step_labelbox, 0, 2)

        if CV_settings:
            self.fine_voltage_checkbox = QCheckBox()
            self.fine_voltage_checkbox.setChecked(False)
            fine_voltage_checkbox_labelbox = add_label_to_input(self.fine_voltage_checkbox, "Enable Fine Voltage")
            
            self.voltage_fine_stop = QSpinBox()
            self.voltage_fine_stop.setRange(-1000, 0)
            self.voltage_fine_stop.setValue(CV_FINE_VOLTAGE_STOP)
            self.voltage_fine_stop.setSingleStep(1)
            self.voltage_fine_stop.setFixedSize(100, 25)
            self.voltage_fine_stop.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.voltage_fine_stop.setEnabled(False)
            voltage_fine_stop_labelbox = add_label_to_input(self.voltage_fine_stop, "Fine Voltage Stop")

            self.voltage_fine_ramp = QSpinBox()
            self.voltage_fine_ramp.setRange(0, 500)
            self.voltage_fine_ramp.setValue(CV_FINE_VOLTAGE_STEP_SIZE)
            self.voltage_fine_ramp.setSingleStep(1)
            self.voltage_fine_ramp.setFixedSize(100, 25)
            self.voltage_fine_ramp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.voltage_fine_ramp.setEnabled(False)
            voltage_fine_ramp_labelbox = add_label_to_input(self.voltage_fine_ramp, "Fine Step Size (V)")

            # Check previous voltage settings button
            self.check_previous_voltage_settings_button = QPushButton("Check Prev. Meas.")
            self.check_previous_voltage_settings_button.setFixedSize(120, 25)
            self.check_previous_voltage_settings_button.clicked.connect(self.check_previous_voltage_settings)
            
            def toggle_fine_voltage_CV(enabled):
                self.voltage_fine_stop.setEnabled(enabled)
                self.voltage_fine_ramp.setEnabled(enabled)
                
            self.fine_voltage_checkbox.toggled.connect(toggle_fine_voltage_CV)
            
            vol_set_layout.addWidget(fine_voltage_checkbox_labelbox, 1, 0)
            vol_set_layout.addWidget(voltage_fine_stop_labelbox, 1, 1)
            vol_set_layout.addWidget(voltage_fine_ramp_labelbox, 1, 2)
            vol_set_layout.addWidget(self.check_previous_voltage_settings_button, 1, 3, alignment=Qt.AlignmentFlag.AlignBottom)


        if TCT_settings:    
            self.fine_voltage_checkbox = QCheckBox()
            self.fine_voltage_checkbox.setChecked(False)
            fine_voltage_checkbox_labelbox = add_label_to_input(self.fine_voltage_checkbox, "Enable Fine Voltage")
            
            self.voltage_fine_start = QSpinBox()
            self.voltage_fine_start.setRange(-1000, 0)
            self.voltage_fine_start.setValue(TCT_FINE_VOLTAGE_START)
            self.voltage_fine_start.setSingleStep(1)
            self.voltage_fine_start.setFixedSize(100, 25)
            self.voltage_fine_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.voltage_fine_start.setEnabled(False)
            voltage_fine_start_labelbox = add_label_to_input(self.voltage_fine_start, "Fine Voltage Start")

            self.voltage_fine_ramp = QSpinBox()
            self.voltage_fine_ramp.setRange(0, 500)
            self.voltage_fine_ramp.setValue(TCT_FINE_VOLTAGE_STEP_SIZE)
            self.voltage_fine_ramp.setSingleStep(1)
            self.voltage_fine_ramp.setFixedSize(100, 25)
            self.voltage_fine_ramp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.voltage_fine_ramp.setEnabled(False)
            voltage_fine_ramp_labelbox = add_label_to_input(self.voltage_fine_ramp, "Fine Step Size (V)")

            # Check previous voltage settings button
            self.check_previous_voltage_settings_button = QPushButton("Check Prev. Meas.")
            self.check_previous_voltage_settings_button.setFixedSize(120, 25)
            self.check_previous_voltage_settings_button.clicked.connect(self.check_previous_voltage_settings)
            
            def toggle_fine_voltage_TCT(enabled):
                self.voltage_fine_start.setEnabled(enabled)
                self.voltage_fine_ramp.setEnabled(enabled)
                
            self.fine_voltage_checkbox.toggled.connect(toggle_fine_voltage_TCT)
            
            vol_set_layout.addWidget(fine_voltage_checkbox_labelbox, 1, 0)
            vol_set_layout.addWidget(voltage_fine_start_labelbox, 1, 1)
            vol_set_layout.addWidget(voltage_fine_ramp_labelbox, 1, 2)
            vol_set_layout.addWidget(self.check_previous_voltage_settings_button, 1, 3, alignment=Qt.AlignmentFlag.AlignBottom)
            
        self.setLayout(vol_set_layout)
