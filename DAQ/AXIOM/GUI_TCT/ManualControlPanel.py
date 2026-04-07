from PySide6.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QGroupBox, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from DAQ.AXIOM.Utils.Plot.TCTPlot import TCTPlot

class ManualControlPanel(QWidget): 
    def __init__(self, vbias_set, vbias_set_0, vbias_set_neg6, vbias_set_neg600,
                osc_on, osc_off, move_x_left=None, move_x_right=None, 
                 move_y_left=None, move_y_right=None):
        super().__init__()

        set_VBias = QGroupBox(title='Voltage Source Init')
        set_VBias.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        set_VBias.setFixedHeight(250)

        # Create motor control buttons for vbias layout
        self.vbias_x_left = QPushButton('<---')
        self.vbias_x_left.setFixedSize(60, 25)
        if move_x_left:
            self.vbias_x_left.clicked.connect(move_x_left)
        
        self.vbias_x_right = QPushButton('--->')
        self.vbias_x_right.setFixedSize(60, 25)
        if move_x_right:
            self.vbias_x_right.clicked.connect(move_x_right)
        
        self.vbias_y_left = QPushButton('<---')
        self.vbias_y_left.setFixedSize(60, 25)
        if move_y_left:
            self.vbias_y_left.clicked.connect(move_y_left)
        
        self.vbias_y_right = QPushButton('--->')
        self.vbias_y_right.setFixedSize(60, 25)
        if move_y_right:
            self.vbias_y_right.clicked.connect(move_y_right)
        
        # Create a grid for motor controls
        motors_grid = QGridLayout()
        motors_grid.setHorizontalSpacing(15)
        motors_grid.setVerticalSpacing(10)

        self.x_axis_indicator = QLabel('')
        self.x_axis_indicator.setFixedSize(15, 15)
        self.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')

        self.x_axis_position_step = QSpinBox()
        self.x_axis_position_step.setFixedSize(50, 25)
        self.x_axis_position_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.x_axis_position_step.setRange(-5000, 5000)
        self.x_axis_position_step.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)

        self.y_axis_indicator = QLabel('')
        self.y_axis_indicator.setFixedSize(15, 15)
        self.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')

        self.y_axis_position_step = QSpinBox()
        self.y_axis_position_step.setFixedSize(50, 25)
        self.y_axis_position_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.y_axis_position_step.setRange(-5000, 5000)
        self.y_axis_position_step.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)


        motors_grid.addWidget(self.x_axis_indicator, 0, 0)
        motors_grid.addWidget(self.vbias_x_left, 0, 1)
        motors_grid.addWidget(self.vbias_x_right, 0, 2)
        motors_grid.addWidget(QLabel("X-axis position: "), 0, 3)
        motors_grid.addWidget(self.x_axis_position_step, 0, 4)
        motors_grid.addWidget(self.y_axis_indicator, 1, 0)
        motors_grid.addWidget(self.vbias_y_left, 1, 1)
        motors_grid.addWidget(self.vbias_y_right, 1, 2)
        motors_grid.addWidget(QLabel("Y-axis position: "), 1, 3)
        motors_grid.addWidget(self.y_axis_position_step, 1, 4)
        motors_grid.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a widget for motors grid
        motors_widget = QWidget()
        motors_widget.setLayout(motors_grid)


        # Add vbias control
        # Add the most common vbias settings as buttons
        self.vbias_set_0_button = QPushButton('Set 0')
        self.vbias_set_0_button.setFixedSize(70, 25)
        self.vbias_set_0_button.clicked.connect(vbias_set_0)

        self.vbias_set_neg6_button = QPushButton('Set -6')
        self.vbias_set_neg6_button.setFixedSize(70, 25)
        self.vbias_set_neg6_button.clicked.connect(vbias_set_neg6)

        self.vbias_set_neg600_button = QPushButton('Set -600')
        self.vbias_set_neg600_button.setFixedSize(70, 25)
        self.vbias_set_neg600_button.clicked.connect(vbias_set_neg600)

        self.vbias = QSpinBox()
        self.vbias.setRange(-1000, 1000)
        self.vbias.setValue(0)
        self.vbias.setSingleStep(1)
        self.vbias.setFixedSize(100, 25)
        self.vbias.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbias_labelbox = add_label_to_input(self.vbias, 'Vbias [V]')

        self.vbias_set = QPushButton('Set')
        self.vbias_set.setFixedSize(70, 25)
        self.vbias_set.clicked.connect(vbias_set)

        vbias_layout = QHBoxLayout()
        vbias_layout.addStretch(0.5)
        vbias_layout.addWidget(self.vbias_set_0_button)
        vbias_layout.addStretch(0.5)
        vbias_layout.addWidget(self.vbias_set_neg6_button)
        vbias_layout.addStretch(0.5)
        vbias_layout.addWidget(self.vbias_set_neg600_button)
        vbias_layout.addStretch(0.5)
        vbias_layout.addWidget(vbias_labelbox)
        vbias_layout.addStretch(0.5)
        vbias_layout.addWidget(self.vbias_set)
        vbias_layout.addStretch(0.5)

        vbias_layout.setAlignment(vbias_labelbox, Qt.AlignmentFlag.AlignBottom)
        vbias_layout.setAlignment(self.vbias_set, Qt.AlignmentFlag.AlignBottom)
        vbias_layout.setAlignment(self.vbias_set_0_button, Qt.AlignmentFlag.AlignBottom)
        vbias_layout.setAlignment(self.vbias_set_neg6_button, Qt.AlignmentFlag.AlignBottom)
        vbias_layout.setAlignment(self.vbias_set_neg600_button, Qt.AlignmentFlag.AlignBottom)

        osc_label = QLabel()
        osc_label.setText("Toggle Oscilloscope:")

        self.osc_on = QPushButton('On')
        self.osc_on.setFixedSize(70, 25)
        self.osc_on.clicked.connect(osc_on)

        self.osc_off = QPushButton('Off')
        self.osc_off.setFixedSize(70, 25)
        self.osc_off.clicked.connect(osc_off)

        osc_layout = QHBoxLayout()
        osc_layout.addWidget(osc_label)
        osc_layout.setAlignment(osc_label, Qt.AlignmentFlag.AlignCenter)
        osc_layout.addWidget(self.osc_on)
        osc_layout.setAlignment(self.osc_on, Qt.AlignmentFlag.AlignCenter)
        osc_layout.addWidget(self.osc_off)
        osc_layout.setAlignment(self.osc_off, Qt.AlignmentFlag.AlignCenter)

        init_layout = QVBoxLayout()
        init_layout.addWidget(motors_widget)
        init_layout.addLayout(vbias_layout)
        init_layout.addLayout(osc_layout)
        set_VBias.setLayout(init_layout)

        self.results_canvas = TCTPlot()
        self.results_canvas.ax.set_title('TCT Plot')
        self.results_canvas.ax.set_xlabel('Time (s)')
        self.results_canvas.ax.set_ylabel('Voltage (V)')

        self.voltage_ramp_status = QLabel("Status: " + "-", self)
        self.display_curr = QLabel("Current(A): " + "-", self)

        layout = QVBoxLayout()
        layout.addWidget(set_VBias)
        layout.setAlignment(set_VBias, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.voltage_ramp_status)
        layout.addWidget(self.display_curr)
        layout.addWidget(self.results_canvas)
        self.setLayout(layout)

        self.osc_off.setEnabled(False)
        
        # Set manual control status to prevent vbias to nonzero values and oscilloscope to be on when running CV/IV measurements
        self.manual_control_status(device = "osc", mode = 0)
        self.manual_control_status(device = "vbias", mode = 0)
    
    def manual_control_status(self, device, mode : int):
        if device == "osc":
            self.osc_toggle_status = "off" if mode == 0 else "on"
        elif device == "vbias":
            self.vbias_status = "zero" if mode == 0 else "nonzero"
            