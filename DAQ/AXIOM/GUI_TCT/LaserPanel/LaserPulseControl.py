from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QTabWidget, QGroupBox, QSpinBox, QCheckBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from os import path
from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input

class LaserPulseControl(QWidget): 
    def __init__(self, clear_sequence, load_sequence, start_sequence, set_pulse_duration, enable_ext_interrupts, enable_timer_interrupts, send_seq_period):
        super().__init__()
        layout = QVBoxLayout()

        self.def_file_info = QLabel('Default File: streamFile.txt')
        self.set_seq_info = QLabel('')

        file_sequence = QGroupBox(title='Sequence from file')
        file_sequence.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.clear_sequence = QPushButton('Clear Sequence')
        self.clear_sequence.setFixedSize(90, 30)
        self.clear_sequence.clicked.connect(clear_sequence)

        self.load_sequence = QPushButton('Load Sequence')
        self.load_sequence.setFixedSize(90, 30)
        self.clear_sequence.clicked.connect(load_sequence)

        self.start_sequence = QPushButton('Start Sequence')
        self.start_sequence.setFixedSize(90, 30)
        self.clear_sequence.clicked.connect(start_sequence)

        set_seq_buttons = QHBoxLayout()
        set_seq_buttons.addWidget(self.clear_sequence)
        set_seq_buttons.addWidget(self.load_sequence)
        set_seq_buttons.addWidget(self.start_sequence)
        set_seq_buttons.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        pulse_label = QLabel("Pulse Duration:")
        self.pulse_duration = QSpinBox()
        self.pulse_duration.setRange(0, 10000)
        self.pulse_duration.setSingleStep(10.0)
        _pulse_label = QLabel(" [ns]")

        self.set_pulse_duration = QPushButton('Set Pulse\nDuration')
        self.set_pulse_duration.setFixedSize(90, 40)
        self.set_pulse_duration.clicked.connect(set_pulse_duration)

        set_pulse_dur = QHBoxLayout()
        set_pulse_dur.addWidget(pulse_label)
        set_pulse_dur.addWidget(self.pulse_duration)
        set_pulse_dur.addWidget(_pulse_label)
        set_pulse_dur.addWidget(self.set_pulse_duration)
        set_pulse_dur.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        file_sequence_box = QVBoxLayout()
        file_sequence_box.addLayout(set_seq_buttons)
        file_sequence_box.addLayout(set_pulse_dur)
        file_sequence.setLayout(file_sequence_box)

        auto_sequence = QGroupBox(title='Automatic Sequence Generator')
        auto_sequence.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.enable_ext_interrupts = QPushButton('Enable External\nInterrupts')
        self.enable_ext_interrupts.setFixedSize(90, 30)
        self.enable_ext_interrupts.clicked.connect(enable_ext_interrupts)

        self.enable_timer_interrupts = QPushButton('Enable Timer\nInterrupts')
        self.enable_timer_interrupts.setFixedSize(90, 30)
        self.clear_sequence.clicked.connect(enable_timer_interrupts)

        aut_seq_buttons = QHBoxLayout()
        aut_seq_buttons.addWidget(self.enable_ext_interrupts)
        aut_seq_buttons.addWidget(self.enable_timer_interrupts)
        aut_seq_buttons.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        seq_label = QLabel("Seq. Period:")
        self.seq_period = QSpinBox()
        self.seq_period.setRange(0, 10000)
        self.seq_period.setSingleStep(10.0)
        _seq_label = QLabel(" [mSec]")

        self.send_seq_period = QPushButton('Send Seq.\nPeriod')
        self.send_seq_period.setFixedSize(90, 40)
        self.send_seq_period.clicked.connect(send_seq_period)

        set_seq_per = QHBoxLayout()
        set_seq_per.addWidget(seq_label)
        set_seq_per.addWidget(self.seq_period)
        set_seq_per.addWidget(_seq_label)
        set_seq_per.addWidget(self.send_seq_period)
        set_seq_per.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        auto_sequence_box = QVBoxLayout()
        auto_sequence_box.addLayout(aut_seq_buttons)
        auto_sequence_box.addLayout(set_seq_per)
        auto_sequence.setLayout(auto_sequence_box)
        
        layout.addWidget(file_sequence)
        layout.addWidget(auto_sequence)
        layout.addWidget(self.def_file_info)
        layout.setAlignment(self.def_file_info, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.set_seq_info)
        layout.setAlignment(self.set_seq_info, Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(layout)           