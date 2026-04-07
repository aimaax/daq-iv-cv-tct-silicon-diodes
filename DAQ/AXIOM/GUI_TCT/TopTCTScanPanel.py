from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QCheckBox, QHBoxLayout, QPushButton, QLineEdit, QLabel, QSizePolicy, QSpinBox, QTabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from DAQ.AXIOM.Utils.Plot.TCTPlot import TCTPlot

class TopTCTScanPanel(QWidget): 
    def __init__(self, start_area_scan = None, abort_area_scan = None, start_focus_scan = None, abort_focus_scan = None):
        super().__init__()

        # --- Connect start and abort area scan ---
        self.start_area_scan = start_area_scan
        self.abort_area_scan = abort_area_scan

        # --- Connect start and abort focus scan ---
        self.start_focus_scan = start_focus_scan
        self.abort_focus_scan = abort_focus_scan

        # --- Intial choice of XY for focus scan ---
        self.FS_xy = "X"

        # --- Create Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # --- Create Area Search Tab ---
        self.area_scan_widget = QWidget()
        self._area_scan_tab() 
        self.tab_widget.addTab(self.area_scan_widget, "Area Scan")

        # --- Create Focus Scan Tab ---
        self.focus_scan_widget = QWidget() 
        self._focus_scan_tab()
        self.tab_widget.addTab(self.focus_scan_widget, "Focus Scan")

        # --- Main Layout for the Top_TCT_Scan Widget ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # --- Initial setup for the default tab ---
        self.set_top_TCT_scan_indicator(mode=0)
        self._update_scan_points_label(tab_name="Area Scan")
        self._update_scan_points_label(tab_name="Focus Scan")


    def _area_scan_tab(self):

        area_scan_control = QGroupBox(title='Area Scan Settings')
        area_scan_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # --- X Axis Controls ---
        self.AS_initial_position_x = QSpinBox()
        self.AS_initial_position_x.setFixedWidth(60)
        self.AS_initial_position_x.setRange(-100000, 100000)
        self.AS_initial_position_x.setValue(-500)

        self.AS_step_size_x = QSpinBox()
        self.AS_step_size_x.setFixedWidth(50)
        self.AS_step_size_x.setRange(1, 10000)
        self.AS_step_size_x.setValue(50)

        self.AS_num_steps_x = QSpinBox()
        self.AS_num_steps_x.setFixedWidth(50)
        self.AS_num_steps_x.setRange(1, 10000)
        self.AS_num_steps_x.setValue(20)

        # --- Y Axis Controls ---
        self.AS_initial_position_y = QSpinBox()
        self.AS_initial_position_y.setFixedWidth(60)
        self.AS_initial_position_y.setRange(-100000, 10000)
        self.AS_initial_position_y.setValue(-500)

        self.AS_step_size_y = QSpinBox()
        self.AS_step_size_y.setFixedWidth(50)
        self.AS_step_size_y.setRange(1, 10000)
        self.AS_step_size_y.setValue(50)

        self.AS_num_steps_y = QSpinBox()
        self.AS_num_steps_y.setFixedWidth(50)
        self.AS_num_steps_y.setRange(1, 10000)
        self.AS_num_steps_y.setValue(20)

        # --- Layout for X ---
        x_layout = QHBoxLayout()
        x_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        x_layout.addStretch(1)
        x_layout.addWidget(QLabel(u"X\u2080:"))
        x_layout.addWidget(self.AS_initial_position_x)
        x_layout.addStretch(1)
        x_layout.addWidget(QLabel("ΔX:"))
        x_layout.addWidget(self.AS_step_size_x)
        x_layout.addStretch(1)
        x_layout.addWidget(QLabel("N Steps:"))
        x_layout.addWidget(self.AS_num_steps_x)
        x_layout.addStretch(1)
    
        # --- Label for X Scan Points ---
        self.AS_x_scan_points_label = QLabel()
        self.AS_x_scan_points_label.setFixedWidth(160)
        self.AS_x_scan_points_label.setWordWrap(False)
        x_layout.addWidget(self.AS_x_scan_points_label)

        # --- Layout for Y ---
        y_layout = QHBoxLayout()
        y_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        y_layout.addStretch(1)
        y_layout.addWidget(QLabel(u"Y\u2080:"))
        y_layout.addWidget(self.AS_initial_position_y)
        y_layout.addStretch(1)
        y_layout.addWidget(QLabel("ΔY:"))
        y_layout.addWidget(self.AS_step_size_y)
        y_layout.addStretch(1)
        y_layout.addWidget(QLabel("N Steps:"))
        y_layout.addWidget(self.AS_num_steps_y)
        y_layout.addStretch(1)

        # --- Label for Y Scan Points ---
        self.AS_y_scan_points_label = QLabel()
        self.AS_y_scan_points_label.setFixedWidth(160)
        self.AS_y_scan_points_label.setWordWrap(False)
        y_layout.addWidget(self.AS_y_scan_points_label)

        # --- Connect signals to update labels ---
        self.AS_initial_position_x.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Area Scan"))
        self.AS_step_size_x.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Area Scan"))
        self.AS_num_steps_x.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Area Scan"))
        self.AS_initial_position_y.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Area Scan"))
        self.AS_step_size_y.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Area Scan"))
        self.AS_num_steps_y.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Area Scan"))

        # --- Add Voltage Label ---
        self.AS_voltage_label = QLabel('Voltage:')
        self.AS_voltage_label.setFixedWidth(50)

        # --- Add Voltage Value QSpinBox ---
        self.AS_voltage_value = QSpinBox()
        self.AS_voltage_value.setFixedWidth(50)
        self.AS_voltage_value.setRange(-1000, 0)
        self.AS_voltage_value.setValue(-300)

        # --- Control Buttons ---
        self.AS_start_scan = QPushButton('Start')
        self.AS_start_scan.setFixedSize(70, 25)
        self.AS_start_scan.clicked.connect(self.start_area_scan)

        self.AS_abort_scan = QPushButton('Abort')
        self.AS_abort_scan.setFixedSize(70, 25)
        self.AS_abort_scan.clicked.connect(self.abort_area_scan)

        button_info_layout = QHBoxLayout()
        button_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.AS_voltage_label)
        button_info_layout.addWidget(self.AS_voltage_value)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.AS_start_scan)
        button_info_layout.setAlignment(self.AS_start_scan, Qt.AlignmentFlag.AlignCenter)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.AS_abort_scan)
        button_info_layout.setAlignment(self.AS_abort_scan, Qt.AlignmentFlag.AlignCenter)

        # --- Status Indicator ---
        self.AS_align_indicator = QLabel('')
        self.AS_align_indicator.setFixedSize(15, 15)
        self.AS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        
        self.AS_align_info = QLabel('')
        self.AS_align_info.setFixedWidth(250)
        self.AS_align_info.setContentsMargins(3, 3, 3, 3)
        self.AS_align_info.setStyleSheet('background-color: #FBFBFB;')
        
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.AS_align_indicator)
        button_info_layout.setAlignment(self.AS_align_indicator, Qt.AlignmentFlag.AlignVCenter)
        button_info_layout.addWidget(self.AS_align_info)
        button_info_layout.addStretch(1)

        # --- Assemble Settings Layout ---
        area_settings_layout = QVBoxLayout()
        area_settings_layout.addLayout(x_layout)
        area_settings_layout.addLayout(y_layout)
        area_settings_layout.addLayout(button_info_layout)
        area_scan_control.setLayout(area_settings_layout)

        # --- Results Plot ---
        self.AS_results_canvas = TCTPlot()
        self.AS_results_canvas.ax.set_title('Area Scan Graph')
        self.AS_results_canvas.ax.set_xlabel('X Motor Position (steps)')
        self.AS_results_canvas.ax.set_ylabel('Y Motor Position (steps)')

        # --- Layout for the Area Search Tab Widget ---
        area_scan_layout = QVBoxLayout(self.area_scan_widget)
        area_scan_layout.addWidget(area_scan_control)
        area_scan_layout.addWidget(self.AS_results_canvas)
        self.area_scan_widget.setLayout(area_scan_layout)

    def _focus_scan_tab(self):
        focus_scan_control = QGroupBox(title='Focus Scan Settings')
        focus_scan_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # --- Z Axis Controls ---
        self.FS_initial_position_z = QSpinBox()
        self.FS_initial_position_z.setFixedWidth(60)
        self.FS_initial_position_z.setRange(-100000, 100000)
        self.FS_initial_position_z.setValue(-500)

        self.FS_step_size_z = QSpinBox()
        self.FS_step_size_z.setFixedWidth(50)
        self.FS_step_size_z.setRange(1, 10000)
        self.FS_step_size_z.setValue(50)

        self.FS_num_steps_z = QSpinBox()
        self.FS_num_steps_z.setFixedWidth(50)
        self.FS_num_steps_z.setRange(1, 10000)
        self.FS_num_steps_z.setValue(20)

        # --- XY Axis Controls ---
        self.FS_initial_position_xy = QSpinBox()
        self.FS_initial_position_xy.setFixedWidth(60)
        self.FS_initial_position_xy.setRange(-100000, 100000)
        self.FS_initial_position_xy.setValue(-500)

        self.FS_step_size_xy = QSpinBox()
        self.FS_step_size_xy.setFixedWidth(50)
        self.FS_step_size_xy.setRange(1, 10000)
        self.FS_step_size_xy.setValue(50)

        self.FS_num_steps_xy = QSpinBox()
        self.FS_num_steps_xy.setFixedWidth(50)
        self.FS_num_steps_xy.setRange(1, 10000)
        self.FS_num_steps_xy.setValue(20)

        # --- Layout for Z ---
        z_layout = QHBoxLayout()
        z_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        z_layout.addStretch(1)
        z_layout.addWidget(QLabel(u"Z\u2080:"))
        z_layout.addWidget(self.FS_initial_position_z)
        z_layout.addStretch(1)
        z_layout.addWidget(QLabel("ΔZ:"))
        z_layout.addWidget(self.FS_step_size_z)
        z_layout.addStretch(1)
        z_layout.addWidget(QLabel("N Steps:"))
        z_layout.addWidget(self.FS_num_steps_z)
        z_layout.addStretch(1)
    
        # --- Label for Z Scan Points ---
        self.FS_z_scan_points_label = QLabel()
        self.FS_z_scan_points_label.setFixedWidth(160)
        self.FS_z_scan_points_label.setWordWrap(False)
        z_layout.addWidget(self.FS_z_scan_points_label)

        # --- Layout for XY ---
        xy_layout = QHBoxLayout()
        xy_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        xy_layout.addStretch(1)
        self.FS_xy_0_label = QLabel(f"{self.FS_xy}\u2080:")
        xy_layout.addWidget(self.FS_xy_0_label)
        xy_layout.addWidget(self.FS_initial_position_xy)
        xy_layout.addStretch(1)
        self.FS_xy_delta_label = QLabel(f"Δ{self.FS_xy}:")
        xy_layout.addWidget(self.FS_xy_delta_label)
        xy_layout.addWidget(self.FS_step_size_xy)
        xy_layout.addStretch(1)
        xy_layout.addWidget(QLabel("N Steps:"))
        xy_layout.addWidget(self.FS_num_steps_xy)
        xy_layout.addStretch(1)

        # --- Label for Y Scan Points ---
        self.FS_xy_scan_points_label = QLabel()
        self.FS_xy_scan_points_label.setFixedWidth(160)
        self.FS_xy_scan_points_label.setWordWrap(False)
        xy_layout.addWidget(self.FS_xy_scan_points_label)

        # --- Connect signals to update labels ---
        self.FS_initial_position_z.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Focus Scan"))
        self.FS_step_size_z.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Focus Scan"))
        self.FS_num_steps_z.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Focus Scan"))
        self.FS_initial_position_xy.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Focus Scan"))
        self.FS_step_size_xy.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Focus Scan"))
        self.FS_num_steps_xy.valueChanged.connect(lambda: self._update_scan_points_label(tab_name="Focus Scan"))

        # --- Add Voltage Label ---
        self.FS_voltage_label = QLabel('Voltage:')
        self.FS_voltage_label.setFixedWidth(50)

        # --- Add Voltage Value QSpinBox ---
        self.FS_voltage_value = QSpinBox()
        self.FS_voltage_value.setFixedWidth(50)
        self.FS_voltage_value.setRange(-1000, 0)
        self.FS_voltage_value.setValue(-300)

        # --- XY Choice ---
        # create a on off button for XY choice
        self.FS_xy_choice = QPushButton('X')
        self.FS_xy_choice.setFixedSize(50, 25)
        self.FS_xy_choice.setCheckable(True)
        self.FS_xy_choice.clicked.connect(self._toggle_xy_choice)

        # --- Control Buttons ---
        self.FS_start_scan = QPushButton('Start')
        self.FS_start_scan.setFixedSize(70, 25)
        self.FS_start_scan.clicked.connect(self.start_focus_scan)

        self.FS_abort_scan = QPushButton('Abort')
        self.FS_abort_scan.setFixedSize(70, 25)	
        self.FS_abort_scan.clicked.connect(self.abort_focus_scan)
        
        button_info_layout = QHBoxLayout()
        button_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.FS_voltage_label)
        button_info_layout.addWidget(self.FS_voltage_value)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.FS_xy_choice)
        button_info_layout.setAlignment(self.FS_xy_choice, Qt.AlignmentFlag.AlignCenter)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.FS_start_scan)
        button_info_layout.setAlignment(self.FS_start_scan, Qt.AlignmentFlag.AlignCenter)
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.FS_abort_scan)
        button_info_layout.setAlignment(self.FS_abort_scan, Qt.AlignmentFlag.AlignCenter)

        # --- Status Indicator ---
        self.FS_align_indicator = QLabel('')
        self.FS_align_indicator.setFixedSize(15, 15)
        self.FS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        
        self.FS_align_info = QLabel('')
        self.FS_align_info.setFixedWidth(250)
        self.FS_align_info.setContentsMargins(3, 3, 3, 3)
        self.FS_align_info.setStyleSheet('background-color: #FBFBFB;')
        
        button_info_layout.addStretch(1)
        button_info_layout.addWidget(self.FS_align_indicator)
        button_info_layout.setAlignment(self.FS_align_indicator, Qt.AlignmentFlag.AlignVCenter)
        button_info_layout.addWidget(self.FS_align_info)
        button_info_layout.addStretch(1)

        # --- Assemble Settings Layout ---
        focus_settings_layout = QVBoxLayout()
        focus_settings_layout.addLayout(z_layout)
        focus_settings_layout.addLayout(xy_layout)
        focus_settings_layout.addLayout(button_info_layout)
        focus_scan_control.setLayout(focus_settings_layout)

        # --- Results Plot ---
        self.FS_results_canvas = TCTPlot()
        self.FS_results_canvas.ax.set_title('Focus Scan Graph')
        self.FS_results_canvas.ax.set_ylabel('Z Motor Position (steps)')
        self.FS_results_canvas.ax.set_xlabel(f'{self.FS_xy} Motor Position (steps)')

        # --- Layout for the Area Search Tab Widget ---
        focus_scan_layout = QVBoxLayout(self.focus_scan_widget)
        focus_scan_layout.addWidget(focus_scan_control)
        focus_scan_layout.addWidget(self.FS_results_canvas)
        self.focus_scan_widget.setLayout(focus_scan_layout)

    def _toggle_xy_choice(self):
        if self.FS_xy_choice.text() == 'Y':
            self.FS_xy_choice.setText('X')
            self.FS_xy = "X"
        else:
            self.FS_xy_choice.setText('Y')
            self.FS_xy = "Y"

        # Update labels
        self.FS_xy_0_label.setText(f"{self.FS_xy}\u2080:")
        self.FS_xy_delta_label.setText(f"Δ{self.FS_xy}:")
        self._update_scan_points_label(tab_name="Focus Scan")

    def _points_label(self, axis: str, points: list):
        if not points:
            label_text = f"{axis}: []"
        elif len(points) == 1:
            label_text = f"{axis}: [{points[0]}]"
        elif len(points) == 2:
            label_text = f"{axis}: [{points[0]}, {points[1]}]"
        else:
            label_text = f"{axis}: [{points[0]}, {points[1]}, ..., {points[-1]}]"
        return label_text

    def _update_scan_points_label(self, tab_name: str):
        """Updates the labels showing the calculated scan points."""
        # --- Calculate X points ---
        if tab_name == "Area Scan":
            start_x = self.AS_initial_position_x.value()
            step_x = self.AS_step_size_x.value()
            num_x = self.AS_num_steps_x.value()
            points_x = [start_x + i * step_x for i in range(num_x)]
            label_text_x = self._points_label("X", points_x)
            self.AS_x_scan_points_label.setText(label_text_x)
        elif tab_name == "Focus Scan":
            start_z = self.FS_initial_position_z.value()
            step_z = self.FS_step_size_z.value()
            num_z = self.FS_num_steps_z.value()
            points_z = [start_z + i * step_z for i in range(num_z)]
            label_text_z = self._points_label("Z", points_z)
            self.FS_z_scan_points_label.setText(label_text_z)
        
        # --- Calculate Y points ---
        if tab_name == "Area Scan":
            start_y = self.AS_initial_position_y.value()
            step_y = self.AS_step_size_y.value()
            num_y = self.AS_num_steps_y.value()
            points_y = [start_y + i * step_y for i in range(num_y)]
            label_text_y = self._points_label("Y", points_y)
            self.AS_y_scan_points_label.setText(label_text_y)
        elif tab_name == "Focus Scan":
            start_xy = self.FS_initial_position_xy.value()
            step_xy = self.FS_step_size_xy.value()
            num_xy = self.FS_num_steps_xy.value()
            points_xy = [start_xy + i * step_xy for i in range(num_xy)]
            label_text_xy = self._points_label(self.FS_xy, points_xy)
            self.FS_xy_scan_points_label.setText(label_text_xy)


    def set_top_TCT_scan_indicator(self, mode: int):
        """
        Set the alignment indicator state and message.
        
        Args:
            mode (int): Indicator mode (0-5)
                0: Not ready (red)
                1: Ready to start (yellow)
                2: Starting calibration (green)
                3: Broad scan (green)
                4: Fine scan (green)
                5: Finished (green)
        
        Raises:
            ValueError: If mode is not between 0 and 5
        """
        if mode == 0:
            self.AS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.AS_align_info.setText('Laser is off!')
            self.FS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.FS_align_info.setText('Laser is off!')
        elif mode == 1:
            self.AS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.AS_align_info.setText('Scans are ready to start')
            self.FS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.FS_align_info.setText('Scans are ready to start')
        elif mode == 2:
            self.AS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.AS_align_info.setText('Starting Area scan...')
            self.FS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.FS_align_info.setText('Starting Area scan...')
        elif mode == 3:
            self.AS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.AS_align_info.setText('Starting Focus scan...')
            self.FS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.FS_align_info.setText('Starting Focus scan...')
        elif mode == 4:
            self.AS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.AS_align_info.setText('Scan finished.')
            self.FS_align_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.FS_align_info.setText('Scan finished.')
        else:
            raise ValueError('The parameter "mode" must be 0-5!')