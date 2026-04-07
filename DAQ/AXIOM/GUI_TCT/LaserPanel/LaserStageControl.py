from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QTabWidget, QGroupBox, QSpinBox, QCheckBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from os import path
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from config import LASER_STEP_SIZE_DEFAULT

class LaserStageControl(QWidget): 
    def __init__(self, swap_x_y, move_motors, set_zero, move_x_left, move_x_right, move_y_left, move_y_right, move_z_left, move_z_right, motor_stages_connect, motor_stages_disconnect):
        super().__init__()

        self.move_stage_button = QPushButton('MOVE ALL MOTORS')
        self.move_stage_button.setFixedSize(150, 25)
        self.move_stage_button.clicked.connect(move_motors)

        self.swap_stage_button = QPushButton('Swap X/Y')
        self.swap_stage_button.setFixedSize(70, 25)
        self.swap_stage_button.clicked.connect(swap_x_y)

        self.set_zero_button = QPushButton('Set 0')
        self.set_zero_button.setFixedSize(70, 25)
        self.set_zero_button.clicked.connect(set_zero)

        self.motor_stages_connect_button = QPushButton('Connect')
        self.motor_stages_connect_button.setFixedSize(70, 25)
        self.motor_stages_connect_button.clicked.connect(motor_stages_connect)

        self.motor_stages_disconnect_button = QPushButton('Disconnect')
        self.motor_stages_disconnect_button.setFixedSize(70, 25)
        self.motor_stages_disconnect_button.clicked.connect(motor_stages_disconnect)

        stage_layout = QHBoxLayout()
        stage_layout.addWidget(self.motor_stages_connect_button)
        stage_layout.addStretch()
        stage_layout.addWidget(self.motor_stages_disconnect_button)
        stage_layout.addStretch()
        stage_layout.addWidget(self.set_zero_button)
        stage_layout.addStretch()
        stage_layout.addWidget(self.swap_stage_button)
        stage_layout.addStretch()
        stage_layout.addWidget(self.move_stage_button)

        self.speed_checkbox = QCheckBox('Same Speed', self)
        self.speed_checkbox.setChecked(True)
        self.speed_checkbox.stateChanged.connect(self.box_same_speed)

        self.set_same_speed = QSpinBox()
        self.set_same_speed.setFixedSize(125, 25)
        self.set_same_speed.setRange(0, 500000)
        self.set_same_speed.setSingleStep(100.0)
        self.set_same_speed.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        set_speed_labelbox = add_label_to_input(self.set_same_speed, 'Motor Speed')

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(self.speed_checkbox)
        speed_layout.addWidget(set_speed_labelbox)
    
        # START X AXIS BOX
        x_axis_motor = QGroupBox(title='X axis')
        x_axis_motor.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.x_axis_indicator = QLabel('')
        self.x_axis_indicator.setFixedSize(15, 15)
        self.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')

        x_indicator_layout = QVBoxLayout()
        x_indicator_layout.addWidget(self.x_axis_indicator)
        x_indicator_layout.setAlignment(self.x_axis_indicator, Qt.AlignmentFlag.AlignLeft)

        self.x_from = QLabel("Position: " + "0" + " steps, " + "0" + " microsteps", self)
        
        x_from_layout = QHBoxLayout()
        x_from_layout.addWidget(self.x_from)
        x_from_layout.setAlignment(self.x_from, Qt.AlignmentFlag.AlignVCenter)

        x_to = QLabel("To: ")
        self.set_x_step = QSpinBox()
        self.set_x_step.setRange(-5000, 5000)
        self.set_x_step.setSingleStep(10.0)
        x_steps = QLabel("steps")
        self.set_x_ustep = QSpinBox()
        self.set_x_ustep.setRange(-100, 100)
        self.set_x_ustep.setSingleStep(10.0)
        x_microsteps = QLabel("microsteps")
        
        x_to_layout = QHBoxLayout()
        x_to_layout.addWidget(x_to)
        x_to_layout.addWidget(self.set_x_step)
        x_to_layout.addWidget(x_steps)
        x_to_layout.addWidget(self.set_x_ustep)
        x_to_layout.addWidget(x_microsteps)

        x_speed = QLabel("Speed: ")
        self.set_x_speed = QSpinBox()
        self.set_x_speed.setRange(0, 5000)
        self.set_x_speed.setSingleStep(10.0)
        
        x_speed_layout = QHBoxLayout()
        x_speed_layout.addWidget(x_speed)
        x_speed_layout.addWidget(self.set_x_speed)

        x_move_layout = QVBoxLayout()
        x_move_layout.addLayout(x_from_layout)
        x_move_layout.addLayout(x_to_layout)
        x_move_layout.addLayout(x_speed_layout)

        self.move_x_left = QPushButton('<--')
        self.move_x_left.setFixedSize(70, 25)
        self.move_x_left.clicked.connect(move_x_left)

        self.move_x_right = QPushButton('-->')
        self.move_x_right.setFixedSize(70, 25)
        self.move_x_right.clicked.connect(move_x_right)

        self.x_step_size = QSpinBox()
        self.x_step_size.setRange(0, 5000)
        self.x_step_size.setSingleStep(10.0)
        self.x_step_size.setValue(LASER_STEP_SIZE_DEFAULT)
        x_step_size_labelbox = add_label_to_input(self.x_step_size, 'Step Size')

        x_axis_layout = QHBoxLayout()
        x_axis_layout.addLayout(x_indicator_layout)
        x_axis_layout.addWidget(x_step_size_labelbox)
        x_axis_layout.setAlignment(x_step_size_labelbox, Qt.AlignmentFlag.AlignCenter)
        x_axis_layout.addWidget(self.move_x_left)
        x_axis_layout.setAlignment(self.move_x_left, Qt.AlignmentFlag.AlignCenter)
        x_axis_layout.addWidget(self.move_x_right)
        x_axis_layout.setAlignment(self.move_x_right, Qt.AlignmentFlag.AlignCenter)
        x_axis_layout.addLayout(x_move_layout)
        x_axis_motor.setLayout(x_axis_layout)
        # END X AXIS BOX

        # START Y AXIS BOX
        y_axis_motor = QGroupBox(title='Y axis')
        y_axis_motor.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.y_axis_indicator = QLabel('')
        self.y_axis_indicator.setFixedSize(15, 15)
        self.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')

        y_indicator_layout = QVBoxLayout()
        y_indicator_layout.addWidget(self.y_axis_indicator)
        y_indicator_layout.setAlignment(self.y_axis_indicator, Qt.AlignmentFlag.AlignLeft)

        self.y_from = QLabel("Position: " + "0" + " steps, " + "0" + " microsteps", self)
        
        y_from_layout = QHBoxLayout()
        y_from_layout.addWidget(self.y_from)
        y_from_layout.setAlignment(self.y_from, Qt.AlignmentFlag.AlignVCenter)

        y_to = QLabel("To: ")
        self.set_y_step = QSpinBox()
        self.set_y_step.setRange(-5000, 5000)
        self.set_y_step.setSingleStep(10.0)
        y_steps = QLabel("steps")
        self.set_y_ustep = QSpinBox()
        self.set_y_ustep.setRange(-100, 100)
        self.set_y_ustep.setSingleStep(10.0)
        y_microsteps = QLabel("microsteps")
        
        y_to_layout = QHBoxLayout()
        y_to_layout.addWidget(y_to)
        y_to_layout.addWidget(self.set_y_step)
        y_to_layout.addWidget(y_steps)
        y_to_layout.addWidget(self.set_y_ustep)
        y_to_layout.addWidget(y_microsteps)

        y_speed = QLabel("Speed: ")
        self.set_y_speed = QSpinBox()
        self.set_y_speed.setRange(0, 5000)
        self.set_y_speed.setSingleStep(10.0)
        
        y_speed_layout = QHBoxLayout()
        y_speed_layout.addWidget(y_speed)
        y_speed_layout.addWidget(self.set_y_speed)

        y_move_layout = QVBoxLayout()
        y_move_layout.addLayout(y_from_layout)
        y_move_layout.addLayout(y_to_layout)
        y_move_layout.addLayout(y_speed_layout)

        self.move_y_left = QPushButton('<--')
        self.move_y_left.setFixedSize(70, 25)
        self.move_y_left.clicked.connect(move_y_left)

        self.move_y_right = QPushButton('-->')
        self.move_y_right.setFixedSize(70, 25)
        self.move_y_right.clicked.connect(move_y_right)

        self.y_step_size = QSpinBox()
        self.y_step_size.setRange(0, 5000)
        self.y_step_size.setSingleStep(10.0)
        self.y_step_size.setValue(LASER_STEP_SIZE_DEFAULT)
        y_step_size_labelbox = add_label_to_input(self.y_step_size, 'Step Size')

        y_axis_layout = QHBoxLayout()
        y_axis_layout.addLayout(y_indicator_layout)
        y_axis_layout.addWidget(y_step_size_labelbox)
        y_axis_layout.setAlignment(y_step_size_labelbox, Qt.AlignmentFlag.AlignCenter)
        y_axis_layout.addWidget(self.move_y_left)
        y_axis_layout.setAlignment(self.move_y_left, Qt.AlignmentFlag.AlignCenter)
        y_axis_layout.addWidget(self.move_y_right)
        y_axis_layout.setAlignment(self.move_y_right, Qt.AlignmentFlag.AlignCenter)
        y_axis_layout.addLayout(y_move_layout)
        y_axis_motor.setLayout(y_axis_layout)
        # END Y AXIS BOX

        # START Z AXIS BOX
        z_axis_motor = QGroupBox(title='Z axis')
        z_axis_motor.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.z_axis_indicator = QLabel('')
        self.z_axis_indicator.setFixedSize(15, 15)
        self.z_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')

        z_indicator_layout = QVBoxLayout()
        z_indicator_layout.addWidget(self.z_axis_indicator)
        z_indicator_layout.setAlignment(self.z_axis_indicator, Qt.AlignmentFlag.AlignLeft)

        self.z_from = QLabel("Position: " + "0" + " steps, " + "0" + " microsteps", self)
        
        z_from_layout = QHBoxLayout()
        z_from_layout.addWidget(self.z_from)
        z_from_layout.setAlignment(self.z_from, Qt.AlignmentFlag.AlignVCenter)

        z_to = QLabel("To: ")
        self.set_z_step = QSpinBox()
        self.set_z_step.setRange(-5000, 5000)
        self.set_z_step.setSingleStep(10.0)
        z_steps = QLabel("steps")
        self.set_z_ustep = QSpinBox()
        self.set_z_ustep.setRange(-100, 100)
        self.set_z_ustep.setSingleStep(10.0)
        z_microsteps = QLabel("microsteps")
        
        z_to_layout = QHBoxLayout()
        z_to_layout.addWidget(z_to)
        z_to_layout.addWidget(self.set_z_step)
        z_to_layout.addWidget(z_steps)
        z_to_layout.addWidget(self.set_z_ustep)
        z_to_layout.addWidget(z_microsteps)

        z_speed = QLabel("Speed: ")
        self.set_z_speed = QSpinBox()
        self.set_z_speed.setRange(0, 5000)
        self.set_z_speed.setSingleStep(10.0)
        
        z_speed_layout = QHBoxLayout()
        z_speed_layout.addWidget(z_speed)
        z_speed_layout.addWidget(self.set_z_speed)

        z_move_layout = QVBoxLayout()
        z_move_layout.addLayout(z_from_layout)
        z_move_layout.addLayout(z_to_layout)
        z_move_layout.addLayout(z_speed_layout)

        self.move_z_left = QPushButton('<--')
        self.move_z_left.setFixedSize(70, 25)
        self.move_z_left.clicked.connect(move_z_left)

        self.move_z_right = QPushButton('-->')
        self.move_z_right.setFixedSize(70, 25)
        self.move_z_right.clicked.connect(move_z_right)

        self.z_step_size = QSpinBox()
        self.z_step_size.setRange(0, 5000)
        self.z_step_size.setSingleStep(10.0)
        self.z_step_size.setValue(LASER_STEP_SIZE_DEFAULT)
        z_step_size_labelbox = add_label_to_input(self.z_step_size, 'Step Size')

        z_axis_layout = QHBoxLayout()
        z_axis_layout.addLayout(z_indicator_layout)
        z_axis_layout.addWidget(z_step_size_labelbox)
        z_axis_layout.setAlignment(z_step_size_labelbox, Qt.AlignmentFlag.AlignCenter)
        z_axis_layout.addWidget(self.move_z_left)
        z_axis_layout.setAlignment(self.move_z_left, Qt.AlignmentFlag.AlignCenter)
        z_axis_layout.addWidget(self.move_z_right)
        z_axis_layout.setAlignment(self.move_z_right, Qt.AlignmentFlag.AlignCenter)
        z_axis_layout.addLayout(z_move_layout)
        z_axis_motor.setLayout(z_axis_layout)
        # END Z AXIS BOX

        layout = QVBoxLayout()
        layout.addLayout(stage_layout)
        layout.addLayout(speed_layout)
        layout.addWidget(x_axis_motor)
        layout.addWidget(y_axis_motor)
        layout.addWidget(z_axis_motor)
        layout.addStretch(1)
        self.setLayout(layout)

    def box_same_speed(self):
        if self.speed_checkbox.isChecked() == True:
            self.set_same_speed.setEnabled(True)
            self.set_x_speed.setEnabled(False)
            self.set_y_speed.setEnabled(False)
            self.set_z_speed.setEnabled(False)
        elif self.speed_checkbox.isChecked() == False:
            self.set_same_speed.setEnabled(False)
            self.set_x_speed.setEnabled(True)
            self.set_y_speed.setEnabled(True)
            self.set_z_speed.setEnabled(True)