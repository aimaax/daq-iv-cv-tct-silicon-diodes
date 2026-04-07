from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from DAQ.AXIOM.GUI_temp_IV_CV.VoltageSettings import VoltageSettings
from DAQ.AXIOM.Utils.Plot.TCTPlot import TCTPlot

 
class AnalysisPanel(QWidget): 
    def __init__(self, select_measurement_directory, get_measurement_directory, start_analysis, abort_analysis):
        super().__init__()

        status_analysis = QGroupBox(title='Analysis Directory')
        status_analysis.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        status_analysis.setContentsMargins(10, 30, 10, 10)

        directory_label = QLabel('Current Analysis Directory:')

        # self.current_directory_box = QLabel(get_measurement_directory())
        # self.current_directory_box.setFixedWidth(350)
        # self.current_directory_box.setContentsMargins(3, 3, 3, 3)
        # self.current_directory_box.setStyleSheet('background-color: #FBFBFB;')

        self.current_directory_box = QPlainTextEdit(get_measurement_directory())
        self.current_directory_box.setFixedWidth(350)
        self.current_directory_box.setFixedHeight(40)
        self.current_directory_box.setReadOnly(True)
        self.current_directory_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.current_directory_box.setContentsMargins(3, 3, 3, 3)
        self.current_directory_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.current_directory_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        select_directory = QPushButton('Select Directory')
        select_directory.setFixedSize(200, 25)
        select_directory.clicked.connect(select_measurement_directory)

        self.voltage_settings = VoltageSettings()

        status_analysis_layout = QVBoxLayout()
        status_analysis_layout.addWidget(directory_label)
        #status_analysis_layout.addSpacing(5)
        status_analysis_layout.addWidget(self.current_directory_box)
        #status_analysis_layout.addSpacing(20)
        status_analysis_layout.addWidget(select_directory)
        status_analysis_layout.setAlignment(self.current_directory_box, Qt.AlignmentFlag.AlignHCenter)
        status_analysis_layout.setAlignment(select_directory, Qt.AlignmentFlag.AlignHCenter)
        status_analysis.setLayout(status_analysis_layout)
        status_analysis.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.start_analysis = QPushButton('Start')
        self.start_analysis.setFixedSize(70, 25)
        self.start_analysis.clicked.connect(start_analysis)

        self.abort_analysis = QPushButton('Abort')
        self.abort_analysis.setFixedSize(70, 25)
        self.abort_analysis.clicked.connect(abort_analysis)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.start_analysis)
        buttons_layout.setAlignment(self.start_analysis, Qt.AlignmentFlag.AlignCenter)
        buttons_layout.addWidget(self.abort_analysis)
        buttons_layout.setAlignment(self.abort_analysis, Qt.AlignmentFlag.AlignCenter)

        self.analysis_indicator = QLabel('')
        self.analysis_indicator.setFixedSize(15, 15)
        self.analysis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.analysis_info = QLabel('')
        self.analysis_info.setFixedWidth(250)
        self.analysis_info.setContentsMargins(3, 3, 3, 3)
        self.analysis_info.setStyleSheet('background-color: #FBFBFB;')
        analysis_layout = QHBoxLayout()
        analysis_layout.addStretch(1)
        analysis_layout.addWidget(self.analysis_indicator)
        analysis_layout.setAlignment(self.analysis_indicator, Qt.AlignmentFlag.AlignVCenter)
        analysis_layout.addWidget(self.analysis_info)
        analysis_layout.addStretch(1)
        analysis_layout.setSpacing(10)

        self.results_canvas = TCTPlot()
        self.results_canvas.ax.set_title('Analysis Plot')
        self.results_canvas.ax.set_xlabel('Voltage (V)')
        self.results_canvas.ax.set_ylabel('Collected Charge (a.u.)')

        layout = QVBoxLayout()
        layout.addWidget(status_analysis)
        #layout.addWidget(self.voltage_settings)
        layout.addLayout(buttons_layout)
        layout.addLayout(analysis_layout)
        layout.addWidget(self.results_canvas)
        self.setLayout(layout)

        self.set_analysis_indicator(mode=0)
        self.abort_analysis.setEnabled(False)

    def set_analysis_indicator(self, mode: int):
        if mode == 0:
            self.analysis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.analysis_info.setText('Please select TCT measurement directory')
        elif mode == 1:
            self.analysis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.analysis_info.setText('TCT analysis ready')
        elif mode == 2:
            self.analysis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.analysis_info.setText('TCT analysis started')
        elif mode == 3:
            self.analysis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.analysis_info.setText('Analysis finished! Ready for next analysis')
        else:
            raise ValueError('The parameter "mode" must be 0, 1, 2 or 3!')