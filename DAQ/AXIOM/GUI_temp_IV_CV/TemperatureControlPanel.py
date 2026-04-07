from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, \
    QGroupBox, QPushButton, QDoubleSpinBox, QSizePolicy, QPlainTextEdit, QSpinBox, QCheckBox
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from DAQ.AXIOM.Utils.design_helper_functions import add_label_to_input
from config import AIR_FLOW_SETPOINT_DEFAULT
from DAQ.AXIOM.Utils.summary_300um_uirad import create_300um_uirad_summary_csv


class TemperatureControlPanel(QWidget):
    def __init__(self, start_chiller, stop_chiller, toggle_peltiers, peltiers_active, get_measurement_directory,
                 select_measuremnet_directory, save_temperature_parameters, temp_config, switch_IV, switch_CV, switch_TCT,
                 reconnect_chiller, reconnect_peltier, reconnect_pt1000, reconnect_arduino, reconnect_air_flux, set_value_air_flux,
                 copy_and_sync_to_git_all_csv_files, overwrite_sync_files_checkbox_state_changed):
        super().__init__()

        self.setFixedWidth(400)
        self.setContentsMargins(0, 10, 0, 10)

        directory_selection = QGroupBox(title='Measurement Directory')
        directory_selection.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        directory_selection.setContentsMargins(10, 25, 10, 10)

        directory_label = QLabel('Current Measurement Directory:')

        self.current_directory_box = QPlainTextEdit(get_measurement_directory())
        self.current_directory_box.setFixedWidth(350)
        self.current_directory_box.setFixedHeight(40)
        self.current_directory_box.setReadOnly(True)
        self.current_directory_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.current_directory_box.setContentsMargins(3, 3, 3, 3)
        self.current_directory_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.current_directory_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        select_directory = QPushButton('Select Measurement Directory')
        select_directory.setFixedSize(200, 25)
        select_directory.clicked.connect(select_measuremnet_directory)

        cable_reminder_label = QLabel('<b>REMINDER: PAD current for LF, TOTAL current for the rest.</b>')

        directory_selection_layout = QVBoxLayout()
        directory_selection_layout.addWidget(directory_label)
        directory_selection_layout.addSpacing(5)
        directory_selection_layout.addWidget(self.current_directory_box)
        directory_selection_layout.addSpacing(14)
        directory_selection_layout.addWidget(select_directory)
        directory_selection_layout.addSpacing(5)
        directory_selection_layout.addWidget(cable_reminder_label)
        directory_selection_layout.setAlignment(self.current_directory_box, Qt.AlignmentFlag.AlignHCenter)
        directory_selection_layout.setAlignment(select_directory, Qt.AlignmentFlag.AlignHCenter)
        directory_selection_layout.setAlignment(cable_reminder_label, Qt.AlignmentFlag.AlignHCenter)
        directory_selection.setLayout(directory_selection_layout)
        directory_selection.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        switch_control = QGroupBox(title='Switch Box Control')
        switch_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        switch_control.setContentsMargins(10, 20, 10, 10)

        self.switch_info = QLabel('Select Channel')
        self.switch_info.setFixedWidth(100)
        self.switch_info.setContentsMargins(3, 3, 3, 3)
        self.switch_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.switch_info.setStyleSheet('background-color: #FBFBFB;')
        switch_info_labelbox = add_label_to_input(self.switch_info, 'Active Channel')

        switch_layout_top = QHBoxLayout()
        switch_layout_top.addWidget(switch_info_labelbox)

        self.IV_switch_button = QPushButton('IV')
        self.IV_switch_button.setFixedSize(35, 25)
        self.IV_switch_button.clicked.connect(switch_IV)
        self.CV_switch_button = QPushButton('CV')
        self.CV_switch_button.setFixedSize(35, 25)
        self.CV_switch_button.clicked.connect(switch_CV)
        self.TCT_switch_button = QPushButton('TCT')
        self.TCT_switch_button.setFixedSize(35, 25)
        self.TCT_switch_button.clicked.connect(switch_TCT)

        switch_layout_bottom = QHBoxLayout()
        switch_layout_bottom.addWidget(self.IV_switch_button)
        switch_layout_bottom.addWidget(self.CV_switch_button)
        switch_layout_bottom.addWidget(self.TCT_switch_button)
        switch_layout_bottom.setAlignment(Qt.AlignmentFlag.AlignBottom)

        switch_layout = QHBoxLayout()
        switch_layout.addStretch(1)
        switch_layout.addLayout(switch_layout_top)
        switch_layout.addStretch(1)
        switch_layout.addLayout(switch_layout_bottom)
        switch_layout.addStretch(1)
        switch_control.setLayout(switch_layout)
        switch_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        chiller_control = QGroupBox(title='Chiller Control')
        chiller_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        chiller_control.setContentsMargins(10, 20, 10, 10)

        self.chiller_indicator = QLabel('')
        self.chiller_indicator.setFixedSize(15, 15)
        self.chiller_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.chiller_info = QLabel('')
        self.chiller_info.setFixedWidth(225)
        self.chiller_info.setContentsMargins(3, 3, 3, 3)
        self.chiller_info.setStyleSheet('background-color: #FBFBFB;')

        # Horizontal layout to hold indicator and info     
        chiller_layout_top = QHBoxLayout()
        chiller_layout_top.addStretch(1)
        chiller_layout_top.addWidget(self.chiller_indicator)
        chiller_layout_top.setAlignment(self.chiller_indicator, Qt.AlignmentFlag.AlignVCenter)
        chiller_layout_top.addWidget(self.chiller_info)
        chiller_layout_top.addStretch(1)

        self.chiller_setpoint_box = QDoubleSpinBox()
        self.chiller_setpoint_box.setFixedSize(125, 25)
        self.chiller_setpoint_box.setDecimals(2)
        self.chiller_setpoint_box.setRange(-100, 35)
        self.chiller_setpoint_box.setSingleStep(1.0)
        self.chiller_setpoint_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chiller_setpoint_box.setValue(temp_config['chiller_setpoint'])
        self.chiller_setpoint_box.valueChanged.connect(self.enable_save_button)
        chiller_setpoint_labelbox = add_label_to_input(self.chiller_setpoint_box, 'Chiller Setpoint (°C)')
        self.start_chiller_button = QPushButton('Start Chiller')
        self.start_chiller_button.setFixedSize(75, 25)
        self.start_chiller_button.clicked.connect(start_chiller)
        self.stop_chiller_button = QPushButton('Stop Chiller')
        self.stop_chiller_button.setFixedSize(75, 25)
        self.stop_chiller_button.clicked.connect(stop_chiller)
        chiller_layout_bottom = QHBoxLayout()
        chiller_layout_bottom.addStretch(1)
        chiller_layout_bottom.addWidget(chiller_setpoint_labelbox)
        chiller_layout_bottom.addWidget(self.start_chiller_button)
        chiller_layout_bottom.addWidget(self.stop_chiller_button)
        chiller_layout_bottom.setAlignment(self.start_chiller_button, Qt.AlignmentFlag.AlignBottom)
        chiller_layout_bottom.setAlignment(self.stop_chiller_button, Qt.AlignmentFlag.AlignBottom)
        chiller_layout_bottom.addStretch(1)
        chiller_layout_bottom.setSpacing(20)

        chiller_layout = QVBoxLayout()
        chiller_layout.addLayout(chiller_layout_top)
        chiller_layout.addLayout(chiller_layout_bottom)
        chiller_layout.setSpacing(10)
        chiller_control.setLayout(chiller_layout)
        chiller_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        peltier_control = QGroupBox(title='Peltier Control')
        peltier_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        peltier_control.setContentsMargins(10, 20, 10, 10)

        self.peltier_indicator = QLabel('')
        self.peltier_indicator.setFixedSize(15, 15)
        self.peltier_indicator.setStyleSheet('border: 1px solid #000000; background-color: #FBFBFB;')
        self.peltier_info = QLabel('')
        self.peltier_info.setFixedWidth(225)
        self.peltier_info.setContentsMargins(3, 3, 3, 3)
        self.peltier_info.setStyleSheet('background-color: #FBFBFB;')

        # Horizontal layout to hold indicator and info
        peltier_layout_top = QHBoxLayout()
        peltier_layout_top.addStretch(1)
        peltier_layout_top.addWidget(self.peltier_indicator)
        peltier_layout_top.setAlignment(self.peltier_indicator, Qt.AlignmentFlag.AlignVCenter)
        peltier_layout_top.addWidget(self.peltier_info)
        peltier_layout_top.addStretch(1)

        self.peltier_target_box = QDoubleSpinBox()
        self.peltier_target_box.setFixedSize(125, 25)
        self.peltier_target_box.setDecimals(2)
        self.peltier_target_box.setRange(-100, 30)
        self.peltier_target_box.setSingleStep(1.0)
        self.peltier_target_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.peltier_target_box.setValue(temp_config['target_temperature'])
        self.peltier_target_box.valueChanged.connect(self.enable_save_button)
        peltier_target_labelbox = add_label_to_input(self.peltier_target_box, 'Target Temperature (°C)')
        self.toggle_peltier_button = QPushButton('Start Peltier Elements' if not peltiers_active else 'Stop Peltier Elements')
        self.toggle_peltier_button.setFixedSize(150, 25)
        self.toggle_peltier_button.clicked.connect(toggle_peltiers)
        peltier_layout_bottom = QHBoxLayout()
        peltier_layout_bottom.addStretch(1)
        peltier_layout_bottom.addWidget(peltier_target_labelbox)
        peltier_layout_bottom.addWidget(self.toggle_peltier_button)
        peltier_layout_bottom.setAlignment(self.toggle_peltier_button, Qt.AlignmentFlag.AlignBottom)
        peltier_layout_bottom.addStretch(1)
        peltier_layout_bottom.setSpacing(20)

        peltier_layout = QVBoxLayout()
        peltier_layout.addLayout(peltier_layout_top)
        peltier_layout.addLayout(peltier_layout_bottom)
        peltier_layout.setSpacing(10)
        peltier_control.setLayout(peltier_layout)
        peltier_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        reconnect_control = QGroupBox(title='Reconnect Devices')
        reconnect_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        reconnect_control.setContentsMargins(10, 20, 10, 10)
        
        self.chiller_reconnect_button = QPushButton()
        self.chiller_reconnect_button.setFixedSize(25, 25)
        self.chiller_reconnect_button.setIcon(QIcon("DAQ/AXIOM/GUI_temp_IV_CV/Images/reset_button.png"))
        self.chiller_reconnect_button.setIconSize(QSize(22, 22))
        chiller_reconnect_labelbox = add_label_to_input(self.chiller_reconnect_button, 'Chiller')
        self.chiller_reconnect_button.clicked.connect(reconnect_chiller)
        
        self.peltier_reconnect_button = QPushButton()
        self.peltier_reconnect_button.setFixedSize(25, 25)
        self.peltier_reconnect_button.setIcon(QIcon("DAQ/AXIOM/GUI_temp_IV_CV/Images/reset_button.png"))
        self.peltier_reconnect_button.setIconSize(QSize(22, 22))
        peltier_reconnect_labelbox = add_label_to_input(self.peltier_reconnect_button, 'Peltier')
        self.peltier_reconnect_button.clicked.connect(reconnect_peltier)
        
        self.pt1000_reconnect_button = QPushButton()
        self.pt1000_reconnect_button.setFixedSize(25, 25)
        self.pt1000_reconnect_button.setIcon(QIcon("DAQ/AXIOM/GUI_temp_IV_CV/Images/reset_button.png"))
        self.pt1000_reconnect_button.setIconSize(QSize(22, 22))
        pt1000_reconnect_labelbox = add_label_to_input(self.pt1000_reconnect_button, 'Pt1000')
        self.pt1000_reconnect_button.clicked.connect(reconnect_pt1000)
        
        self.arduino_reconnect_button = QPushButton()
        self.arduino_reconnect_button.setFixedSize(25, 25)
        self.arduino_reconnect_button.setIcon(QIcon("DAQ/AXIOM/GUI_temp_IV_CV/Images/reset_button.png"))
        self.arduino_reconnect_button.setIconSize(QSize(22, 22))
        arduino_reconnect_labelbox = add_label_to_input(self.arduino_reconnect_button, 'Arduino')
        self.arduino_reconnect_button.clicked.connect(reconnect_arduino)
        
        self.air_flux_reconnect_button = QPushButton()
        self.air_flux_reconnect_button.setFixedSize(25, 25)
        self.air_flux_reconnect_button.setIcon(QIcon("DAQ/AXIOM/GUI_temp_IV_CV/Images/reset_button.png"))
        self.air_flux_reconnect_button.setIconSize(QSize(22, 22))
        air_flux_reconnect_labelbox = add_label_to_input(self.air_flux_reconnect_button, 'Air Flow')
        self.air_flux_reconnect_button.clicked.connect(reconnect_air_flux)

        reconnect_layout = QHBoxLayout()
        reconnect_layout.addStretch(1)
        reconnect_layout.addWidget(chiller_reconnect_labelbox)
        reconnect_layout.addWidget(peltier_reconnect_labelbox)
        reconnect_layout.addWidget(pt1000_reconnect_labelbox)
        reconnect_layout.addWidget(arduino_reconnect_labelbox)
        reconnect_layout.addWidget(air_flux_reconnect_labelbox)
        reconnect_layout.setAlignment(chiller_reconnect_labelbox, Qt.AlignmentFlag.AlignHCenter)
        reconnect_layout.setAlignment(peltier_reconnect_labelbox, Qt.AlignmentFlag.AlignHCenter)
        reconnect_layout.setAlignment(pt1000_reconnect_labelbox, Qt.AlignmentFlag.AlignHCenter)
        reconnect_layout.setAlignment(arduino_reconnect_labelbox, Qt.AlignmentFlag.AlignHCenter)
        reconnect_layout.setAlignment(air_flux_reconnect_labelbox, Qt.AlignmentFlag.AlignHCenter)
        reconnect_layout.addStretch(1)
        reconnect_layout.setSpacing(20)

        reconnect_control.setLayout(reconnect_layout)
        reconnect_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        air_flux_control = QGroupBox(title="Air Flow Controller")
        air_flux_control.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        air_flux_control.setContentsMargins(10, 20, 10, 10)
        
        self.air_flux_set_button = QPushButton("Apply Change")
        self.air_flux_set_button.setFixedSize(90, 25)
        air_flux_button_labelbox = add_label_to_input(self.air_flux_set_button, "")
        self.air_flux_set_button.clicked.connect(lambda: set_value_air_flux(self.air_flux_value_set.value()))
                
        self.air_flux_value_set = QSpinBox()
        self.air_flux_value_set.setRange(0, 100)
        self.air_flux_value_set.setValue(AIR_FLOW_SETPOINT_DEFAULT)
        self.air_flux_value_set.setSingleStep(1)
        self.air_flux_value_set.setFixedSize(100, 25)
        self.air_flux_value_set.setAlignment(Qt.AlignmentFlag.AlignCenter)
        air_flux_labelbox = add_label_to_input(self.air_flux_value_set, 'Setpoint (sl/min)')

        air_flux_layout = QHBoxLayout()
        air_flux_layout.addStretch(1)
        air_flux_layout.addWidget(air_flux_labelbox)
        air_flux_layout.addWidget(air_flux_button_labelbox)
        air_flux_layout.setAlignment(air_flux_labelbox, Qt.AlignmentFlag.AlignHCenter)
        air_flux_layout.setAlignment(air_flux_button_labelbox, Qt.AlignmentFlag.AlignHCenter)
        air_flux_layout.addStretch(1)
        air_flux_layout.setSpacing(20)
        air_flux_control.setLayout(air_flux_layout)
        air_flux_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Horizontal layout for save button and Create 300um UIRAD Summary button
        self.layout_save_create_summary = QHBoxLayout()
        self.save_button = QPushButton('Apply Changed Parameters')
        self.save_button.setFixedSize(180, 25)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(save_temperature_parameters)
        self.layout_save_create_summary.addWidget(self.save_button)

        # Add button to Create 300um UIRAD Summary
        self.extract_ref_diode_cc_button = QPushButton('Create UIRAD Summary')
        self.extract_ref_diode_cc_button.setFixedSize(180, 25)
        self.extract_ref_diode_cc_button.clicked.connect(create_300um_uirad_summary_csv)
        self.layout_save_create_summary.addWidget(self.extract_ref_diode_cc_button)
        
        # Horizontal layout for Copy/Sync CSV Files button and overwrite checkbox
        self.layout_sync_overwrite = QHBoxLayout()
        self.overwrite_sync_files_checkbox = QCheckBox('Overwrite current files')
        self.overwrite_sync_files_checkbox.setFixedSize(150, 25)
        self.overwrite_sync_files_checkbox.stateChanged.connect(lambda: overwrite_sync_files_checkbox_state_changed(self.overwrite_sync_files_checkbox.isChecked()))
        
        self.sync_csv_button = QPushButton('Copy/Sync CSV Files')
        self.sync_csv_button.setFixedSize(150, 25)
        self.sync_csv_button.clicked.connect(copy_and_sync_to_git_all_csv_files)

        self.layout_sync_overwrite.addStretch(1)
        self.layout_sync_overwrite.addWidget(self.overwrite_sync_files_checkbox)
        self.layout_sync_overwrite.addStretch(1)
        self.layout_sync_overwrite.addWidget(self.sync_csv_button)
        self.layout_sync_overwrite.addStretch(1)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, -1, 10, -1)
        # layout.setSpacing(40)
        layout.addWidget(directory_selection)
        layout.addWidget(chiller_control)
        layout.addWidget(peltier_control)
        layout.addWidget(switch_control)
        layout.addWidget(reconnect_control)
        layout.addWidget(air_flux_control)
        layout.addLayout(self.layout_save_create_summary)
        layout.addLayout(self.layout_sync_overwrite)
        self.setLayout(layout)

    def enable_save_button(self):
        self.save_button.setEnabled(True)

    def set_peltier_indicator(self, mode: int):
        if mode == 1:
            self.peltier_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.peltier_info.setText('Peltiers are active')
        elif mode == 2:
            self.peltier_indicator.setStyleSheet('border: 1px solid #000000; background-color: #f0ca24')
            self.peltier_info.setText('Peltiers are enabled, but not active')
        elif mode == 3:
            self.peltier_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.peltier_info.setText('Peltiers are deactivated')
        else:
            raise ValueError('The parameter "mode" must be 1, 2 or 3!')

    def set_chiller_indicator(self, mode: int):
        if mode == 1:
            self.chiller_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.chiller_info.setText('Chiller is active')
        elif mode == 2:
            self.chiller_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.chiller_info.setText('Chiller is deactivated')
        else:
            raise ValueError('The parameter "mode" must be 1 or 2!')
