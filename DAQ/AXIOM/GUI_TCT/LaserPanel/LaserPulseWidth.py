from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QTabWidget, QGroupBox, QSpinBox, QCheckBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from os import path
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from config import LASER_PULSE_WIDTH_PERCENT_DEFAULT

class LaserPulseWidth(QWidget): 
    def __init__(self, DACOn, DACOff, setDAC):
        super().__init__()
        layout = QVBoxLayout()

        status_DAC = QGroupBox(title='DAC Status')
        status_DAC.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.DAC_indicator = QLabel('')
        self.DAC_indicator.setFixedSize(15, 15)
        self.DAC_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.DAC_info = QLabel('')
        self.DAC_info.setFixedWidth(250)
        self.DAC_info.setContentsMargins(3, 3, 3, 3)
        self.DAC_info.setStyleSheet('background-color: #FBFBFB;')
        DAC_layout = QHBoxLayout()
        DAC_layout.addStretch(1)
        DAC_layout.addWidget(self.DAC_indicator)
        DAC_layout.setAlignment(self.DAC_indicator, Qt.AlignmentFlag.AlignVCenter)
        DAC_layout.addWidget(self.DAC_info)
        DAC_layout.addStretch(1)
        DAC_layout.setSpacing(20)
        DAC_widget = QWidget()
        DAC_widget.setLayout(DAC_layout)
        DAC_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.DAC_on_button = QPushButton('On')
        self.DAC_on_button.setFixedSize(50, 25)
        self.DAC_on_button.clicked.connect(DACOn)

        self.DAC_off_button = QPushButton('Off')
        self.DAC_off_button.setFixedSize(50, 25)
        self.DAC_off_button.clicked.connect(DACOff)

        toggle_DAC_layout = QHBoxLayout()
        toggle_DAC_layout.addWidget(self.DAC_on_button)
        toggle_DAC_layout.addWidget(self.DAC_off_button)
        toggle_DAC_layout.setAlignment(self.DAC_on_button, Qt.AlignmentFlag.AlignHCenter)
        toggle_DAC_layout.setAlignment(self.DAC_off_button, Qt.AlignmentFlag.AlignHCenter)

        status_layout = QVBoxLayout()
        status_layout.addWidget(DAC_widget)
        status_layout.addLayout(toggle_DAC_layout)
        status_DAC.setLayout(status_layout)

        self.set_DAC_box = QDoubleSpinBox()
        self.set_DAC_box.setFixedSize(125, 25)
        self.set_DAC_box.setRange(0, 100) # Since we using percentage
        self.set_DAC_box.setDecimals(1)
        self.set_DAC_box.setValue(LASER_PULSE_WIDTH_PERCENT_DEFAULT)
        # self.set_DAC_box.setSuffix("%")
        self.set_DAC_box.setSingleStep(1.0)
        #self.set_DAC_box.setValue(temp_config['chiller_setpoint']) this gets it from the json file, not yet done for laser
        # set_DAC_labelbox = add_label_to_input(self.set_DAC_box, 'Laser Pulse Width\n(0mV-3300mV)')
        set_DAC_labelbox = add_label_to_input(self.set_DAC_box, 'Laser Pulse Width [0-100%]')

        self.set_DAC_button = QPushButton('Set')
        self.set_DAC_button.setFixedSize(50, 25)
        self.set_DAC_button.clicked.connect(setDAC)

        set_DAC_layout = QHBoxLayout()
        set_DAC_layout.addWidget(set_DAC_labelbox)
        set_DAC_layout.addWidget(self.set_DAC_button)
        set_DAC_layout.setAlignment(self.set_DAC_button, Qt.AlignmentFlag.AlignBottom)
        set_DAC_layout.setAlignment(set_DAC_labelbox, Qt.AlignmentFlag.AlignBottom)

        self.DAC_mV = QLabel("0 mV", self)

        layout.addWidget(status_DAC)
        layout.addLayout(set_DAC_layout)
        layout.addWidget(self.DAC_mV)
        layout.setAlignment(set_DAC_layout, Qt.AlignmentFlag.AlignCenter)
        layout.setAlignment(self.DAC_mV, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)   