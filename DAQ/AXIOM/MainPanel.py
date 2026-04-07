# === This GUI has to be started by executing the file ../start_GUI.py === #

from os import path
from time import sleep
from PySide6.QtCore import QSize, QThread, Signal, Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSizePolicy, QFileDialog, QTabWidget, QMessageBox, QCheckBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QVBoxLayout
import os
import shutil
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from git import Repo
from datetime import datetime, timedelta
import time
import re
import pandas as pd
import numpy as np

from DAQ.AXIOM.GUI_temp_IV_CV.TemperatureControlPanel import TemperatureControlPanel
from DAQ.AXIOM.GUI_temp_IV_CV.IVCVPanel import IVCVPanel
from DAQ.AXIOM.GUI_TCT.TCTPanel import TCTPanel

from DAQ.AXIOM.Utils.Plot.TempHumPlot import TempHumPlot
from DAQ.AXIOM.Utils.EnvironmentControl import EnvironmentControl
from DAQ.AXIOM.Utils.MeasurementSequences.MeasurementSequenceCV import MeasurementSequenceCV
from DAQ.AXIOM.Utils.MeasurementSequences.MeasurementSequenceIV import MeasurementSequenceIV
from DAQ.AXIOM.Utils.CloseEventDialog import CloseEventDialog
from DAQ.AXIOM.Utils.check_previous_measurements import check_previous_voltage_settings

from DAQ.AXIOM.TemperatureControl import temperature_config

from config import (
    CAMPAIGN_MEASUREMENT_DIRECTORY, 
    REFERENCE_UIRAD_DIODE_DIRECTORY,
    HIGH_FLUENCE_NEUTRONS_DIRECTORY,
    LOW_FLUENCE_NEUTRONS_DIRECTORY,
    DOUBLE_IRR_NEUTRON_DIRECTORY,
    PROTON_CAMPAIGN_DIRECTORY,
    PARTICULARS_ANALYSIS_DIRECTORY,
    COPY_TEMPERATURE_FILES
)


class MainPanel(QMainWindow):

    stop_temp_thread = Signal()

    def __init__(self):
        super().__init__()

        self.campaign_measurement_directory = path.abspath(CAMPAIGN_MEASUREMENT_DIRECTORY)
        self.automatically_select_measurement_directory(measurement_type='initial', sensor_name='')

        self.setWindowTitle('Temperature IV CV Control')

        self.setMinimumSize(QSize(1400, 750))
        self.resize(QSize(2000, 1100))

        # Read out or create temperature configuration file #
        temp_config = temperature_config.initialize(config_directory=path.abspath('./'))
        self._peltiers_active = temp_config['voltage_output_on']

        self.temperature_control_panel = TemperatureControlPanel(self.start_chiller, self.stop_chiller, self.toggle_peltiers, self._peltiers_active,
                                                                 self.get_measurement_directory, self.select_measurement_directory,
                                                                 self.save_temperature_parameters, temp_config, self.switch_IV, self.switch_CV, self.switch_TCT,
                                                                 self.reconnect_chiller, self.reconnect_peltier, self.reconnect_pt1000, self.reconnect_arduino,
                                                                 self.reconnect_air_flow, self.set_value_air_flux, self.copy_and_sync_to_git_all_csv_files,
                                                                 self.overwrite_sync_files_checkbox_state_changed)
        self.temperature_control_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        temperature_monitoring_canvas = TempHumPlot(labels_temp=['Target (PCB) Temperature', 'Chiller Setpoint',
                                                                 'Chiller Temperature (internal)', 'Housing Temperature',
                                                                 'Sensor Box Temperature', 'PCB Temperature', 'Pt1000 Temperature'],
                                                    labels_hum=['Housing Humidity', 'Sensor Box Humidity'],
                                                    line_colors_temp=['green', 'black', 'cyan', 'red', 'blue', 'orange', 'purple'],
                                                    line_colors_hum=['red', 'blue'])
        temperature_monitoring_canvas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        measurement_tabs = QTabWidget()
        measurement_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        self.IV_panel = IVCVPanel(measurement_type='IV', start_measurement_thread=self.start_measurement_thread_IV, 
                                        open_correction=self.open_correction
                                        # , only_one_start_after_finished_measurement_checkbox_active=self.only_one_start_after_finished_measurement_checkbox_active
                                        )
        self.IV_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        measurement_tabs.addTab(self.IV_panel, 'IV Measurement')
        
        self.CV_panel = IVCVPanel(
            measurement_type='CV', 
            start_measurement_thread=self.start_measurement_thread_CV, 
            open_correction=self.open_correction, 
            check_previous_voltage_settings=lambda: self.check_previous_voltage_settings_measurements(CV_or_TCT='CV')
        )
        
        self.CV_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        measurement_tabs.addTab(self.CV_panel, 'CV Measurement')
        self.TCT_panel = TCTPanel(
            start_measurement=self.start_TCT_measurement, 
            set_IV_indicator=self.IV_panel.set_measurement_indicator,
            set_CV_indicator=self.CV_panel.set_measurement_indicator, 
            apply_sensor_name_change=self.apply_sensor_name_change,
            change_campaign_measurement_directory_label=self.change_campaign_measurement_directory_label,
            check_filename_directory_exist_add_status=self.check_filename_directory_exist_add_status,
            start_IV_CV_TCT_after_finished_measurement=self.start_IV_CV_TCT_after_finished_measurement,
            check_previous_voltage_settings=lambda: self.check_previous_voltage_settings_measurements(CV_or_TCT='TCT')
        )
        self.TCT_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        measurement_tabs.addTab(self.TCT_panel, 'TCT Measurement')
        measurement_tabs.setCurrentIndex(0)
        measurement_tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        measurement_tabs.setContentsMargins(10, 10, 10, 10)

        main_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, -1, 10, -1)
        layout.setSpacing(30)
        layout.addWidget(self.temperature_control_panel)
        layout.addWidget(temperature_monitoring_canvas)
        layout.addWidget(measurement_tabs)
        main_widget.setLayout(layout)

        self.setCentralWidget(main_widget)
        self.setContentsMargins(0, 0, 0, 0)

        self.temperature_thread = QThread()
        try:
            self.environment_control = EnvironmentControl(temp_monitoring_canvas=temperature_monitoring_canvas,
                                                        temp_config=temp_config,
                                                        set_chiller_indicator=self.temperature_control_panel.set_chiller_indicator)
            self.environment_control.moveToThread(self.temperature_thread)
            self.stop_temp_thread.connect(self.environment_control.close_connections)
            self.environment_control.finished.connect(self.temperature_thread.quit)
            self.environment_control.peltier_in_operation.connect(self.live_peltier_indicator)
            self.temperature_thread.started.connect(self.environment_control.start_temperature_timer)
            self.temperature_thread.start()
        except:
            print("Not connected to setup... launching in test mode\n")
            self.environment_control = None


        self.TCT_thread = None
        self.measurement_thread = None
        self.measurement = None
        self._measurement_active = False
        self.IV_CV_panel = None

        # Make sure that self.overwrite_current_files is initialized to sync files with GUI button
        self.overwrite_current_files = False

    def closeEvent(self, event):
        close_event_dialog = CloseEventDialog(self)
        if close_event_dialog.exec() == QDialog.Accepted:
            self.sync_all_csv_files = close_event_dialog.copy_checkbox.isChecked()
            self.overwrite_current_files = close_event_dialog.overwrite_checkbox.isChecked()
            event.accept()
        else:
            event.ignore()
    
    def cleanup_exit(self):
        print("\nClosing GUI, disconnecting devices...")
        
        # Disconnect the oscilloscope and laser
        self.TCT_panel.osc_disconnect()
        self.TCT_panel.laserDisconnect()

        # Ramping down keithley2410 (keithely on top of box in lab)for TCT
        try:
            print("\nRamping down keithley2410 (address 7) for TCT...")
            self.TCT_panel.keithley2410.ramp_down()
            print("\nKeithley2410 voltage ramped down successfully")
        except:
            print("\nKeithley2410 (address 7) used for TCT already ramped down.")

        # Ramping down keithley2410 on address 4 (left keithley in lab) for IV and CV measurements
        try:
            print("\nRamping down keithley2410 (address 4) used for IV and CV...")
            self.measurement.keithley2410.ramp_down()
            print("\nKeithley2410 voltage ramped down successfully")
        except:
            print("\nKeithley2410 (address 4) used for IV and CV already ramped down.")
        
        # Stop the temperature thread
        self.stop_temperature_thread()

        if self.sync_all_csv_files == True:
            # Copy all IV and CV files to _IV_ALL_CSV and _CV_ALL_CSV in the target folder and copy to Particulars Analysis Git Repo
            self.copy_and_sync_to_git_all_csv_files()
            
                
    def start_TCT_measurement(self):
        if self.TCT_panel.TCT_main.sensor_name.text() == '300um_UIRAD' or self.TCT_panel.TCT_main.sensor_name.text() == '300_UIRAD':
            automatically_select_measurement_status = self.automatically_select_measurement_directory(measurement_type='300um_UIRAD_Reference', sensor_name='')
        else:
            automatically_select_measurement_status = self.automatically_select_measurement_directory(measurement_type='TCT', sensor_name=self.TCT_panel.TCT_main.sensor_name.text())
        
        if automatically_select_measurement_status == "user_response_dont_continue":
            return
        
        self.temperature_control_panel.current_directory_box.setPlainText(self.measurement_directory)
        self.TCT_panel.start_TCT_measurement(path=self.measurement_directory, 
                                             uncheck_start_after_finished_measurement_checkboxes=self.uncheck_start_after_finished_measurement_checkboxes)

    def stop_temperature_thread(self):
        self.stop_temp_thread.emit()
        sleep(2)
        self.temperature_thread.quit()
        self.temperature_thread.wait()

    def get_measurement_directory(self):
        return self.measurement_directory

    def select_measurement_directory(self):
        directory_selection = QFileDialog.getExistingDirectory(parent=self, caption='Select campaign directory',
                                                               dir=self.campaign_measurement_directory, options=QFileDialog.Option.ShowDirsOnly)
        if directory_selection:
            self.campaign_measurement_directory = directory_selection
            self.temperature_control_panel.current_directory_box.setPlainText(directory_selection)
        
        # Check status if the filename and directory already exist for IV, CV and TCT
        self.check_filename_directory_exist_add_status()
        
    def start_chiller(self):
        self.save_temperature_parameters()
        ret = self.environment_control.chiller.turn_on_off(mode='on')
        if isinstance(ret, str):
            QMessageBox.warning(self, 'Chiller Warning', ret)

    def stop_chiller(self):
        self.save_temperature_parameters()
        ret = self.environment_control.chiller.turn_on_off(mode='off')
        if isinstance(ret, str):
            QMessageBox.warning(self, 'Chiller Warning', ret)

    def toggle_peltiers(self):
        if not self._peltiers_active:
            self._peltiers_active = True
            self.save_temperature_parameters()
            self.temperature_control_panel.toggle_peltier_button.setText('Stop Peltier Elements')
            self.temperature_control_panel.set_peltier_indicator(mode=2)
        else:
            self._peltiers_active = False
            self.save_temperature_parameters()
            self.temperature_control_panel.toggle_peltier_button.setText('Start Peltier Elements')
            self.temperature_control_panel.set_peltier_indicator(mode=3)

    def live_peltier_indicator(self, in_operation: bool):
        if in_operation:
            self.temperature_control_panel.set_peltier_indicator(mode=1)
        elif self._peltiers_active:
            self.temperature_control_panel.set_peltier_indicator(mode=2)
        else:
            self.temperature_control_panel.set_peltier_indicator(mode=3)

    def save_temperature_parameters(self):
        temperature_config.write(config_directory=path.abspath('./'),
                                 target_temperature=self.temperature_control_panel.peltier_target_box.value(),
                                 voltage_output_on=self._peltiers_active,
                                 chiller_setpoint=self.temperature_control_panel.chiller_setpoint_box.value())
        self.temperature_control_panel.save_button.setEnabled(False)

    def start_measurement_thread_IV(self):
        self.start_measurement_thread(measurement_type='IV')

    def start_measurement_thread_CV(self):
        self.start_measurement_thread(measurement_type='CV')

    def switch_IV(self):
        self.environment_control.set_switchbox(measurement_type=3)
        self.environment_control.set_switchbox(measurement_type=3)
        self.environment_control.set_switchbox(measurement_type=3)
        self.temperature_control_panel.switch_info.setText('Switch Box: IV')

    def switch_CV(self):
        self.environment_control.set_switchbox(measurement_type=2)
        self.environment_control.set_switchbox(measurement_type=2)
        self.environment_control.set_switchbox(measurement_type=2)
        self.temperature_control_panel.switch_info.setText('Switch Box: CV')

    def switch_TCT(self):
        self.environment_control.set_switchbox(measurement_type=1)
        self.environment_control.set_switchbox(measurement_type=1)
        self.environment_control.set_switchbox(measurement_type=1)
        self.temperature_control_panel.switch_info.setText('Switch Box: TCT')


    def open_correction(self):
        self.open_c_status = 1
        self._measurement_active = True
        self.IV_panel.start_button.setEnabled(False)
        self.CV_panel.start_button.setEnabled(False)
        self.TCT_panel.TCT_main.start_measurement.setEnabled(False)
        # self.TCT_panel.TCT_main.log_toggle_button.setEnabled(False) # no log_toggle_button in laser_dev ? 

        self.temperature_control_panel.switch_info.setText('Switch Box: CV')
        self.measurement = MeasurementSequenceCV(plot_canvas=self.CV_panel.results_canvas, voltage_start=0, voltage_stop=0, voltage_step=0,
                                              compliance=self.IV_panel.compliance_value.value(), measure_delay=self.IV_panel.measure_delay.value(),
                                              sample_number=self.IV_panel.sample_number.value(), ramping_speed=self.CV_panel.ramping_speed.value(),
                                              lcr_voltage=self.CV_panel.vol_amplitude.value(), lcr_frequency=self.CV_panel.lcr_frequency.value(),
                                              set_switchbox=self.environment_control.set_switchbox, measurement_active=self.measurement_active,
                                              measurement_filename='', set_IV_indicator=self.IV_panel.set_measurement_indicator,
                                              set_CV_indicator=self.CV_panel.set_measurement_indicator, set_TCT_indicator=self.TCT_panel.TCT_main.set_measurement_indicator,
                                              open_c_status = 1, open_c_label = self.CV_panel.open_c_label,
                                              leakage_current_monitor=self.CV_panel.leakage_current_monitor,
                                              vbias_set_neg600=self.TCT_panel.vbias_set_neg600,
                                              timer_start_measurement_checkbox=self.CV_panel.timer_start_measurement_checkbox.isChecked(), 
                                              timer_value_start_measurement=self.CV_panel.timer_value_start_measurement.value())


        self.open_c_thread = QThread()
        self.measurement.moveToThread(self.open_c_thread)
        self.measurement.finished.connect(self.open_c_thread.quit)
        self.CV_panel.abort_button.clicked.connect(self.abort_open_c)
        self.open_c_thread.started.connect(self.measurement.execute_scan)
        self.open_c_thread.finished.connect(self.finish_measurement)
        
        self.CV_panel.abort_button.setEnabled(True)
        self.open_c_thread.start()
        
    def reconnect_chiller(self):
        # self.environment_control.chiller.reconnect()
        self.environment_control.reconnect_chiller()
    
    def reconnect_peltier(self):
        # self.environment_control.peltier.reconnect()
        self.environment_control.reconnect_peltier()

    def reconnect_pt1000(self):
        # self.environment_control.pt1000.reconnect()
        self.environment_control.reconnect_pt1000()

    def reconnect_arduino(self):
        # self.environment_control.arduino.reconnect()
        self.environment_control.reconnect_arduino()

    def reconnect_air_flow(self):
        # self.environment_control.air_flow.reconnect()
        self.environment_control.reconnect_air_flow()

    def set_value_air_flux(self, value):
        self.environment_control.air_flow.set_value(value)
        
    def voltage_polarity_warning(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Voltage Polarity Mismatch")

        msg.setText("<b>Warning:</b> The start and stop voltages have different polarities or the voltage is positive.<br><br>"
                    "Do you want to continue?<br><br>")
        
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        response = msg.exec_()

        if response == QMessageBox.No:
            return "no"
        else:
            return "yes"

    def start_measurement_thread(self, measurement_type: str = 'IV'):
        if self.TCT_panel.TCT_manual_control.vbias_status == "nonzero" or self.TCT_panel.TCT_manual_control.osc_toggle_status == "on":
            vbias_status = "✅ Vbias is zero" if self.TCT_panel.TCT_manual_control.vbias_status == "zero" else "❌ Vbias is NOT zero"
            osc_toggle_status = "✅ Oscilloscope is NOT toggled" if self.TCT_panel.TCT_manual_control.osc_toggle_status == "off" else "❌ Oscilloscope is toggled"
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("System Readiness Check")
            
            msg.setText("<b>Manual Control Status:</b><br><br>"
                    f"{vbias_status}<br>"
                    f"{osc_toggle_status}<br><br>"
                    "<b>Please ensure Manual Control under TCT is not on.</b>")
    
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        

        if measurement_type == 'IV':
            if self.IV_panel.voltage_settings.voltage_ramp_start.value() * self.IV_panel.voltage_settings.voltage_ramp_stop.value() < 0 or self.IV_panel.voltage_settings.voltage_ramp_start.value() > 0 or self.IV_panel.voltage_settings.voltage_ramp_stop.value() > 0:
                if self.voltage_polarity_warning() == "no":
                    return
            self.IV_CV_panel = self.IV_panel
        elif measurement_type == 'CV':
            if self.CV_panel.voltage_settings.voltage_ramp_start.value() * self.CV_panel.voltage_settings.voltage_ramp_stop.value() < 0 or self.CV_panel.voltage_settings.voltage_ramp_start.value() > 0 or self.CV_panel.voltage_settings.voltage_ramp_stop.value() > 0:
                if self.voltage_polarity_warning() == "no":
                    return
            self.IV_CV_panel = self.CV_panel

        # Automatically select measurement directory. Also check if measurement directory is within the valid campaign/reference path
        if self.automatically_select_measurement_directory(measurement_type=measurement_type, sensor_name=self.TCT_panel.TCT_main.sensor_name.text()) == "user_response_dont_continue":
            return 
        measurement_pre_filename = self.check_filename(measurement_type='IV_CV')
        self.temperature_control_panel.current_directory_box.setPlainText(self.measurement_directory)
        if measurement_pre_filename == '':
            return

        print(f"\nRunning {measurement_type} measurement...")
        if measurement_type not in ['IV', 'CV']:
            raise ValueError('The measurement type must be "IV" or "CV"!')
        
        self._measurement_active = True
        self.IV_panel.start_button.setEnabled(False)
        self.CV_panel.start_button.setEnabled(False)

        self.TCT_panel.TCT_main.start_measurement.setEnabled(False)

        # Disable Set 0, -6, 600, Set, On, Off buttons on TCT panel manual control
        self.enable_disable_TCT_manual_control_buttons(enable=False)

        if measurement_type == 'IV':
            self.temperature_control_panel.switch_info.setText('Switch Box: IV')
            self.measurement = MeasurementSequenceIV(plot_canvas=self.IV_panel.results_canvas, voltage_start=self.IV_panel.voltage_settings.voltage_ramp_start.value(),
                                              voltage_stop=self.IV_panel.voltage_settings.voltage_ramp_stop.value(), voltage_step=self.IV_panel.voltage_settings.voltage_ramp_step.value(),
                                              compliance=self.IV_panel.compliance_value.value(), measure_delay=self.IV_panel.measure_delay.value(),
                                              sample_number=self.IV_panel.sample_number.value(), ramping_speed=self.IV_panel.ramping_speed.value(),
                                              set_switchbox=self.environment_control.set_switchbox,
                                              measurement_active=self.measurement_active, measurement_filename=measurement_pre_filename+'.csv',
                                              set_IV_indicator=self.IV_panel.set_measurement_indicator, set_CV_indicator=self.CV_panel.set_measurement_indicator,
                                              set_TCT_indicator=self.TCT_panel.TCT_main.set_measurement_indicator,
                                              receive_ramp_to_neg600V_checkbox_status_IV=self.receive_ramp_to_neg600V_checkbox_status_IV,
                                              uncheck_start_after_finished_measurement_checkboxes=self.uncheck_start_after_finished_measurement_checkboxes,
                                              vbias_set_neg600=self.TCT_panel.vbias_set_neg600, 
                                              timer_start_measurement_checkbox=self.IV_panel.timer_start_measurement_checkbox.isChecked(),
                                              timer_value_start_measurement=self.IV_panel.timer_value_start_measurement.value(),
                                              start_temperature_log=self.environment_control.start_temperature_log,
                                              )
        elif measurement_type == 'CV':
            self.temperature_control_panel.switch_info.setText('Switch Box: CV')
            self.measurement = MeasurementSequenceCV(plot_canvas=self.CV_panel.results_canvas, voltage_start=self.CV_panel.voltage_settings.voltage_ramp_start.value(),
                                              voltage_stop=self.CV_panel.voltage_settings.voltage_ramp_stop.value(), voltage_step=self.CV_panel.voltage_settings.voltage_ramp_step.value(),
                                              voltage_fine_stop=self.CV_panel.voltage_settings.voltage_fine_stop.value(), voltage_fine_step=self.CV_panel.voltage_settings.voltage_fine_ramp.value(),
                                              voltage_fine_checkbox = self.CV_panel.voltage_settings.fine_voltage_checkbox.isChecked(),
                                              compliance=self.IV_panel.compliance_value.value(), measure_delay=self.IV_panel.measure_delay.value(),
                                              sample_number=self.IV_panel.sample_number.value(), ramping_speed=self.CV_panel.ramping_speed.value(),
                                              lcr_voltage=self.CV_panel.vol_amplitude.value(), lcr_frequency=self.CV_panel.lcr_frequency.value(),
                                              set_switchbox=self.environment_control.set_switchbox, measurement_active=self.measurement_active,
                                              measurement_filename=measurement_pre_filename+'.csv', set_IV_indicator=self.IV_panel.set_measurement_indicator,
                                              set_CV_indicator=self.CV_panel.set_measurement_indicator,
                                              set_TCT_indicator=self.TCT_panel.TCT_main.set_measurement_indicator, open_c_status = 0, open_c_label = self.CV_panel.open_c_label,
                                              leakage_current_monitor=self.CV_panel.leakage_current_monitor,
                                              receive_ramp_to_neg600V_checkbox_status_CV=self.receive_ramp_to_neg600V_checkbox_status_CV,
                                              uncheck_start_after_finished_measurement_checkboxes=self.uncheck_start_after_finished_measurement_checkboxes,
                                              vbias_set_neg600=self.TCT_panel.vbias_set_neg600,
                                              timer_start_measurement_checkbox=self.CV_panel.timer_start_measurement_checkbox.isChecked(),
                                              timer_value_start_measurement=self.CV_panel.timer_value_start_measurement.value(),
                                              start_temperature_log=self.environment_control.start_temperature_log,
                                              )

        self.measurement_thread = QThread()
        self.measurement.moveToThread(self.measurement_thread)
        self.measurement.finished.connect(self.measurement_thread.quit)
        self.IV_CV_panel.abort_button.clicked.connect(self.abort_measurement)
        self.measurement_thread.started.connect(self.measurement.execute_scan)
        self.measurement_thread.finished.connect(self.finish_measurement)
        
        self.IV_CV_panel.abort_button.setEnabled(True)
        self.measurement_thread.start()

    def abort_open_c(self):
        self._measurement_active = False
        self.CV_panel.abort_button.setEnabled(False)

    def abort_measurement(self):
        print("\nAborting measurement...")
        self.temperature_control_panel.current_directory_box.setPlainText(self.campaign_measurement_directory)
        self._measurement_active = False
        self.IV_CV_panel.abort_button.setEnabled(False)

    def measurement_active(self):
        return self._measurement_active

    def finish_measurement(self):
         
        if hasattr(self, 'open_c_status'):
            if not self.open_c_status:
                self.environment_control.stop_temperature_log()
                if hasattr(self, 'measurement_thread') and self.measurement_thread and self.measurement_thread.isRunning():  
                    self.measurement_thread.quit()
                    self.measurement_thread.wait()
                # self.measurement_thread.deleteLater()
            else: 
                if hasattr(self, 'open_c_thread') and self.open_c_thread and self.open_c_thread.isRunning():  
                    self.open_c_thread.quit()
                    self.open_c_thread.wait()
                # self.open_c_thread.deleteLater()
        else:
            self.environment_control.stop_temperature_log()
            if hasattr(self, 'measurement_thread') and self.measurement_thread and self.measurement_thread.isRunning():  
                self.measurement_thread.quit()
                self.measurement_thread.wait()
        self.open_c_status = 0
        self.environment_control.set_switchbox(measurement_type=1)
        self.environment_control.set_switchbox(measurement_type=1)
        self.environment_control.set_switchbox(measurement_type=1)
        self.temperature_control_panel.switch_info.setText('Switch Box: TCT')
        self._measurement_active = False
        self.IV_CV_panel.abort_button.setEnabled(False)
        self.IV_panel.start_button.setEnabled(True)
        self.CV_panel.start_button.setEnabled(True)
        self.TCT_panel.TCT_main.start_measurement.setEnabled(True)

        # Enable Set 0, -6, 600, Set, On, Off buttons on TCT panel manual control again after measurement is finished
        self.enable_disable_TCT_manual_control_buttons(enable=True)

        self.temperature_control_panel.current_directory_box.setPlainText(self.campaign_measurement_directory)
        print("\nMeasurement stopped successfully.")

        # Check status if the filename and directory already exist for IV, CV and TCT
        self.check_filename_directory_exist_add_status() 

        # Check if the start after current measurement checkbox is checked, only one checkbox can be checked at a time
        # This gives priority order of IV --> CV --> TCT
        self.start_IV_CV_TCT_after_finished_measurement()

        # Uncheck the start after current measurement checkboxes once a measurement is finished to not start a loop
        # self.uncheck_start_after_finished_measurement_checkboxes()


    def enable_disable_TCT_manual_control_buttons(self, enable: bool):
        self.TCT_panel.TCT_manual_control.vbias_set_0_button.setEnabled(enable)
        self.TCT_panel.TCT_manual_control.vbias_set_neg6_button.setEnabled(enable)
        self.TCT_panel.TCT_manual_control.vbias_set_neg600_button.setEnabled(enable)
        self.TCT_panel.TCT_manual_control.vbias_set.setEnabled(enable)
        self.TCT_panel.TCT_manual_control.osc_on.setEnabled(enable)
        # osc_off is already disabled when running IV and CV measurements

    def toggle_temperature_log(self):
        if not self._measurement_active:
            measurement_pre_filename = self.check_filename(measurement_type='TCT')
            if measurement_pre_filename == '':
                return

            self._measurement_active = True
            self.IV_panel.start_button.setEnabled(False)
            self.CV_panel.start_button.setEnabled(False)
            self.IV_panel.set_measurement_indicator(mode=4)
            self.CV_panel.set_measurement_indicator(mode=4)
            self.environment_control.start_temperature_log(measurement_filename=measurement_pre_filename+'_temperature.csv')
            self.TCT_panel.TCT_main.set_measurement_indicator(mode=1)
        else:
            self._measurement_active = False
            self.environment_control.stop_temperature_log()
            self.TCT_panel.TCT_main.set_measurement_indicator(mode=2)
            self.IV_panel.start_button.setEnabled(True)
            self.CV_panel.start_button.setEnabled(True)
            self.IV_panel.set_measurement_indicator(mode=2)
            self.CV_panel.set_measurement_indicator(mode=2)
    
    def check_filename(self, measurement_type: str) -> str:
        """
        This method checks if the selected filename is valid and was not already used before.
        If the filename should not be used, an empty string is returned.

        :param measurement_type: string; The measurement type must be "IV_CV" or "TCT".
        :return: string; If the filename is valid, the file path without ".csv" is returned.
            If the filename is not valid, an empty string "" is returned.
        """

        if measurement_type == 'IV_CV':
            measurement_pre_filename = self.measurement_directory+'/'+self.IV_CV_panel.filename_field.text() 
        elif measurement_type == 'TCT':
            measurement_pre_filename = self.measurement_directory+'/'+self.TCT_panel.TCT_main.directory_label_TCT.text().split(' ')[-1] 
        else:
            raise ValueError('The parameter "measurement_type" must be "IV_CV" or "TCT"!')

        if path.isfile(measurement_pre_filename+'.csv') or path.isfile(measurement_pre_filename+'_temperature.csv') or path.isdir(measurement_pre_filename):
            folder_confirmation = QMessageBox()
            folder_confirmation.setWindowTitle('Filename Warning')
            folder_confirmation.setText('The selected filename was already used for a measurement! Are you sure you want to use this filename?')
            folder_confirmation.setInformativeText(measurement_pre_filename+'.csv\n' + measurement_pre_filename+'_temperature.csv')
            folder_confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            folder_confirmation.setDefaultButton(QMessageBox.StandardButton.No)
            ret = folder_confirmation.exec()
            if ret == QMessageBox.StandardButton.No:
                return ''

        if self.IV_CV_panel.filename_field.text() == '':
            filename_error_message = QMessageBox()
            filename_error_message.setWindowTitle('Filename Warning')
            filename_error_message.setText('No filename was selected. Please enter a filename!')
            filename_error_message.setStandardButtons(QMessageBox.StandardButton.Ok)
            filename_error_message.setDefaultButton(QMessageBox.StandardButton.Ok)
            filename_error_message.exec()
            return ''
        
        return measurement_pre_filename
    

    def apply_sensor_name_change(self):
        sensor_name = self.TCT_panel.TCT_main.sensor_name.text()
        temp = self.TCT_panel.TCT_main.sensor_temp.text()
        addText = self.TCT_panel.TCT_main.additional_text.text()
        last_element_addText = addText.split('_')[-1].lower() # usually noadd|min|days
        date = datetime.now().strftime("%y%m%d")

        # Check if last_element_addText is noadd, otherwise check if there is an directory that matches with the sensor name
        if last_element_addText != "noadd" and sensor_name not in ["300um_UIRAD", "300_UIRAD"]:
            sensor_dir_IVCV_onPCB_exists, sensor_dir_TCT_exists = self.check_sensor_directory_already_exist() # return (bool, bool)

            if sensor_dir_IVCV_onPCB_exists == True:
                message_status_IVCV_onPCB = f"✅ {sensor_name} exist in IVCV_onPCB directory<br>"
            else:
                message_status_IVCV_onPCB = f"❌ {sensor_name} does not exist in IVCV_onPCB directory<br>"

            if sensor_dir_TCT_exists == True:
                message_status_TCT = f"✅ {sensor_name} exist in TCT directory<br><br>"
            else: 
                message_status_TCT = f"❌ {sensor_name} does not exist in TCT directory<br><br>"

            if sensor_dir_IVCV_onPCB_exists == False or sensor_dir_TCT_exists == False:
                sensor_dir_exist_confirmation = QMessageBox()
                sensor_dir_exist_confirmation.setWindowTitle('Directory Warning')
                sensor_dir_exist_confirmation.setText(
                    "<b>Sensor Name Warning:</b><br><br>"
                    f"{message_status_IVCV_onPCB}"
                    f"{message_status_TCT}"
                    "Mismatch! Current sensor name doesn't match with previous directory. Sensor name might be misspelled, please double check. <br><br>"
                    "<b>Are you sure you want to continue?</b>"
                )
                sensor_dir_exist_confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                sensor_dir_exist_confirmation.setDefaultButton(QMessageBox.StandardButton.No)
                user_response = sensor_dir_exist_confirmation.exec()
                if user_response == QMessageBox.StandardButton.No:
                    return

        if sensor_name == "300um_UIRAD" or sensor_name == "300_UIRAD":
            # Clear IV and CV filename fields for 300um_UIRAD reference sensor measurements
            self.IV_panel.filename_field.setText("")
            self.CV_panel.filename_field.setText("")
            self.TCT_panel.TCT_main.directory_label_TCT.setText(f"<b>Directory:&nbsp;&nbsp;&nbsp;&nbsp;</b> {sensor_name}_{temp}_{date}_{addText}")

            # Set standard values for 300um_UIRAD reference sensor measurements
            self.campaign_measurement_directory = REFERENCE_UIRAD_DIODE_DIRECTORY
            self.change_campaign_measurement_directory_label()
            self.TCT_panel.TCT_voltage_source.voltage_settings.voltage_ramp_start.setValue(-700)
            self.TCT_panel.TCT_voltage_source.voltage_settings.voltage_ramp_stop.setValue(-400)
            self.TCT_panel.TCT_voltage_source.voltage_settings.voltage_ramp_step.setValue(100)
            self.TCT_panel.TCT_voltage_source.voltage_settings.fine_voltage_checkbox.setChecked(False)
            self.TCT_panel.TCT_voltage_source.voltage_settings.voltage_fine_start.setEnabled(False)
            self.TCT_panel.TCT_voltage_source.voltage_settings.voltage_fine_ramp.setEnabled(False)
        else:
            # check if the last element of the addText contains "noadd", "min", "days"
            valid_annealing_time_units = ["noadd", "min", "days", "d"]

            if any(last_element_addText.endswith(unit) for unit in valid_annealing_time_units):
                valid_unit = True
            else:
                valid_unit = False
            
            if valid_unit == False:
                unit_addText_confirmation = QMessageBox()
                unit_addText_confirmation.setWindowTitle('Unit Warning')
                unit_addText_confirmation.setText(
                    "<b>Unit Warning:</b><br><br>"
                    "❌ Additional text is not ending with a valid unit, {'noadd', 'min', 'days', 'd'}!<br><br>"
                    "<b>Are you sure you want to continue?</b>"
                )
                unit_addText_confirmation.setInformativeText(addText)
                unit_addText_confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                unit_addText_confirmation.setDefaultButton(QMessageBox.StandardButton.No)
                ret = unit_addText_confirmation.exec()
                if ret == QMessageBox.StandardButton.No:
                    return

            self.IV_panel.filename_field.setText(sensor_name+'_'+addText.split('_')[-1]+'_IV')
            self.CV_panel.filename_field.setText(sensor_name+'_'+addText.split('_')[-1]+'_CV')
            self.TCT_panel.TCT_main.directory_label_TCT.setText(f"<b>Directory:&nbsp;&nbsp;&nbsp;&nbsp;</b> {sensor_name+'_'+temp+'_'+date+'_'+addText}")

        # Check status if the filename and directory already exist for IV, CV and TCT
        self.check_filename_directory_exist_add_status()  

        # Change Analysis directory to the new sensor name for easier analysis of previous measurements
        analysis_directory = self.campaign_measurement_directory + '/TCT/' + sensor_name
        self.TCT_panel.TCT_analysis.current_directory_box.setPlainText(analysis_directory)
        self.TCT_panel.analysis_directory = analysis_directory
    
    def automatically_select_measurement_directory(self, measurement_type: str, sensor_name: str):
        # Check if the campaign measurement directory is valid with the current campaign and reference folder to minimize human mistakes

        # Normalize all valid campaign paths
        valid_campaign_reference_paths = [
            os.path.normpath(HIGH_FLUENCE_NEUTRONS_DIRECTORY),
            os.path.normpath(LOW_FLUENCE_NEUTRONS_DIRECTORY),
            os.path.normpath(DOUBLE_IRR_NEUTRON_DIRECTORY),
            os.path.normpath(PROTON_CAMPAIGN_DIRECTORY),
            os.path.normpath(REFERENCE_UIRAD_DIODE_DIRECTORY),
        ]
        
        # Normalize the current campaign measurement directory
        self.campaign_measurement_directory = os.path.normpath(self.campaign_measurement_directory)

        if (self.campaign_measurement_directory not in valid_campaign_reference_paths) and not measurement_type == "initial":
            campaign_folder_confirmation = QMessageBox()
            campaign_folder_confirmation.setWindowTitle('Campaign Folder Warning')
            campaign_folder_confirmation.setText(
                "<b>Campaign Folder Warning:</b><br><br>"
                "❌ The selected campaign folder is not in the list of valid campaign folders!<br><br>"
                "<b>Are you sure you want to continue?</b>"
            )
            campaign_folder_confirmation.setInformativeText(self.campaign_measurement_directory)
            campaign_folder_confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            campaign_folder_confirmation.setDefaultButton(QMessageBox.StandardButton.No)
            ret = campaign_folder_confirmation.exec()
            if ret == QMessageBox.StandardButton.No:
                return "user_response_dont_continue"

        if measurement_type == 'IV' or measurement_type == 'CV':
            self.measurement_directory = self.campaign_measurement_directory + '/IVCV_onPCB/' + sensor_name
            os.makedirs(self.measurement_directory, exist_ok=True)
        elif measurement_type == 'TCT':
            self.measurement_directory = self.campaign_measurement_directory + '/TCT/' + sensor_name
            os.makedirs(self.measurement_directory, exist_ok=True)
        elif measurement_type == '300um_UIRAD_Reference':
            self.measurement_directory = REFERENCE_UIRAD_DIODE_DIRECTORY
        else:
            self.measurement_directory = self.campaign_measurement_directory
        return "continue"

    def change_campaign_measurement_directory_label(self):
        self.temperature_control_panel.current_directory_box.setPlainText(self.campaign_measurement_directory)


    def copy_IVCV_csv_files(self, root_folder):
        valid_annealing_time_units_IV = ["noadd_IV.csv", "min_IV.csv", "days_IV.csv", "d_IV.csv"] # ends with UNIT_IV to make it more specific
        valid_annealing_time_units_CV = ["noadd_CV.csv", "min_CV.csv", "days_CV.csv", "d_CV.csv"] # ends with UNIT_CV to make it more specific
        destination_folder_IV = os.path.join(root_folder, "_IV_ALL_CSV")
        destination_folder_CV = os.path.join(root_folder, "_CV_ALL_CSV")

        # Create destination folders if they don't exist
        main_folders_Git_Particulars_Analysis = [
            "ProtonIrr2024",
            "DoubleIrrNeutron2025",
            "HighFluenceIrrNeutron2023",
            "LowFluenceIrrNeutron2025"
        ]

        subfolders_Git_Particulars_Analysis = ["IV_onPCB", "CV_onPCB", "TCT"]

        for folder in main_folders_Git_Particulars_Analysis:
            for sub in subfolders_Git_Particulars_Analysis:
                path = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", folder, sub)
                os.makedirs(path, exist_ok=True)
    
        # Create destination for IV and CV all within each root folder
        os.makedirs(destination_folder_IV, exist_ok=True)
        os.makedirs(destination_folder_CV, exist_ok=True)
        
        # Create destination for temperature files
        temperature_files_destination = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "TemperatureFiles")
        os.makedirs(temperature_files_destination, exist_ok=True)

        for dirpath, _, filenames in os.walk(root_folder):
            if dirpath == destination_folder_IV or dirpath == destination_folder_CV:
                continue  # Skip the destination folder itself
            dirpath_parts = dirpath.lower().split(os.sep)
            if any(part.endswith(("_old", "-old")) for part in dirpath_parts):
                continue # skip folder if named (or its parent folders) with old in the end as it indicates a remeasurement has been done or unused directories

            # Check which campaign the measurement belongs to
            if "Proton_Campaign" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "ProtonIrr2024")
            elif "Double_Irr_Neutron" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "DoubleIrrNeutron2025")
            elif "High_Fluence_neutrons_2023" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "HighFluenceIrrNeutron2023")
            elif "low_fluence_neutrons_2025" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "LowFluenceIrrNeutron2025")

            for file in filenames:
                source_path = None
                source_path_temperature_files = None

                # Skip files that doesn't include valid annealing units in the filename as they are usually created for testing purposes
                if any(file.endswith(unit) for unit in valid_annealing_time_units_IV):
                    source_path = os.path.join(dirpath, file)
                    destination_path = os.path.join(destination_folder_IV, file)
                    destination_path_Git_Particulars_Analysis = os.path.join(path_campaign_Git_Particulars_Analysis, "IV_onPCB", file)
                elif any(file.endswith(unit) for unit in valid_annealing_time_units_CV):
                    source_path = os.path.join(dirpath, file)
                    destination_path = os.path.join(destination_folder_CV, file)
                    destination_path_Git_Particulars_Analysis = os.path.join(path_campaign_Git_Particulars_Analysis, "CV_onPCB", file)
                elif file.endswith("_temperature.csv") and COPY_TEMPERATURE_FILES:
                    source_path_temperature_files = os.path.join(dirpath, file)
                    
                    # Open the file and read the first line (header)
                    with open(source_path_temperature_files, "r", encoding="utf-8") as f:
                        header = f.readline().strip()

                    # Extract the date inside parentheses -> e.g. "08.04.2025"
                    match = re.search(r"\((\d{2}\.\d{2}\.\d{4})\)", header)
                    if match:
                        date_str_raw = match.group(1)  # "08.04.2025"
                        # Convert to desired format YYMMDD -> "250408"
                        day, month, year = date_str_raw.split(".")
                        date_str = f"{year[2:]}{month}{day}"
                    else:
                        # Fallback if no date found
                        date_str = "unknown"

                    # Insert date into filename
                    filename, ext = os.path.splitext(file)
                    new_filename = f"{filename}_{date_str}{ext}"

                    destination_path_temperature_files = os.path.join(temperature_files_destination, new_filename)
                else:
                    continue  # Skip irrelevant files including old measurements

                # Check if file is larger than 0 bytes which indicates that a measurement is running, only copy finished measurements.
                if source_path is not None:
                    if os.path.getsize(source_path) == 0:
                        print(f"File is empty: {source_path}, skipping...")
                        continue

                # Copy to _ALL_CSV folder and Git Particulars Analysis, overwrite if file already exists
                if self.overwrite_current_files and source_path is not None:
                    shutil.copy2(source_path, destination_path)
                    print(f"Copied: {source_path} -> {destination_path}")
                    shutil.copy2(source_path, destination_path_Git_Particulars_Analysis)
                    print(f"Copied: {source_path} -> {destination_path_Git_Particulars_Analysis}")
                elif not self.overwrite_current_files and source_path is not None:
                    if not os.path.exists(destination_path):
                        shutil.copy2(source_path, destination_path)
                        print(f"Copied: {source_path} -> {destination_path}")
                        shutil.copy2(source_path, destination_path_Git_Particulars_Analysis)
                        print(f"Copied: {source_path} -> {destination_path_Git_Particulars_Analysis}")
                        
                # Copy temperature files to Particulars Analysis Git Repo
                if COPY_TEMPERATURE_FILES and file.endswith("_temperature.csv") and source_path_temperature_files is not None:
                    if not os.path.exists(destination_path_temperature_files):
                        shutil.copy2(source_path_temperature_files, destination_path_temperature_files)
                        print(f"Copied: {source_path_temperature_files} -> {destination_path_temperature_files}")

                
    def copy_TCT_csv_files(self, root_folder):
        valid_endswith_annealing_time_units = ["noadd.csv", "min.csv", "days.csv", "d.csv"]
        destination_folder = os.path.join(root_folder, "_TCT_ALL_CSV")
        os.makedirs(destination_folder, exist_ok=True)
    
        for dirpath, _, filenames in os.walk(root_folder):
            if dirpath == destination_folder:
                continue  # Skip the destination folder itself, .i.e. _TCT_ALL_CSV
            dirpath_parts = dirpath.lower().split(os.sep)
            if any(part.endswith(("_old", "-old")) for part in dirpath_parts):
                continue # skip folder if named (or its parent folders) with old in the end as it indicates a remeasurement has been done or unused directories

            # Check which campaign the measurement belongs to
            if "Proton_Campaign" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "ProtonIrr2024")
            elif "Double_Irr_Neutron" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "DoubleIrrNeutron2025")
            elif "High_Fluence_neutrons_2023" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "HighFluenceIrrNeutron2023")
            elif "low_fluence_neutrons_2025" in dirpath:
                path_campaign_Git_Particulars_Analysis = os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data", "LowFluenceIrrNeutron2025")

        
            for file in filenames:
                if file.lower().startswith("beam_monitor"):
                    continue
                if any(file.endswith(unit) for unit in valid_endswith_annealing_time_units):
                    source_path = os.path.join(dirpath, file)
                    destination_path = os.path.join(destination_folder, file)
                    destination_path_Git_Particulars_Analysis = os.path.join(path_campaign_Git_Particulars_Analysis, "TCT", file)
                    
                    # Check if file is larger than 0 bytes which indicates that a measurement is running, only copy finished measurements.
                    if os.path.getsize(source_path) == 0:
                        print(f"File is empty: {source_path}, skipping...")
                        continue

                    # Copy to _TCT_ALL_CSV folder and Git Particulars Analysis, overwrite if file already exists
                    if self.overwrite_current_files:
                        shutil.copy2(source_path, destination_path)
                        print(f"Copied: {source_path} -> {destination_path}")
                        shutil.copy2(source_path, destination_path_Git_Particulars_Analysis)
                        print(f"Copied: {source_path} -> {destination_path_Git_Particulars_Analysis}")
                    else:
                        if not os.path.exists(destination_path):
                            shutil.copy2(source_path, destination_path)
                            print(f"Copied: {source_path} -> {destination_path}")
                            shutil.copy2(source_path, destination_path_Git_Particulars_Analysis)
                            print(f"Copied: {source_path} -> {destination_path_Git_Particulars_Analysis}")
        
    def git_pull_push_sync_Git_Particulars_Analysis(self):
        # try:
        repo = Repo(path.abspath(PARTICULARS_ANALYSIS_DIRECTORY))
        origin = repo.remote(name='origin')
        origin.pull()
        repo.git.add(os.path.join(PARTICULARS_ANALYSIS_DIRECTORY, "Data/*"))

        # Check if there are any changes to commit
        if repo.index.diff('HEAD'):
            repo.git.commit('-m', f'Sync CSV files from Particulars Computer. Done on {datetime.now().strftime("%d.%m.%Y")}')
            origin.push()
            print(f'\nSynced CSV files to Particulars Analysis Repository')
        else:
            print("No changes to commit")


    def copy_and_sync_to_git_all_csv_files(self):
        # Copy all IV and CV files to _IV_ALL_CSV and _CV_ALL_CSV in the target folder and copy to Particulars Analysis Git Repo
        folder_to_search = [os.path.join(HIGH_FLUENCE_NEUTRONS_DIRECTORY, "IVCV_onPCB"), os.path.join(LOW_FLUENCE_NEUTRONS_DIRECTORY, "IVCV_onPCB"), os.path.join(DOUBLE_IRR_NEUTRON_DIRECTORY, "IVCV_onPCB"), os.path.join(PROTON_CAMPAIGN_DIRECTORY, "IVCV_onPCB")]
        for folder in folder_to_search:
            self.copy_IVCV_csv_files(folder)

        # Copy all TCT files to _TCT_ALL_CSV in the target folder
        folder_to_search = [os.path.join(HIGH_FLUENCE_NEUTRONS_DIRECTORY, "TCT"), os.path.join(LOW_FLUENCE_NEUTRONS_DIRECTORY, "TCT"), os.path.join(DOUBLE_IRR_NEUTRON_DIRECTORY, "TCT"), os.path.join(PROTON_CAMPAIGN_DIRECTORY, "TCT")]
        for folder in folder_to_search:
            self.copy_TCT_csv_files(folder)

        self.git_pull_push_sync_Git_Particulars_Analysis()

    def check_filename_directory_exist_add_status(self):
        if self.TCT_panel.TCT_main.sensor_name.text() in ['300um_UIRAD', '300_UIRAD']:
            self.IV_panel.filename_status_label_IV.setText('')
            self.CV_panel.filename_status_label_CV.setText('')
            self.TCT_panel.TCT_main.directory_status_label_TCT.setText('')
        else:
            sensor_name = self.TCT_panel.TCT_main.sensor_name.text()
            filename_IV = self.IV_panel.filename_field.text()
            filename_CV = self.CV_panel.filename_field.text()
            directory_TCT = self.TCT_panel.TCT_main.directory_label_TCT.text().split(' ')[-1]

            directory_to_search_IV_CV = os.path.join(self.campaign_measurement_directory, 'IVCV_onPCB', sensor_name)
            directory_to_search_TCT = os.path.join(self.campaign_measurement_directory, 'TCT', sensor_name)

            if os.path.isfile(os.path.join(directory_to_search_IV_CV, filename_IV + '.csv')):
                self.IV_panel.filename_status_label_IV.setText('✅ Sensor measured')
            else:
                self.IV_panel.filename_status_label_IV.setText('⏳ To be measured')

            if os.path.isfile(os.path.join(directory_to_search_IV_CV, filename_CV + '.csv')):
                self.CV_panel.filename_status_label_CV.setText('✅ Sensor measured')
            else:
                self.CV_panel.filename_status_label_CV.setText('⏳ To be measured')

            directory_TCT_parts = directory_TCT.split('_')
            directory_annealing_step = directory_TCT_parts[-1]

            directory_TCT_match = False
            if os.path.isdir(directory_to_search_TCT):
                for entry in os.listdir(directory_to_search_TCT):
                    if entry.startswith(sensor_name) and entry.endswith(directory_annealing_step):
                        full_path = os.path.join(directory_to_search_TCT, entry)
                        if os.path.isdir(full_path):
                            directory_TCT_match = True
                            break

            if directory_TCT_match:
                self.TCT_panel.TCT_main.directory_status_label_TCT.setText('✅ Sensor measured')
            else:
                self.TCT_panel.TCT_main.directory_status_label_TCT.setText('⏳ To be measured')
                

    def check_sensor_directory_already_exist(self):
        sensor_name = self.TCT_panel.TCT_main.sensor_name.text()
        sensor_dir_IVCV_onPCV = os.path.join(self.campaign_measurement_directory, 'IVCV_onPCB', sensor_name)
        sensor_dir_TCT = os.path.join(self.campaign_measurement_directory, 'TCT', sensor_name)

        sensor_dir_IVCV_onPCB_exists = os.path.exists(sensor_dir_IVCV_onPCV)
        sensor_dir_TCT_exists = os.path.exists(sensor_dir_TCT)

        return sensor_dir_IVCV_onPCB_exists, sensor_dir_TCT_exists
    

    def uncheck_start_after_finished_measurement_checkboxes(self):
        self.IV_panel.start_after_finished_measurement_checkbox_IV.setChecked(False)
        self.CV_panel.start_after_finished_measurement_checkbox_CV.setChecked(False)
        self.TCT_panel.TCT_main.start_after_finished_measurement_checkbox_TCT.setChecked(False)
        

    def receive_ramp_to_neg600V_checkbox_status_CV(self):
        return self.CV_panel.ramp_to_neg600V_CV_checkbox.isChecked()
        
        
    def receive_ramp_to_neg600V_checkbox_status_IV(self):
        return self.IV_panel.ramp_to_neg600V_IV_checkbox.isChecked()
    

    def start_IV_CV_TCT_after_finished_measurement(self):
        """ 
        Checks if checkboxes are True/False to start another measurement when current measurement is finished.
        With priority order of IV --> CV --> TCT.
        """
        if self.IV_panel.start_after_finished_measurement_checkbox_IV.isChecked():
            self.start_measurement_thread(measurement_type='IV')
            self.IV_panel.start_after_finished_measurement_checkbox_IV.setChecked(False)
        elif self.CV_panel.start_after_finished_measurement_checkbox_CV.isChecked():
            self.start_measurement_thread(measurement_type='CV')
            self.CV_panel.start_after_finished_measurement_checkbox_CV.setChecked(False)
        elif self.TCT_panel.TCT_main.start_after_finished_measurement_checkbox_TCT.isChecked():
            self.start_TCT_measurement()
            self.TCT_panel.TCT_main.start_after_finished_measurement_checkbox_TCT.setChecked(False)
        
    def overwrite_sync_files_checkbox_state_changed(self, overwrite_current_files = False):
        self.overwrite_current_files = overwrite_current_files

    def check_previous_voltage_settings_measurements(self, CV_or_TCT: str = 'CV'):
        check_previous_voltage_settings(sensor_name=self.TCT_panel.TCT_main.sensor_name.text(), campaign_measurement_directory=self.campaign_measurement_directory, CV_or_TCT=CV_or_TCT)