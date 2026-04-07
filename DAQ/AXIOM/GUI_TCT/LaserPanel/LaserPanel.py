from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QTabWidget, QGroupBox, QSpinBox, QCheckBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from os import path
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from DAQ.AXIOM.GUI_TCT.LaserPanel.LaserStageControl import LaserStageControl
from DAQ.AXIOM.GUI_TCT.LaserPanel.LaserPulseWidth import LaserPulseWidth
from DAQ.AXIOM.GUI_TCT.LaserPanel.LaserPulseControl import LaserPulseControl
from config import LASER_FREQ_DEFAULT

 
class LaserPanel(QWidget):
    def __init__(self, checkLaser, setFreq, laserOff, laserDisconnect, laser_reconnect, DACOn, DACOff, setDAC, swap_x_y, move_motors,
                 clear_sequence, load_sequence, start_sequence, set_pulse_duration, enable_ext_interrupts, enable_timer_interrupts, send_seq_period,
                 set_zero, move_x_left, move_x_right, move_y_left, move_y_right, move_z_left, move_z_right, motor_stages_connect, motor_stages_disconnect):
        super().__init__()
        layout = QVBoxLayout()

        self.checkLaser = QPushButton('Refresh')
        self.checkLaser.setFixedSize(50, 20)
        self.checkLaser.clicked.connect(checkLaser)

        status_Laser = QGroupBox(title='Laser Status')
        status_Laser.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.laser_indicator = QLabel('')
        self.laser_indicator.setFixedSize(15, 15)
        self.laser_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.laser_info = QLabel('')
        self.laser_info.setFixedWidth(250)
        self.laser_info.setContentsMargins(3, 3, 3, 3)
        self.laser_info.setStyleSheet('background-color: #FBFBFB;')
        laser_layout = QHBoxLayout()
        laser_layout.addStretch(1)
        laser_layout.addWidget(self.laser_indicator)
        laser_layout.setAlignment(self.laser_indicator, Qt.AlignmentFlag.AlignVCenter)
        laser_layout.addWidget(self.laser_info)
        laser_layout.addStretch(1)
        laser_layout.setSpacing(20)
        laser_widget = QWidget()
        laser_widget.setLayout(laser_layout)
        laser_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.motors_indicator = QLabel('')
        self.motors_indicator.setFixedSize(15, 15)
        self.motors_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.motors_info = QLabel('')
        self.motors_info.setFixedWidth(250)
        self.motors_info.setContentsMargins(3, 3, 3, 3)
        self.motors_info.setStyleSheet('background-color: #FBFBFB;')
        motors_layout = QHBoxLayout()
        motors_layout.addStretch(1)
        motors_layout.addWidget(self.motors_indicator)
        motors_layout.setAlignment(self.motors_indicator, Qt.AlignmentFlag.AlignVCenter)
        motors_layout.addWidget(self.motors_info)
        motors_layout.addStretch(1)
        motors_layout.setSpacing(20)
        motors_widget = QWidget()
        motors_widget.setLayout(motors_layout)
        motors_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.laser_freq_box = QSpinBox()
        self.laser_freq_box.setFixedSize(125, 25)
        self.laser_freq_box.setRange(0, 500000)
        self.laser_freq_box.setSingleStep(100.0)
        self.laser_freq_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.laser_freq_box.setValue(LASER_FREQ_DEFAULT)
        laser_freq_labelbox = add_label_to_input(self.laser_freq_box, 'Laser Frequency (Hz)')

        default_freq = QLabel(f"Default Frequency: {LASER_FREQ_DEFAULT}")

        self.set_freq_button = QPushButton('Set')
        self.set_freq_button.setFixedSize(50, 25)
        self.set_freq_button.clicked.connect(setFreq)

        self.laser_off_button = QPushButton('Off')
        self.laser_off_button.setFixedSize(50, 25)
        self.laser_off_button.clicked.connect(laserOff)
        
        self.laser_disconnect_button = QPushButton('Disconnect')
        self.laser_disconnect_button.setFixedSize(70, 25)
        self.laser_disconnect_button.clicked.connect(laserDisconnect)

        self.laser_reconnect_button = QPushButton('Reconnect')
        self.laser_reconnect_button.setFixedSize(70, 25)
        self.laser_reconnect_button.clicked.connect(laser_reconnect)

        laser_freq_layout = QHBoxLayout()
        laser_freq_layout.addWidget(laser_freq_labelbox)
        laser_freq_layout.addWidget(self.set_freq_button)
        laser_freq_layout.addWidget(self.laser_off_button)
        laser_freq_layout.addWidget(self.laser_disconnect_button)
        laser_freq_layout.addWidget(self.laser_reconnect_button)
        laser_freq_layout.setAlignment(self.set_freq_button, Qt.AlignmentFlag.AlignBottom)
        laser_freq_layout.setAlignment(self.laser_off_button, Qt.AlignmentFlag.AlignBottom)
        laser_freq_layout.setAlignment(self.laser_disconnect_button, Qt.AlignmentFlag.AlignBottom)
        laser_freq_layout.setAlignment(self.laser_reconnect_button, Qt.AlignmentFlag.AlignBottom)
        

        status_layout = QVBoxLayout()
        status_layout.addWidget(laser_widget)
        status_layout.addWidget(motors_widget)
        status_layout.addLayout(laser_freq_layout)
        status_layout.addWidget(default_freq)
        status_layout.setAlignment(default_freq, Qt.AlignmentFlag.AlignHCenter)
        status_Laser.setLayout(status_layout)

        self.Laser_tabs = QTabWidget()
        self.Laser_tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.laser_stage_control = LaserStageControl(swap_x_y=swap_x_y, move_motors=move_motors, set_zero=set_zero, move_x_left=move_x_left, move_x_right=move_x_right, move_y_left=move_y_left, move_y_right=move_y_right, move_z_left=move_z_left, move_z_right=move_z_right,
                                                       motor_stages_connect=motor_stages_connect, motor_stages_disconnect=motor_stages_disconnect)
        self.laser_stage_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.Laser_tabs.addTab(self.laser_stage_control, 'Stage Control')
        self.laser_stage_control.box_same_speed()
        self.laser_pulse_width = LaserPulseWidth(DACOn=DACOn, DACOff=DACOff, setDAC=setDAC)
        self.laser_pulse_width.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.Laser_tabs.addTab(self.laser_pulse_width, 'Pulse Width')
        self.set_DAC_indicator(mode=0)
        self.laser_pulse_width.DAC_off_button.setEnabled(False)
        self.laser_pulse_width.set_DAC_button.setEnabled(False)
        self.laser_pulse_control = LaserPulseControl(clear_sequence=clear_sequence, load_sequence=load_sequence, start_sequence=start_sequence,
                                                       set_pulse_duration=set_pulse_duration, enable_ext_interrupts=enable_ext_interrupts, 
                                                       enable_timer_interrupts=enable_timer_interrupts, send_seq_period=send_seq_period)
        self.laser_pulse_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.laser_pulse_control.setEnabled(False)
        self.Laser_tabs.addTab(self.laser_pulse_control, 'Pulse Control')

        layout.addWidget(self.checkLaser)
        layout.addWidget(status_Laser)
        layout.addWidget(self.Laser_tabs)
        self.setLayout(layout)

    def refresh_laser_stage_tab(self, swap_x_y, move_motors, set_zero, move_x_left, move_x_right, move_y_left, move_y_right, move_z_left, move_z_right,
                                                       motor_stages_connect, motor_stages_disconnect):
        # Remove the current TCT_laser tab
        self.Laser_tabs.removeTab(self.Laser_tabs.indexOf(self.laser_stage_control))
        
        # Recreate the TCT_laser instance
        self.laser_stage_control = LaserStageControl(swap_x_y=swap_x_y, move_motors=move_motors, set_zero=set_zero, move_x_left=move_x_left, move_x_right=move_x_right, move_y_left=move_y_left, move_y_right=move_y_right, move_z_left=move_z_left, move_z_right=move_z_right,
                                                       motor_stages_connect=motor_stages_connect, motor_stages_disconnect=motor_stages_disconnect)
        
        # Add the refreshed tab back to the tabs
        self.Laser_tabs.insertTab(0, self.laser_stage_control, 'Laser')
        self.Laser_tabs.setCurrentIndex(0)

    def set_laser_indicator(self, mode: int):
        if mode == 1:
            self.laser_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.laser_info.setText('Laser is turned on')
            self.laser_ready = True
        elif mode == 2:
            self.laser_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.laser_info.setText('Laser on standby')
            self.laser_ready = False
        elif mode == 4:
            self.laser_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.laser_info.setText('No laser connected!')
            self.laser_ready = False
        else:
            raise ValueError('The parameter "mode" must be 1, 2, or 4!')

    def set_motors_indicator(self, mode: int):
        if mode == 3: 
            self.motors_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.motors_info.setText('All stage motors are connected')
        elif mode == 2 or mode == 1:
            self.motors_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.motors_info.setText('1 or more stage motors are not connected!')
        elif mode == 0:
            self.motors_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.motors_info.setText('No stage motors detected!')
        else:
            raise ValueError('The parameter "mode" must be 1, 2, 3, or 4!')

    def set_DAC_indicator(self, mode: int):
        if mode == 1:
            self.laser_pulse_width.DAC_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.laser_pulse_width.DAC_info.setText('DAC is enabled')
        elif mode == 0:
            self.laser_pulse_width.DAC_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.laser_pulse_width.DAC_info.setText('DAC is disabled')
        else:
            raise ValueError('The parameter "mode" must be 0 or 1!')   