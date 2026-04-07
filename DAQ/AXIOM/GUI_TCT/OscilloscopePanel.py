from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QSpinBox, QGroupBox, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
import pyvisa as visa # http://github.com/hgrecco/pyvisa
from config import WF_PER_VBIAS_DEFAULT, POINTS_PER_WF_DEFAULT, OSCILLOSCOPE_RECALL_DEFAULT

 
class OscilloscopePanel(QWidget):
    def __init__(self, osc_connect, osc_disconnect, recall_setup, save_setup):
        super().__init__()

        status_Osc = QGroupBox(title='Oscilloscope Init')
        status_Osc.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.osc_connect = QPushButton('Connect')
        self.osc_connect.setFixedSize(70, 25)
        self.osc_connect.clicked.connect(osc_connect)

        self.osc_disconnect = QPushButton('Disconnect')
        self.osc_disconnect.setFixedSize(70, 25)
        self.osc_disconnect.clicked.connect(osc_disconnect)

        connect_layout = QHBoxLayout()
        connect_layout.addWidget(self.osc_connect)
        connect_layout.setAlignment(self.osc_connect, Qt.AlignmentFlag.AlignCenter)
        connect_layout.addWidget(self.osc_disconnect)
        connect_layout.setAlignment(self.osc_disconnect, Qt.AlignmentFlag.AlignCenter)

        self.osc_indicator = QLabel('')
        self.osc_indicator.setFixedSize(15, 15)
        self.osc_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.osc_info = QLabel('')
        self.osc_info.setFixedWidth(250)
        self.osc_info.setContentsMargins(3, 3, 3, 3)
        self.osc_info.setStyleSheet('background-color: #FBFBFB;')
        osc_layout = QHBoxLayout()
        osc_layout.addStretch(1)
        osc_layout.addWidget(self.osc_indicator)
        osc_layout.setAlignment(self.osc_indicator, Qt.AlignmentFlag.AlignVCenter)
        osc_layout.addWidget(self.osc_info)
        osc_layout.addStretch(1)
        osc_layout.setSpacing(10)

        rm = visa.ResourceManager()
        devices = rm.list_resources()
        self.osc_visa = QComboBox()
        self.osc_visa.addItems(devices)

        #rm = visa.ResourceManager()
        #devices = rm.list_resources()
        #self.osc_visa = QComboBox()
        #self.osc_visa.addItems(devices)

        visa_label = QLabel()
        visa_label.setText("Visa Address:")

        visa_layout = QHBoxLayout()
        visa_layout.addWidget(visa_label)
        visa_layout.addWidget(self.osc_visa)

        init_layout = QVBoxLayout()
        init_layout.addLayout(connect_layout)
        init_layout.addLayout(osc_layout)
        init_layout.addLayout(visa_layout)
        status_Osc.setLayout(init_layout)

        measurement_settings = QGroupBox(title='Measurement Settings')
        measurement_settings.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.wf_per_vbias = QSpinBox()
        self.wf_per_vbias.setFixedSize(125, 25)
        self.wf_per_vbias.setRange(0, 500000)
        self.wf_per_vbias.setSingleStep(10)
        self.wf_per_vbias.setValue(WF_PER_VBIAS_DEFAULT)
        self.wf_per_vbias.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        #self.set_same_speed.setValue(temp_config['chiller_setpoint']) this gets it from the json file, not yet done for laser
        wf_per_vibas_labelbox = add_label_to_input(self.wf_per_vbias, 'WF/VBias')

        self.points_per_wf = QSpinBox()
        self.points_per_wf.setFixedSize(125, 25)
        self.points_per_wf.setRange(0, 500000)
        self.points_per_wf.setSingleStep(10)
        self.points_per_wf.setValue(POINTS_PER_WF_DEFAULT)
        self.points_per_wf.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        #self.set_same_speed.setValue(temp_config['chiller_setpoint']) this gets it from the json file, not yet done for laser
        points_per_wf_labelbox = add_label_to_input(self.points_per_wf, 'Points/WF')

        # Allowing to read more channels. Track for TCT and beam monitor   
        channels_layout = QHBoxLayout()
        channels_layout.addSpacing(1)

        # Add first channel record to track TCT values
        self.record_channel = QComboBox()
        self.record_channel.addItem("CH1") # for TCT
        self.record_channel.addItem("CH2") # for beam monitor 
        self.record_channel.addItem("CH3")
        self.record_channel.addItem("CH4")
        record_channel_labelbox = add_label_to_input(self.record_channel, "TCT")
        channels_layout.addWidget(record_channel_labelbox)
        channels_layout.addSpacing(1)
        
        # Add checkbox to enable/disable beam monitor 
        self.checkbox_second_record_channel = QCheckBox()
        self.checkbox_second_record_channel.setChecked(True)
        checkbox_second_record_channel_labelbox = add_label_to_input(self.checkbox_second_record_channel, "Enable/Disable\nBeam Monitor")
        channels_layout.addWidget(checkbox_second_record_channel_labelbox)
        self.checkbox_second_record_channel.toggled.connect(self.enable_disable_second_record_channel)

        # Add second channel to record beam monitor
        self.second_record_channel = QComboBox()
        self.add_second_record_channel_items()
        second_record_channel_labelbox = add_label_to_input(self.second_record_channel, "Beam monitor")
        channels_layout.addWidget(second_record_channel_labelbox)
        channels_layout.addSpacing(1)

        self.recall_setup = QPushButton('Recall')
        self.recall_setup.setFixedSize(70, 25)
        self.recall_setup.clicked.connect(recall_setup)

        self.save_setup = QPushButton('Save')
        self.save_setup.setFixedSize(70, 25)
        self.save_setup.clicked.connect(save_setup)

        self.setup_name = QLineEdit()
        self.setup_name.setText(OSCILLOSCOPE_RECALL_DEFAULT)

        setup_label = QLabel()
        setup_label.setText("Setup name:")

        recall_layout = QHBoxLayout()
        recall_layout.addWidget(setup_label)
        recall_layout.addWidget(self.setup_name)
        recall_layout.addWidget(self.recall_setup)
        recall_layout.addWidget(self.save_setup)

        settings_layout = QVBoxLayout()
        settings_layout.addWidget(wf_per_vibas_labelbox)
        settings_layout.setAlignment(wf_per_vibas_labelbox, Qt.AlignmentFlag.AlignHCenter)
        settings_layout.addWidget(points_per_wf_labelbox)
        settings_layout.setAlignment(points_per_wf_labelbox, Qt.AlignmentFlag.AlignHCenter)
        # settings_layout.addWidget(self.record_channel)
        # settings_layout.setAlignment(self.record_channel, Qt.AlignmentFlag.AlignHCenter)
        settings_layout.addLayout(channels_layout)
        # settings_layout.setAlignment(channels_layout, Qt.AlignmentFlag.AlignHCenter)
        settings_layout.addLayout(recall_layout)
        settings_layout.setAlignment(recall_layout, Qt.AlignmentFlag.AlignHCenter)
        measurement_settings.setLayout(settings_layout)

        layout = QVBoxLayout()
        layout.addWidget(status_Osc)
        layout.addWidget(measurement_settings)
        self.setLayout(layout)

        self.set_osc_indicator(mode=0)

    def set_osc_indicator(self, mode: int):
        if mode == 0:
            self.osc_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.osc_info.setText('No device connected')
            self.osc_ready = False
        elif mode == 1:
            self.osc_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.osc_info.setText('Successfully connected')
            self.osc_ready = True
        elif mode == 2:
            self.osc_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.osc_info.setText('Successfully saved settings')
            self.osc_ready = True
        elif mode == 3:
            self.osc_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.osc_info.setText('Successfully recalled settings')
            self.osc_ready = True
        else:
            raise ValueError('The parameter "mode" must be 0, 1, 2 or 3!')
        
    def add_second_record_channel_items(self):
        self.second_record_channel.addItem("CH1") 
        self.second_record_channel.addItem("CH2")
        self.second_record_channel.addItem("CH3")
        self.second_record_channel.addItem("CH4")
        self.second_record_channel.setCurrentIndex(1)

    def enable_disable_second_record_channel(self, enabled):
        if not enabled:
            self.second_record_channel.setEnabled(False)
            self.second_record_channel.clear()
            self.second_record_channel.addItem("")
        else:
            self.second_record_channel.setEnabled(True)
            self.second_record_channel.clear()
            self.add_second_record_channel_items()