from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QCheckBox, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.Plot.TCTPlot import TCTPlot

 
class AutoAlignPanel(QWidget): 
    def __init__(self, start_auto_align, abort_auto_align):
        super().__init__()

        auto_align_control = QGroupBox(title='Auto Alignment Control')
        auto_align_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        auto_align_control.setFixedHeight(150)

        self.start_scan = QPushButton('Start')
        self.start_scan.setFixedSize(70, 25)
        self.start_scan.clicked.connect(start_auto_align)

        self.abort_scan = QPushButton('Abort')
        self.abort_scan.setFixedSize(70, 25)
        self.abort_scan.clicked.connect(abort_auto_align)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_scan)
        button_layout.setAlignment(self.start_scan, Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.abort_scan)
        button_layout.setAlignment(self.abort_scan, Qt.AlignmentFlag.AlignCenter)

        self.align_indicator = QLabel('')
        self.align_indicator.setFixedSize(15, 15)
        self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.align_info = QLabel('')
        self.align_info.setFixedWidth(250)
        self.align_info.setContentsMargins(3, 3, 3, 3)
        self.align_info.setStyleSheet('background-color: #FBFBFB;')
        info_layout = QHBoxLayout()
        info_layout.addStretch(1)
        info_layout.addWidget(self.align_indicator)
        info_layout.setAlignment(self.align_indicator, Qt.AlignmentFlag.AlignVCenter)
        info_layout.addWidget(self.align_info)
        info_layout.addStretch(1)
        info_layout.setSpacing(10)

        init_layout = QVBoxLayout()
        init_layout.addLayout(button_layout)
        init_layout.addLayout(info_layout)
        auto_align_control.setLayout(init_layout)

        self.results_canvas = TCTPlot()
        self.results_canvas.ax.set_title('Auto Alignment Graph')
        self.results_canvas.ax.set_xlabel('X Motor Position (steps)')
        self.results_canvas.ax.set_ylabel('Y Motor Position (steps)')

        layout = QVBoxLayout()
        layout.addWidget(auto_align_control)
        layout.addWidget(self.results_canvas)
        self.setLayout(layout)
        self.set_align_indicator(mode=0)

    def set_align_indicator(self, mode: int):
        if mode == 0:
            self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.align_info.setText('Laser is off!')
        elif mode == 1:
            self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.align_info.setText('Auto alignment ready to start')
        elif mode == 2:
            self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.align_info.setText('Alignment calibration starting...')
        elif mode == 3:
            self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.align_info.setText('Laser position not inside sensor, proceeding with broad scan')
        elif mode == 4:
            self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            # self.align_info.setText('Laser position inside sensor, proceeding with 3 point scan')
            self.align_info.setText('Laser position inside sensor, proceeding with fine scan')
        elif mode == 5:
            self.align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.align_info.setText('Scan finished, moving to center point')
        else:
            raise ValueError('The parameter "mode" must be 0-5!')