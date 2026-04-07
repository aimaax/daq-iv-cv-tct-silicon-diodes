from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QDoubleSpinBox, QSpinBox, QTabWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from DAQ.AXIOM.GUI_temp_IV_CV.VoltageSettings import VoltageSettings
from config import VSOURCE_COMPLIANCE_DEFAULT, VSOURCE_MEASURE_DELAY_DEFAULT, VSOURCE_RAMPING_SPEED_DEFAULT, VSOURCE_RAMPING_INTERVAL_DEFAULT

 
class TCTVoltageSourcePanel(QWidget): 
    def __init__(self, vsource_connect, vsource_disconnect, check_previous_voltage_settings):
        super().__init__()

        status_VSource = QGroupBox(title='Voltage Source Init')
        status_VSource.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.vsource_connect = QPushButton('Connect')
        self.vsource_connect.setFixedSize(70, 25)
        self.vsource_connect.clicked.connect(vsource_connect)

        self.vsource_disconnect = QPushButton('Disconnect')
        self.vsource_disconnect.setFixedSize(70, 25)
        self.vsource_disconnect.clicked.connect(vsource_disconnect)

        connect_layout = QHBoxLayout()
        connect_layout.addWidget(self.vsource_connect)
        connect_layout.setAlignment(self.vsource_connect, Qt.AlignmentFlag.AlignCenter)
        connect_layout.addWidget(self.vsource_disconnect)
        connect_layout.setAlignment(self.vsource_disconnect, Qt.AlignmentFlag.AlignCenter)

        self.vsource_indicator = QLabel('')
        self.vsource_indicator.setFixedSize(15, 15)
        self.vsource_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.vsource_info = QLabel('')
        self.vsource_info.setFixedWidth(250)
        self.vsource_info.setContentsMargins(3, 3, 3, 3)
        self.vsource_info.setStyleSheet('background-color: #FBFBFB;')
        vsource_layout = QHBoxLayout()
        vsource_layout.addStretch(1)
        vsource_layout.addWidget(self.vsource_indicator)
        vsource_layout.setAlignment(self.vsource_indicator, Qt.AlignmentFlag.AlignVCenter)
        vsource_layout.addWidget(self.vsource_info)
        vsource_layout.addStretch(1)
        vsource_layout.setSpacing(10)

        self.vsource_gpib = QLineEdit()
        self.vsource_gpib.setText("7")

        gpib_label = QLabel()
        gpib_label.setText("GPIB Address:")

        gpib_layout = QHBoxLayout()
        gpib_layout.addWidget(gpib_label)
        gpib_layout.addWidget(self.vsource_gpib)

        init_layout = QVBoxLayout()
        init_layout.addLayout(connect_layout)
        init_layout.addLayout(vsource_layout)
        init_layout.addLayout(gpib_layout)
        status_VSource.setLayout(init_layout)

        self.voltage_settings = VoltageSettings(TCT_settings=True, check_previous_voltage_settings=check_previous_voltage_settings)

        self.advanced_settings = QGroupBox(title='Advanced Settings')
        self.advanced_settings.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.compliance_value = QDoubleSpinBox()
        self.compliance_value.setRange(0, 1000)
        self.compliance_value.setDecimals(1)
        self.compliance_value.setValue(VSOURCE_COMPLIANCE_DEFAULT)
        self.compliance_value.setSingleStep(1)
        self.compliance_value.setFixedSize(100, 25)
        self.compliance_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        compliance_value_labelbox = add_label_to_input(self.compliance_value, 'Compliance (uA)')

        self.measure_delay = QSpinBox()
        self.measure_delay.setRange(0, 100)
        self.measure_delay.setValue(VSOURCE_MEASURE_DELAY_DEFAULT)
        self.measure_delay.setSingleStep(1)
        self.measure_delay.setFixedSize(100, 25)
        self.measure_delay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        measure_delay_labelbox = add_label_to_input(self.measure_delay, 'Measure Delay (s)')

        adv_set_layout_top = QHBoxLayout()
        adv_set_layout_top.addWidget(compliance_value_labelbox)
        adv_set_layout_top.addWidget(measure_delay_labelbox)

        self.ramping_speed = QSpinBox()
        self.ramping_speed.setRange(0, 100)
        self.ramping_speed.setValue(VSOURCE_RAMPING_SPEED_DEFAULT)
        self.ramping_speed.setSingleStep(1)
        self.ramping_speed.setFixedSize(100, 25)
        self.ramping_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ramping_speed_labelbox = add_label_to_input(self.ramping_speed, 'Ramping Step (V)')

        self.ramping_interval = QDoubleSpinBox()
        self.ramping_interval.setRange(0, 100)
        self.ramping_interval.setValue(VSOURCE_RAMPING_INTERVAL_DEFAULT)
        self.ramping_interval.setSingleStep(1)
        self.ramping_interval.setFixedSize(100, 25)
        self.ramping_interval.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ramping_interval_labelbox = add_label_to_input(self.ramping_interval, 'Ramping Interval (s)')

        adv_set_layout_bottom = QHBoxLayout()
        adv_set_layout_bottom.addWidget(ramping_speed_labelbox)
        adv_set_layout_bottom.addWidget(ramping_interval_labelbox)

        all_adv_layout = QVBoxLayout()
        all_adv_layout.addLayout(adv_set_layout_top)
        all_adv_layout.addSpacing(10)
        all_adv_layout.addLayout(adv_set_layout_bottom)
        self.advanced_settings.setLayout(all_adv_layout)

        layout = QVBoxLayout()
        layout.addWidget(status_VSource)
        layout.addWidget(self.voltage_settings)
        layout.addWidget(self.advanced_settings)
        self.setLayout(layout)

        self.set_vsource_indicator(mode=0)
    
    def set_vsource_indicator(self, mode: int):
        if mode == 0:
            self.vsource_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.vsource_info.setText('No device connected')
            self.vsource_ready = False
        elif mode == 1:
            self.vsource_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.vsource_info.setText('Successfully connected')
            self.vsource_ready = True
        else:
            raise ValueError('The parameter "mode" must be 0 or 1!')