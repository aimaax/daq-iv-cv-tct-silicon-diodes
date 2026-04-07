import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QSizePolicy, QTabWidget, QMessageBox
from PySide6.QtCore import QThread
import os

from DAQ.AXIOM.GUI_TCT.TCTMainTabPanel import TCTMainTabPanel
from DAQ.AXIOM.GUI_TCT.LaserPanel.LaserPanel import LaserPanel
from DAQ.AXIOM.GUI_TCT.OscilloscopePanel import OscilloscopePanel
from DAQ.AXIOM.GUI_TCT.TCTVoltageSourcePanel import TCTVoltageSourcePanel
from DAQ.AXIOM.GUI_TCT.ManualControlPanel import ManualControlPanel
from DAQ.AXIOM.GUI_TCT.AnalysisPanel import AnalysisPanel
from DAQ.AXIOM.GUI_TCT.AutoAlignPanel import AutoAlignPanel
from DAQ.AXIOM.GUI_TCT.TopTCTScanPanel import TopTCTScanPanel

from DAQ.AXIOM.Devices.Laser.LaserPos.LaserPos import LaserPos
from DAQ.AXIOM.Devices.Laser.LaserSettings.LaserSettings import LaserSettings
from DAQ.AXIOM.Devices.Oscillocope import Oscilloscope
from DAQ.AXIOM.Devices.OscilloScopeHSI import OscilloscopeHSI
from DAQ.AXIOM.Devices.ke2410 import ke2410  # power supply

from DAQ.AXIOM.Utils.MeasurementSequences.MeasurementSequenceTCT import MeasurementSequenceTCT
from DAQ.AXIOM.Utils.MeasurementSequences.TCTAnalysisSequence import TCTAnalysisSequence
from DAQ.AXIOM.Utils.MeasurementSequences.TCTAreaScanSequence import TCTAreaScanSequence
from DAQ.AXIOM.Utils.MeasurementSequences.TCTFocusScanSequence import TCTFocusScanSequence

from config import MOTOR_STAGES_SPEED_DEFAULT, LASER_MAX_STRENGTH, OSCILLOSCOPEHSI


class TCTPanel(QWidget):

    def __init__(self, start_measurement, set_CV_indicator, set_IV_indicator, apply_sensor_name_change, 
                 change_campaign_measurement_directory_label, check_filename_directory_exist_add_status,
                 start_IV_CV_TCT_after_finished_measurement, check_previous_voltage_settings):
        super().__init__()
        layout = QVBoxLayout()

        self.motorsLaser = LaserPos()
        self.settingsLaser = LaserSettings()

        self._measurement_active = False
        self._analysis_active = False
        self._alignment_active = False
        self._area_scan_active = False
        self._focus_scan_active = False

        self.change_campaign_measurement_directory_label = change_campaign_measurement_directory_label
        self.check_filename_directory_exist_add_status = check_filename_directory_exist_add_status
        self.start_IV_CV_TCT_after_finished_measurement = start_IV_CV_TCT_after_finished_measurement
        self.analysis_directory = os.path.abspath('./DAQ/AXIOM/')
        # print(self.analysis_directory)

        self.X = 1 #Left to right
        self.Y = 0 #Front to back
        self.Z = 2 #Up and down

        #This variable stores the position steps and usteps for each stage motor
        self.Xpos_zero = [0,0]
        self.Ypos_zero = [0,0]
        self.Zpos_zero = [0,0]
        
        self.TCT_tabs = QTabWidget()
        self.TCT_tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.TCT_main = TCTMainTabPanel(start_measurement=start_measurement, default_settings=self.default_settings, abort_measurement=self.abort_measurement, 
                                 disconnect_TCT_devices=self.disconnect_TCT_devices, connect_TCT_devices=self.connect_TCT_devices,
                                 apply_sensor_name_change=apply_sensor_name_change)
        self.TCT_main.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.TCT_main, 'Main')
        self.TCT_laser = LaserPanel(checkLaser=self.checkLaser, setFreq=self.setFreq, laserOff=self.laserOff, laserDisconnect=self.laserDisconnect, laser_reconnect = self.laser_reconnect, DACOn=self.DACOn, DACOff=self.DACOff, setDAC=self.setDAC,
                                   swap_x_y=self.swap_x_y, move_motors=self.move_motors, clear_sequence=self.clear_sequence, 
                                   load_sequence=self.load_sequence, start_sequence=self.start_sequence, set_pulse_duration=self.set_pulse_duration,
                                   enable_ext_interrupts=self.enable_ext_interrupts, enable_timer_interrupts=self.enable_timer_interrupts, send_seq_period=self.send_seq_period,
                                   set_zero=self.set_zero, move_x_left=self.move_x_left, move_x_right=self.move_x_right, move_y_left=self.move_y_left, move_y_right=self.move_y_right, move_z_left=self.move_z_left, move_z_right=self.move_z_right,
                                   motor_stages_connect=self.motor_stages_connect, motor_stages_disconnect=self.motor_stages_disconnect)
        self.TCT_laser.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.TCT_laser, 'Laser')
        self.TCT_osc = OscilloscopePanel(osc_connect=self.osc_connect, osc_disconnect=self.osc_disconnect, recall_setup=self.recall_setup,
                               save_setup=self.save_setup)
        self.TCT_osc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.TCT_osc, 'Oscilloscope')
        self.TCT_voltage_source = TCTVoltageSourcePanel(vsource_connect=self.vsource_connect, vsource_disconnect=self.vsource_disconnect, check_previous_voltage_settings=check_previous_voltage_settings)
        self.TCT_voltage_source.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.TCT_voltage_source, 'Voltage Source')
        self.TCT_manual_control = ManualControlPanel(vbias_set=self.vbias_set, vbias_set_0=self.vbias_set_0, vbias_set_neg6=self.vbias_set_neg6, vbias_set_neg600=self.vbias_set_neg600, 
                                                     osc_on=self.osc_on, osc_off=self.abort_measurement, 
                                                     move_x_left=self.move_x_left, move_x_right=self.move_x_right, 
                                                     move_y_left=self.move_y_left, move_y_right=self.move_y_right)
        self.TCT_manual_control.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.TCT_manual_control, 'Manual Control')
        self.TCT_analysis = AnalysisPanel(get_measurement_directory=self.get_measurement_directory, select_measurement_directory=self.select_measurement_directory, start_analysis=self.start_analysis, abort_analysis=self.abort_analysis)
        self.TCT_analysis.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.TCT_analysis, 'Analysis')
        self.top_TCT_scan = TopTCTScanPanel(start_area_scan=self.start_area_scan, abort_area_scan=self.abort_area_scan, start_focus_scan=self.start_focus_scan, abort_focus_scan=self.abort_focus_scan)
        self.top_TCT_scan.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.TCT_tabs.addTab(self.top_TCT_scan, 'Top TCT Scan')

        layout.addWidget(self.TCT_tabs)
        self.setLayout(layout)

        self.set_IV_indicator = set_IV_indicator
        self.set_CV_indicator = set_CV_indicator
        self.set_TCT_indicator = self.TCT_main.set_measurement_indicator
        
        self.checkLaser()
        self.default_settings()

    def measurement_active(self):
        return self._measurement_active

    def analysis_active(self):
        return self._analysis_active
    
    def alignment_active(self):
        return self._alignment_active
    
    def area_scan_active(self):
        return self._area_scan_active
    
    def focus_scan_active(self):
        return self._focus_scan_active
    
    def start_focus_scan(self):
        try:
            self.top_TCT_scan.AS_start_scan.setEnabled(False)
            self.top_TCT_scan.AS_abort_scan.setEnabled(False)
            self.top_TCT_scan.FS_start_scan.setEnabled(False)
            self.top_TCT_scan.FS_abort_scan.setEnabled(True)
            self.top_TCT_scan.set_top_TCT_scan_indicator(mode=3)

            # --- Set indicator to show that focus scan is ongoing ---   
            self.set_IV_indicator(mode=4)
            self.set_CV_indicator(mode=4)
            self.TCT_main.set_measurement_indicator(mode=4)

            # --- Start focus scan --- 
            self._focus_scan_active = True
            self.focus_scan_control = TCTFocusScanSequence(
                start_pos_xy=self.top_TCT_scan.FS_initial_position_xy.value(),
                start_pos_z=self.top_TCT_scan.FS_initial_position_z.value(),
                step_size_xy=self.top_TCT_scan.FS_step_size_xy.value(),
                step_size_z=self.top_TCT_scan.FS_step_size_z.value(),
                num_steps_xy=self.top_TCT_scan.FS_num_steps_xy.value(),
                num_steps_z=self.top_TCT_scan.FS_num_steps_z.value(),
                voltage=self.top_TCT_scan.FS_voltage_value.value(),
                ramping_interval=self.TCT_voltage_source.ramping_interval.value(),
                ramping_step=self.TCT_voltage_source.ramping_speed.value(),
                set_top_TCT_scan_indicator=self.top_TCT_scan.set_top_TCT_scan_indicator,
                motors=self.motorsLaser,
                osc=self.osc,
                keithley2410=self.keithley2410,
                area_scan_active=self.area_scan_active,
                plot_canvas=self.top_TCT_scan.FS_results_canvas,
                xy_choice=self.top_TCT_scan.FS_xy_choice.text()
            )

            self.focus_scan_thread = QThread()
            self.focus_scan_control.moveToThread(self.focus_scan_thread)
            self.focus_scan_control.error_occurred.connect(self.handle_focus_scan_error)
            self.focus_scan_control.finished.connect(self.focus_scan_thread.quit)
            self.focus_scan_thread.started.connect(self.focus_scan_control.perform_focus_scan)
            self.focus_scan_thread.finished.connect(self.finished_focus_scan)
            self.focus_scan_thread.start()
        except Exception as e:
            print(f"Error starting focus scan: {e}")
            self.top_TCT_scan.AS_start_scan.setEnabled(True)
            self.top_TCT_scan.AS_abort_scan.setEnabled(False)
            self.top_TCT_scan.FS_start_scan.setEnabled(True)
            self.top_TCT_scan.FS_abort_scan.setEnabled(False)
            self.top_TCT_scan.set_top_TCT_scan_indicator(mode=1)
            self.set_IV_indicator(mode=2)
            self.set_CV_indicator(mode=2)
            self.TCT_main.set_measurement_indicator(mode=2)

    def handle_focus_scan_error(self, error_message):
        print(error_message)
        self.abort_focus_scan()
        self.finished_focus_scan()

    def abort_focus_scan(self):
        print("Aborting Focus Scan...")
        self._focus_scan_active = False

    def finished_focus_scan(self):
        print("Focus Scan stopping...")
        self._focus_scan_active = False
        self.top_TCT_scan.AS_start_scan.setEnabled(True)
        self.top_TCT_scan.AS_abort_scan.setEnabled(False)
        self.top_TCT_scan.FS_start_scan.setEnabled(True)
        self.top_TCT_scan.FS_abort_scan.setEnabled(False)
        self.top_TCT_scan.set_top_TCT_scan_indicator(mode=1)
        self.TCT_main.set_measurement_indicator(mode=2)
        self.set_IV_indicator(mode=2)
        self.set_CV_indicator(mode=2)
        if hasattr(self, 'focus_scan_thread') and self.focus_scan_thread and self.focus_scan_thread.isRunning():
            self.focus_scan_thread.quit()
            self.focus_scan_thread.wait()
        print("Focus Scan stopped successfully.")

    def start_area_scan(self):
        try:
            self.top_TCT_scan.AS_start_scan.setEnabled(False)
            self.top_TCT_scan.AS_abort_scan.setEnabled(True)
            self.top_TCT_scan.FS_start_scan.setEnabled(False)
            self.top_TCT_scan.FS_abort_scan.setEnabled(False)
            self.top_TCT_scan.set_top_TCT_scan_indicator(mode=2)

            # --- Set indicator to show that alignment is ongoing --- 
            self.set_IV_indicator(mode=4)
            self.set_CV_indicator(mode=4)
            self.TCT_main.set_measurement_indicator(mode=4)

            # --- Start area scan --- 
            self._area_scan_active = True
            self.area_scan_control = TCTAreaScanSequence(
                start_pos_x=self.top_TCT_scan.AS_initial_position_x.value(),
                start_pos_y=self.top_TCT_scan.AS_initial_position_y.value(),
                step_size_x=self.top_TCT_scan.AS_step_size_x.value(),
                step_size_y=self.top_TCT_scan.AS_step_size_y.value(),
                num_steps_x=self.top_TCT_scan.AS_num_steps_x.value(),
                num_steps_y=self.top_TCT_scan.AS_num_steps_y.value(),
                voltage=self.top_TCT_scan.AS_voltage_value.value(),
                ramping_interval=self.TCT_voltage_source.ramping_interval.value(),
                ramping_step=self.TCT_voltage_source.ramping_speed.value(),
                set_top_TCT_scan_indicator=self.top_TCT_scan.set_top_TCT_scan_indicator,
                motors=self.motorsLaser,
                osc=self.osc,
                keithley2410=self.keithley2410,
                area_scan_active=self.area_scan_active,
                plot_canvas=self.top_TCT_scan.AS_results_canvas
            )

            self.area_scan_thread = QThread()
            self.area_scan_control.moveToThread(self.area_scan_thread)
            self.area_scan_control.error_occurred.connect(self.handle_area_scan_error)
            self.area_scan_control.finished.connect(self.area_scan_thread.quit)
            self.area_scan_thread.started.connect(self.area_scan_control.perform_area_scan)
            self.area_scan_thread.finished.connect(self.finished_area_scan)
            self.area_scan_thread.start()
        except Exception as e:
            print(f"Error starting area scan: {e}")
            self.top_TCT_scan.AS_start_scan.setEnabled(True)
            self.top_TCT_scan.AS_abort_scan.setEnabled(False)
            self.top_TCT_scan.FS_start_scan.setEnabled(True)
            self.top_TCT_scan.FS_abort_scan.setEnabled(False)
            self.top_TCT_scan.set_top_TCT_scan_indicator(mode=1)
            self.set_IV_indicator(mode=2)
            self.set_CV_indicator(mode=2)
            self.TCT_main.set_measurement_indicator(mode=2)

    def handle_area_scan_error(self, error_message):
        print(error_message)
        self.abort_area_scan()
        self.finished_area_scan()

    def abort_area_scan(self):
        print("Aborting Area Scan...")
        self._area_scan_active = False

    def finished_area_scan(self):
        print("Area Scan stopping...")
        self._area_scan_active = False
        self.top_TCT_scan.AS_start_scan.setEnabled(True)
        self.top_TCT_scan.AS_abort_scan.setEnabled(False)
        self.top_TCT_scan.FS_start_scan.setEnabled(True)
        self.top_TCT_scan.FS_abort_scan.setEnabled(False)
        self.top_TCT_scan.set_top_TCT_scan_indicator(mode=1)
        self.TCT_main.set_measurement_indicator(mode=2)
        self.set_IV_indicator(mode=2)
        self.set_CV_indicator(mode=2)
        if hasattr(self, 'area_scan_thread') and self.area_scan_thread and self.area_scan_thread.isRunning():
            self.area_scan_thread.quit()
            self.area_scan_thread.wait()
        print("Area Scan stopped successfully.")

    def abort_analysis(self):
        print("TCT Analysis stopped successfully.")
        self._analysis_active = False
        self.TCT_analysis.start_analysis.setEnabled(True)
        self.TCT_analysis.abort_analysis.setEnabled(False)
        self.TCT_analysis.set_analysis_indicator(mode=3)


    def start_analysis(self):
        print("\nRunning TCT Analysis.")
        self.TCT_analysis.start_analysis.setEnabled(False)
        self.TCT_analysis.abort_analysis.setEnabled(True)
        path = self.get_measurement_directory()

        self._analysis_active = True
        self.TCT_analysis_seq = TCTAnalysisSequence(voltage_start=self.TCT_analysis.voltage_settings.voltage_ramp_start.value(), voltage_step=self.TCT_analysis.voltage_settings.voltage_ramp_step.value(), voltage_stop=self.TCT_analysis.voltage_settings.voltage_ramp_stop.value(),
                                                analysis_active=self.analysis_active, path=path, plot_canvas=self.TCT_analysis.results_canvas)

        self.analysis_thread = QThread()
        self.analysis_thread.started.connect(self.TCT_analysis_seq.perform_analysis)
        self.analysis_thread.finished.connect(self.abort_analysis)
        self.TCT_analysis_seq.finished.connect(self.analysis_thread.quit)
        self.TCT_analysis.set_analysis_indicator(mode=2)

        self.TCT_analysis_seq.moveToThread(self.analysis_thread)
        self.analysis_thread.start()

    def get_measurement_directory(self):
        return self.analysis_directory
    
    def select_measurement_directory(self):
        directory_selection = QFileDialog.getExistingDirectory(parent=self, caption='Select the measurement directory',
                                                               dir=self.analysis_directory, options=QFileDialog.Option.ShowDirsOnly)
        if directory_selection:
            self.analysis_directory = directory_selection
            # self.TCT_analysis.current_directory_box.setText(directory_selection)
            self.TCT_analysis.current_directory_box.setPlainText(directory_selection)
            self.TCT_analysis.set_analysis_indicator(mode=1)

    def default_settings(self):
        if self.TCT_main.default_checkbox.isChecked() == True:
            self.TCT_osc.wf_per_vbias.setEnabled(False)
            self.TCT_osc.points_per_wf.setEnabled(False)
            self.TCT_osc.record_channel.setEnabled(False)
            self.TCT_voltage_source.advanced_settings.setEnabled(False)
        elif self.TCT_main.default_checkbox.isChecked() == False:
            self.TCT_osc.wf_per_vbias.setEnabled(True)
            self.TCT_osc.points_per_wf.setEnabled(True)
            self.TCT_osc.record_channel.setEnabled(True)
            self.TCT_voltage_source.advanced_settings.setEnabled(True)
            return
        return

    def start_TCT_measurement(self, path, uncheck_start_after_finished_measurement_checkboxes):
        if not (self.TCT_osc.osc_ready and self.TCT_voltage_source.vsource_ready and self.TCT_laser.laser_ready):
            osc_status = "✅ Oscilloscope is ready" if self.TCT_osc.osc_ready else "❌ Oscilloscope is NOT ready"
            vsource_status = "✅ Voltage Source is ready" if self.TCT_voltage_source.vsource_ready else "❌ Voltage Source is NOT ready"
            laser_status = "✅ Laser is ready" if self.TCT_laser.laser_ready else "❌ Laser is NOT ready"

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("System Readiness Check")
            
            msg.setText("<b>System Status:</b><br><br>"
                    f"{osc_status}<br>"
                    f"{vsource_status}<br>"
                    f"{laser_status}<br><br>"
                    "<b>Please ensure all systems are ready before proceeding.</b>")
    
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        if self.TCT_voltage_source.voltage_settings.voltage_ramp_start.value() * self.TCT_voltage_source.voltage_settings.voltage_ramp_stop.value() < 0 or self.TCT_voltage_source.voltage_settings.voltage_ramp_start.value() > 0 or self.TCT_voltage_source.voltage_settings.voltage_ramp_stop.value() > 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Voltage Polarity Mismatch")

            msg.setText("<b>Warning:</b> The start and stop voltages have different polarities or the voltage is positive.<br><br>"
                        "Do you want to continue?<br><br>")
            
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            response = msg.exec_()

            if response == QMessageBox.No:
                return
            
        sensorName = self.TCT_main.sensor_name.text()
        temp = self.TCT_main.sensor_temp.text()
        addText = self.TCT_main.additional_text.text()
        year = time.strftime("%y")
        month = time.strftime("%m")
        day = time.strftime("%d")
        date = year+month+day
        directory = sensorName+"_"+temp+"_"+date+"_"+addText
        path = os.path.join(path, directory) 
        
        # Raise a warning if the filename already exists and stop the TCT from running
        if os.path.exists(path):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            msg.setText(f"The directory '{directory}' was already used for another measurement!")
            msg.setInformativeText("Please choose a different filename or delete the existing one.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        os.mkdir(path)
        pathDir = path+r'\\'
        pathLog = os.path.join(path, "Logs")
        os.mkdir(pathLog) 
        
        
        self.TCT_main.start_measurement.setEnabled(False)
        self.TCT_main.abort_measurement.setEnabled(True)
        self.TCT_manual_control.osc_on.setEnabled(False) 
        self.TCT_manual_control.osc_off.setEnabled(True)
        self.TCT_main.set_measurement_indicator(mode=1)

        self._measurement_active = True
        self.TCT_measurement = MeasurementSequenceTCT(
            set_IV_indicator=self.set_IV_indicator, set_CV_indicator=self.set_CV_indicator, set_TCT_indicator=self.set_TCT_indicator, display_curr=self.TCT_main.display_curr,
            display_volt=self.TCT_main.display_volt, display_event=self.TCT_main.display_event, measurement_active=self.measurement_active, osc=self.osc, plot_canvas=self.TCT_main.results_canvas,
            channel=self.TCT_osc.record_channel.currentText(), beam_monitor_channel=self.TCT_osc.second_record_channel.currentText(), points_per_wf=str(self.TCT_osc.points_per_wf.value()),
            keithley2410=self.keithley2410, amount_wf = self.TCT_osc.wf_per_vbias.value(), directory=pathDir, date=date, sensorName=sensorName, temp=temp, addText=addText, voltage_start=self.TCT_voltage_source.voltage_settings.voltage_ramp_start.value(), 
            voltage_step=self.TCT_voltage_source.voltage_settings.voltage_ramp_step.value(), voltage_stop=self.TCT_voltage_source.voltage_settings.voltage_ramp_stop.value(), 
            voltage_fine_checkbox = self.TCT_voltage_source.voltage_settings.fine_voltage_checkbox.isChecked(), voltage_fine_start=self.TCT_voltage_source.voltage_settings.voltage_fine_start.value(), voltage_fine_step=self.TCT_voltage_source.voltage_settings.voltage_fine_ramp.value(),
            user=self.TCT_main.user_name.text(), comment=self.TCT_main.comments.text(),
            compliance=self.TCT_voltage_source.compliance_value.value(), measure_delay=self.TCT_voltage_source.measure_delay.value(), 
            ramping_speed=self.TCT_voltage_source.ramping_speed.value(), ramping_interval=self.TCT_voltage_source.ramping_interval.value(),
            uncheck_start_after_finished_measurement_checkboxes=uncheck_start_after_finished_measurement_checkboxes
            )

        self.measurement_thread = QThread()
        self.TCT_measurement.moveToThread(self.measurement_thread)
        self.TCT_measurement.error_occurred.connect(self.handle_TCT_measurement_error)
        self.TCT_measurement.finished.connect(self.measurement_thread.quit)
        self.measurement_thread.started.connect(self.TCT_measurement.execute_scan)
        self.measurement_thread.finished.connect(lambda: self.finish_TCT_measurement(path))
        self.measurement_thread.start()

    def osc_on(self):
        if self.osc_connected == False:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            msg.setText(f"Oscilloscope is not connected!")
            msg.setInformativeText("Please connect the oscilloscope before turning on the manual control.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        self.TCT_main.start_measurement.setEnabled(False)
        self.TCT_main.abort_measurement.setEnabled(True)
        self.TCT_manual_control.osc_on.setEnabled(False)
        self.TCT_manual_control.osc_off.setEnabled(True)
        self.TCT_manual_control.manual_control_status(device = "osc", mode = 1) 

        self._measurement_active = True
        self.osc_manual_control = MeasurementSequenceTCT(
            set_IV_indicator=self.set_IV_indicator, set_CV_indicator=self.set_CV_indicator, set_TCT_indicator=self.set_TCT_indicator, 
            display_curr=self.TCT_manual_control.display_curr, display_volt="", display_event="", measurement_active=self.measurement_active, 
            osc=self.osc, plot_canvas=self.TCT_manual_control.results_canvas, 
            channel=self.TCT_osc.record_channel.currentText(), beam_monitor_channel=self.TCT_osc.second_record_channel.currentText(), points_per_wf=str(self.TCT_osc.points_per_wf.value()),
            keithley2410=self.keithley2410, amount_wf = self.TCT_osc.wf_per_vbias.value(), directory="", date="", sensorName="", temp="", addText="", voltage_start=self.TCT_voltage_source.voltage_settings.voltage_ramp_start.value(), 
            voltage_step=self.TCT_voltage_source.voltage_settings.voltage_ramp_step.value(), voltage_stop=self.TCT_voltage_source.voltage_settings.voltage_ramp_stop.value(), 
            voltage_fine_checkbox = False, voltage_fine_start=0, voltage_fine_step=0,
            user=self.TCT_main.user_name.text(), comment=self.TCT_main.comments.text(),
            compliance=self.TCT_voltage_source.compliance_value.value(), measure_delay=self.TCT_voltage_source.measure_delay.value(), 
            ramping_speed=self.TCT_voltage_source.ramping_speed.value(), ramping_interval=self.TCT_voltage_source.ramping_interval.value()
            )
        

        self.manual_control_thread = QThread()
        self.osc_manual_control.moveToThread(self.manual_control_thread)
        self.osc_manual_control.error_occurred.connect(self.handle_manual_control_measurement_error) # handles raised exceptations
        self.osc_manual_control.finished.connect(self.manual_control_thread.quit)
        self.manual_control_thread.started.connect(self.osc_manual_control.manual_control)
        self.manual_control_thread.finished.connect(self.finish_manual_control_measurement)
        self.manual_control_thread.start()

    def handle_TCT_measurement_error(self, error_message):
        print(error_message)
        self.abort_measurement()
        self.finish_TCT_measurement()

    def handle_manual_control_measurement_error(self, error_message):
        print(error_message)
        self.abort_measurement()
        self.finish_manual_control_measurement()

    def abort_measurement(self):
        print("\nAborting measurement...")
        self._measurement_active = False
        
    def finish_TCT_measurement(self, path = None):
        self.change_campaign_measurement_directory_label()
        self.TCT_main.set_measurement_indicator(mode=2)
        self.set_IV_indicator(mode=2)
        self.set_CV_indicator(mode=2)
        self._measurement_active = False
        self.TCT_main.start_measurement.setEnabled(True)
        self.TCT_main.abort_measurement.setEnabled(False)
        self.TCT_manual_control.osc_on.setEnabled(True)
        self.TCT_manual_control.osc_off.setEnabled(False)
        self.TCT_manual_control.manual_control_status(device = "osc", mode = 0)
        if hasattr(self, 'manual_control_thread') and self.manual_control_thread and self.manual_control_thread.isRunning():  
            self.manual_control_thread.quit()
            self.manual_control_thread.wait()
        if hasattr(self, 'measurement_thread') and self.measurement_thread and self.measurement_thread.isRunning():  
            self.measurement_thread.quit()
            self.measurement_thread.wait()
        print("\nMeasurement stopped successfully")

        # Set vbias box to 0 as the measurement has ramped down the voltage to 0V.
        self.TCT_manual_control.vbias.setValue(0)
        self.vbias_set()

        if path is not None:
            # Analyse the TCT measurement directly after it has finished
            # 1. Change directory in the analysis panel to the new measurement directory
            self.analysis_directory = path
            self.TCT_analysis.current_directory_box.setPlainText(path)
            # 2. Start the TCT analysis 
            self.start_analysis()

        # Update status if the filename and directory already exist for IV, CV and TCT
        self.check_filename_directory_exist_add_status() 

        # Check if the checkboxes are checked to start another measurement after TCT is finished
        self.start_IV_CV_TCT_after_finished_measurement()
        

    def finish_manual_control_measurement(self):
        self.change_campaign_measurement_directory_label()
        self.TCT_main.set_measurement_indicator(mode=2)
        self.set_IV_indicator(mode=2)
        self.set_CV_indicator(mode=2)
        self._measurement_active = False
        self.TCT_main.start_measurement.setEnabled(True)
        self.TCT_main.abort_measurement.setEnabled(False)
        self.TCT_manual_control.osc_on.setEnabled(True)
        self.TCT_manual_control.osc_off.setEnabled(False)
        self.TCT_manual_control.manual_control_status(device = "osc", mode = 0)
        if hasattr(self, 'manual_control_thread') and self.manual_control_thread and self.manual_control_thread.isRunning():  
            self.manual_control_thread.quit()
            self.manual_control_thread.wait()
        if hasattr(self, 'measurement_thread') and self.measurement_thread and self.measurement_thread.isRunning():  
            self.measurement_thread.quit()
            self.measurement_thread.wait()
        print("\nMeasurement stopped successfully")
    

    def connect_TCT_devices(self):
        """ Connect all TCT devices. """
        self.osc_connect()
        self.vsource_connect()
        self.DACOn()
        self.setDAC()
        self.setFreq()
        self.recall_setup()

    def disconnect_TCT_devices(self):
        """ Disconnect all TCT devices, i.e. release them from memory allocation, in able to do measurements in LabView. """
        self.vsource_disconnect()
        self.osc_disconnect()
        self.laserDisconnect()
        self.motor_stages_disconnect()

    def vbias_set(self):
        voltage = self.TCT_manual_control.vbias.value()
        if voltage > 0:
            voltage_status = "❌ Voltage can't be set to positive"
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            
            msg.setText("<b>Warning:</b><br><br>"
                    f"{voltage_status}<br><br>"
                    "<b>Please ensure voltage is set to negative.</b>")
    
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        self.keithley2410.set_output_on()
        ramping_speed = self.TCT_voltage_source.ramping_speed.value()
        ramping_interval = self.TCT_voltage_source.ramping_interval.value()
        self.keithley2410.ramp_voltage(voltage, ramping_step=ramping_speed, time_interval=ramping_interval)
        self.TCT_manual_control.voltage_ramp_status.setText("Status: " + f"Voltage is now at {voltage}V")
        cur_tot = self.keithley2410.read_current()
        self.TCT_manual_control.display_curr.setText("Current(A): " + f"{cur_tot}")
        
        # Add control status of the manual control panel to prevent IV/CV measurement to run if vbias and toggle oscilloscope is on and non zero
        if voltage == 0:
            self.TCT_manual_control.manual_control_status(device = "vbias", mode = 0)
        elif voltage != 0:
            self.TCT_manual_control.manual_control_status(device = "vbias", mode = 1)

    def vbias_set_0(self):
        self.TCT_manual_control.vbias.setValue(0)
        self.vbias_set()

    def vbias_set_neg6(self):
        self.TCT_manual_control.vbias.setValue(-6)
        self.vbias_set()

    def vbias_set_neg600(self):
        self.TCT_manual_control.vbias.setValue(-600)
        self.vbias_set()
        

    def vsource_connect(self):
        ## KEITHLEY settings
        self.lim_cur_ke2410 = self.TCT_voltage_source.compliance_value.value() * 1e-6  # compliance in [A]
        keithley2410_address = self.TCT_voltage_source.vsource_gpib.text() # in the SSD lab gpib address of the power supply that does the TCT scan
        self.keithley2410 = ke2410(keithley2410_address)
        self.TCT_voltage_source.set_vsource_indicator(mode=1)

    def vsource_disconnect(self):
        """ Reset power supply for TCT measurement """
        try:
            if self.keithley2410 is not None:
                print('\nTrying to disconnect voltage source...')
                self.keithley2410.ramp_down()
                self.keithley2410.set_output_off()
                self.keithley2410.reset()
                self.keithley2410.set_source('voltage')
                self.keithley2410.set_sense('current')
                self.keithley2410.set_current_limit(self.lim_cur_ke2410)
                self.keithley2410.set_voltage(0)
                self.keithley2410.set_terminal('rear')
                self.keithley2410.set_output_off()
                
                # Set to None so it is properly disconnect for other programs to connect
                del self.keithley2410
                self.keithley2410 = None

                self.TCT_voltage_source.set_vsource_indicator(mode=0)
                print("\nVoltage source disconnected successfully.")
            else:
                print("\nVoltage source is already disconnected.")
        except Exception as e:
            print(f"\nError during voltage source disconnection: {e}")
        finally:
            time.sleep(1) 
            
        # self.keithley2410.ramp_down()
        # self.keithley2410.set_output_off()
        # self.keithley2410.reset()
        # self.keithley2410.set_source('voltage')
        # self.keithley2410.set_sense('current')
        # self.keithley2410.set_current_limit(self.lim_cur_ke2410)
        # self.keithley2410.set_voltage(0)
        # self.keithley2410.set_terminal('rear')
        # self.keithley2410.set_output_off()
        # self.TCT_voltage_source.set_vsource_indicator(mode=0)
        # time.sleep(1)

    def save_setup(self):
        file = self.TCT_osc.setup_name.text()
        self.osc.save_setup(file)
        self.TCT_osc.set_osc_indicator(mode=2)

    def recall_setup(self):
        file = self.TCT_osc.setup_name.text()
        self.osc.recall_setup(file)
        self.TCT_osc.set_osc_indicator(mode=3)
        
    def osc_connect(self):
        visa_address = self.TCT_osc.osc_visa.currentText()
        if not OSCILLOSCOPEHSI:
            self.osc = Oscilloscope(visa_address=visa_address) # visa_address = TCPIPO::128.141.104.233::inst0::INSTR
        else:
            self.osc = OscilloscopeHSI(visa_address=visa_address) # ip_address = 128.141.104.233
        self.TCT_osc.set_osc_indicator(mode=1)
        self.osc_connected = True

    def osc_disconnect(self):
        try:
            print("\nTrying to disconnect oscilloscope...")
            if self._measurement_active:
                self.abort_measurement()
                self.finish_manual_control_measurement()
            
            # Properly close the oscilloscope connection
            if self.osc is not None:
                self.osc.close_osc()  
                self.osc = None  
                
                # Update the GUI to reflect the disconnection
                self.TCT_osc.set_osc_indicator(mode=0)
                self.osc_connected = False
                print("\nOscilloscope disconnected successfully.")
            else:
                print("\nOscilloscope is already disconnected.")
        except Exception as e:
            print(f"\nError during oscilloscope disconnection: {e}")

    def checkLaser(self, raise_exceptation = False):
        try:
            if self.motorsLaser is not None:
                motors = self.motorsLaser.checkMotors()
            else: 
                motors = 0
            self.TCT_laser.set_motors_indicator(mode=motors)

            if self.settingsLaser is not None:
                device = self.settingsLaser.checkDevice()
            else: 
                device = False

            if self.motorsLaser is not None:
                speed = self.motorsLaser.getMotorSpeed(self.X)
                self.positionX = self.motorsLaser.getMotorPosition(self.X)
            else:
                speed = MOTOR_STAGES_SPEED_DEFAULT
                self.positionX = (0, 0)
            
            # if self.settingsLaser is not None:
            self.TCT_laser.laser_stage_control.set_same_speed.setValue(speed)
            self.TCT_laser.laser_stage_control.x_from.setText("Position: " + str(self.positionX[0]-self.Xpos_zero[0]) + " steps, " + str(self.positionX[1]-self.Xpos_zero[1]) + " microsteps")
            self.TCT_laser.laser_stage_control.set_x_step.setValue(self.positionX[0]-self.Xpos_zero[0])
            self.TCT_manual_control.x_axis_position_step.setValue(self.positionX[0]-self.Xpos_zero[0])
            self.TCT_laser.laser_stage_control.set_x_ustep.setValue(self.positionX[1]-self.Xpos_zero[1])
            self.TCT_laser.laser_stage_control.set_x_speed.setValue(speed)

            if self.motorsLaser is not None:
                speed = self.motorsLaser.getMotorSpeed(self.Y)
                self.positionY = self.motorsLaser.getMotorPosition(self.Y)
            else:
                speed = MOTOR_STAGES_SPEED_DEFAULT
                self.positionY = (0, 0)
            
            # if self.settingsLaser is not None:
            self.TCT_laser.laser_stage_control.y_from.setText("Position: " + str(self.positionY[0]-self.Ypos_zero[0]) + " steps, " + str(self.positionY[1]-self.Ypos_zero[1]) + " microsteps")
            self.TCT_laser.laser_stage_control.set_y_step.setValue(self.positionY[0]-self.Ypos_zero[0])
            self.TCT_manual_control.y_axis_position_step.setValue(self.positionY[0]-self.Ypos_zero[0])
            self.TCT_laser.laser_stage_control.set_y_ustep.setValue(self.positionY[1]-self.Ypos_zero[1])
            self.TCT_laser.laser_stage_control.set_y_speed.setValue(speed)

            if self.motorsLaser is not None:
                self.positionZ = self.motorsLaser.getMotorPosition(self.Z)
                speed = self.motorsLaser.getMotorSpeed(self.Z)
            else:
                speed = MOTOR_STAGES_SPEED_DEFAULT
                self.positionZ = (0, 0)

            # if self.settingsLaser is not None:
            self.TCT_laser.laser_stage_control.z_from.setText("Position: " + str(self.positionZ[0]-self.Zpos_zero[0]) + " steps, " + str(self.positionZ[1]-self.Zpos_zero[1]) + " microsteps")
            self.TCT_laser.laser_stage_control.set_z_step.setValue(self.positionZ[0]-self.Zpos_zero[0])
            self.TCT_laser.laser_stage_control.set_z_ustep.setValue(self.positionZ[1]-self.Zpos_zero[1])
            self.TCT_laser.laser_stage_control.set_z_speed.setValue(speed)

            if self.settingsLaser is not None:
                laser = self.settingsLaser.checkLaserState()
            else:
                laser = False

            if device & laser:
                self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(True)
                self.TCT_laser.set_freq_button.setEnabled(True)
                self.TCT_laser.set_laser_indicator(mode=1)
                self.top_TCT_scan.set_top_TCT_scan_indicator(mode=1)
            elif device:
                self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(True)
                self.TCT_laser.set_freq_button.setEnabled(True)
                self.TCT_laser.set_laser_indicator(mode=2)
                self.top_TCT_scan.set_top_TCT_scan_indicator(mode=0)
            else:
                self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(False)
                self.TCT_laser.set_freq_button.setEnabled(False)
                self.TCT_laser.set_laser_indicator(mode=4)
                self.top_TCT_scan.set_top_TCT_scan_indicator(mode=0)
        
            if motors == 3:
                self.TCT_laser.laser_stage_control.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
                self.TCT_manual_control.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
                self.TCT_laser.laser_stage_control.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f') 
                self.TCT_manual_control.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
                self.TCT_laser.laser_stage_control.z_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            else:           
                self.TCT_laser.laser_stage_control.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
                self.TCT_manual_control.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
                self.TCT_laser.laser_stage_control.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
                self.TCT_manual_control.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
                self.TCT_laser.laser_stage_control.z_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')

        except Exception as e:
            print(f"\nAn error occurred in checkLaser: {e}")
            self.TCT_laser.set_laser_indicator(mode=4)  
            self.top_TCT_scan.set_top_TCT_scan_indicator(mode=0)
            self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(False)
            self.TCT_laser.set_freq_button.setEnabled(False)
            if raise_exceptation:
                raise

    def setFreq(self):
        freq = self.TCT_laser.laser_freq_box.value()
        self.settingsLaser.setLaserFrequency(int(freq))
        time.sleep(1)
        self.checkLaser()

    def laserOff(self):
        self.settingsLaser.turnLaserOff()
        self.checkLaser()

    def laser_reconnect(self):
        try:
            print('\nTrying to reconnect laser...')

            # Reinitialize the laser settings
            # self.motorsLaser = LaserPos()
            self.settingsLaser = LaserSettings()

            # Reset variables
            self._alignment_active = False
            self._measurement_active = False

            # Check laser
            self.settingsLaser.turnLaserOff()
            self.checkLaser(raise_exceptation=True) 
            
            print("\nLaser has been reconnected successfully.")
        except:
            print(f'\nFailed to reconnect laser. Another program might be occupying the laser.')
            

        
    def laserDisconnect(self):
        if self._alignment_active:
            self.abort_auto_align()
            self._alignment_active = False 

        if self._measurement_active:
            self.abort_measurement()
            self.finish_manual_control_measurement()
            self._measurement_active = False  
        
        # Turn off the laser and reset related variables
        if self.settingsLaser is not None:
            print('\nTrying to disconnect laser...')
            self.settingsLaser.turnLaserOff()
            del self.settingsLaser
            self.settingsLaser = None
            # del self.motorsLaser
            # self.motorsLaser = None
            # Update GUI indicators
            self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(False)
            self.TCT_laser.set_freq_button.setEnabled(False)
            self.TCT_laser.set_laser_indicator(mode=4)
            print("\nLaser has been disconnected successfully.")
        else:
            print("\nLaser is already disconnected.")

    def DACOn(self):
        self.laserOff()
        self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(False)
        self.TCT_laser.laser_pulse_width.set_DAC_button.setEnabled(True)
        self.settingsLaser.toggleDAC(True)
        self.TCT_laser.set_DAC_indicator(mode=1)
        self.TCT_laser.laser_pulse_width.DAC_off_button.setEnabled(True)
        self.setDAC()
        self.checkLaser()

    def DACOff(self):
        self.laserOff()
        self.TCT_laser.laser_pulse_width.DAC_off_button.setEnabled(False)
        self.TCT_laser.laser_pulse_width.set_DAC_button.setEnabled(False)
        self.settingsLaser.toggleDAC(False)
        self.TCT_laser.set_DAC_indicator(mode=0)
        self.TCT_laser.laser_pulse_width.DAC_on_button.setEnabled(True)
        self.checkLaser()

    def setDAC(self):
        self.laserOff()
        # value = self.TCT_laser.laser_pulse_width.set_DAC_box.value()
        # percentage = (value/3300) * 100
        # percentage = str(percentage)
        # self.TCT_laser.laser_pulse_width.DAC_perc.setText(percentage + " %") 
        percentage = self.TCT_laser.laser_pulse_width.set_DAC_box.value()/100
        value = int(LASER_MAX_STRENGTH * percentage)
        str_value = str(value)
        self.TCT_laser.laser_pulse_width.DAC_mV.setText(str_value + " mV") 
        self.settingsLaser.setLaserDAC(value)
        self.checkLaser()

    def motor_stages_connect(self):
        try:
            print("\nTrying to connect motor stages...")
            # Connect motor positions
            self.motorsLaser = LaserPos()

            # Check laser
            if self.settingsLaser is not None:
                self.settingsLaser.turnLaserOff()
            self.TCT_laser.refresh_laser_stage_tab(swap_x_y=self.swap_x_y, move_motors=self.move_motors, set_zero=self.set_zero, move_x_left=self.move_x_left, move_x_right=self.move_x_right, move_y_left=self.move_y_left, move_y_right=self.move_y_right, 
                                                   move_z_left=self.move_z_left, move_z_right=self.move_z_right, motor_stages_connect=self.motor_stages_connect, motor_stages_disconnect=self.motor_stages_disconnect)
            self.checkLaser(raise_exceptation=True)
            # result_motor_stages = self.checkLaser(raise_exceptation=True, motor_stages=True)
            # if result_motor_stages == True:
            #     print('\nMotor stages connected successfully.')
            # else:
            #     print(f'\nMotor stages are not available. Another program might be occupying the motor stages.')
        except Exception as e:
            print(f"Unexpected error while connecting motor stages: {e}")

    def motor_stages_disconnect(self):
        try:
            print('\nDisconnecting motor stages...')
            del self.motorsLaser
            self.motorsLaser = None
            self.checkLaser()
            print("\nMotor stages disconnected successfully")
        except Exception as e:
            print(f"\nUnexpected error while disconnecting motor stages: {e}")

    def set_zero(self):
        self.checkLaser()
        self.Xpos_zero = self.positionX
        self.Ypos_zero = self.positionY
        self.Zpos_zero = self.positionZ
        self.checkLaser()

    def swap_x_y(self):
        buffer = self.Y
        self.Y = self.X
        self.X = buffer
        self.checkLaser()

    def move_motors(self):
        try:
            self.TCT_laser.laser_stage_control.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.TCT_laser.laser_stage_control.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')
            self.TCT_laser.laser_stage_control.z_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #c72e26')

            self.TCT_laser.laser_stage_control.move_stage_button.setEnabled(False)
            self.TCT_laser.laser_stage_control.swap_stage_button.setEnabled(False)

            if self.TCT_laser.laser_stage_control.speed_checkbox.isChecked() == True:
                speed = self.TCT_laser.laser_stage_control.set_same_speed.value()
                self.motorsLaser.setMotorSpeed(self.X, speed)
                self.motorsLaser.setMotorSpeed(self.Y, speed)
                self.motorsLaser.setMotorSpeed(self.Z, speed)
            else: 
                speed = self.TCT_laser.laser_stage_control.set_x_speed.value()
                self.motorsLaser.setMotorSpeed(self.X, speed)
                speed = self.TCT_laser.laser_stage_control.set_y_speed.value()
                self.motorsLaser.setMotorSpeed(self.Y, speed)
                speed = self.TCT_laser.laser_stage_control.set_z_speed.value()
                self.motorsLaser.setMotorSpeed(self.Z, speed)

            dist = self.TCT_laser.laser_stage_control.set_x_step.value()
            udist = self.TCT_laser.laser_stage_control.set_x_ustep.value()
            if self.positionX[0] != dist or self.positionX[1] != udist:
                self.motorsLaser.moveMotor(self.X, dist, udist)
                self.motorsLaser.waitMotorStop(self.X, 100)

            dist = self.TCT_laser.laser_stage_control.set_y_step.value()
            udist = self.TCT_laser.laser_stage_control.set_y_ustep.value()
            if self.positionY[0] != dist or self.positionY[1] != udist:
                self.motorsLaser.moveMotor(self.Y, dist, udist)
                self.motorsLaser.waitMotorStop(self.Y, 100)

            dist = self.TCT_laser.laser_stage_control.set_z_step.value()
            udist = self.TCT_laser.laser_stage_control.set_z_ustep.value()
            if self.positionZ[0] != dist or self.positionZ[1] != udist:
                self.motorsLaser.moveMotor(self.Z, dist, udist)
                self.motorsLaser.waitMotorStop(self.Z, 100)

            self.TCT_laser.laser_stage_control.move_stage_button.setEnabled(True)
            self.TCT_laser.laser_stage_control.swap_stage_button.setEnabled(True)

            self.TCT_laser.laser_stage_control.x_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')
            self.TCT_laser.laser_stage_control.y_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')           
            self.TCT_laser.laser_stage_control.z_axis_indicator.setStyleSheet('border: 1px solid #000000; background-color: #1bde4f')

            self.checkLaser()
        except:
            print("Motors are not available to move")

    def move_x_left(self):
        speed = self.TCT_laser.laser_stage_control.set_x_speed.value()
        self.motorsLaser.setMotorSpeed(self.X, speed)
        position = self.motorsLaser.getMotorPosition(self.X)
        self.motorsLaser.moveMotor(self.X, position[0]-self.TCT_laser.laser_stage_control.x_step_size.value(), position[1])
        # self.motorsLaser.moveMotor(self.X, position[0]-self.TCT_laser.laser_stage_control.x_step_size.value(), 0)
        self.motorsLaser.waitMotorStop(self.X, 100)
        self.checkLaser()
    def move_x_right(self):
        speed = self.TCT_laser.laser_stage_control.set_x_speed.value()
        self.motorsLaser.setMotorSpeed(self.X, speed)
        position = self.motorsLaser.getMotorPosition(self.X)
        self.motorsLaser.moveMotor(self.X, position[0]+self.TCT_laser.laser_stage_control.x_step_size.value(), position[1])
        self.motorsLaser.waitMotorStop(self.X, 100)
        self.checkLaser()
    def move_y_left(self):
        speed = self.TCT_laser.laser_stage_control.set_y_speed.value()
        self.motorsLaser.setMotorSpeed(self.Y, speed)
        position = self.motorsLaser.getMotorPosition(self.Y)
        self.motorsLaser.moveMotor(self.Y, position[0]-self.TCT_laser.laser_stage_control.y_step_size.value(), position[1])
        self.motorsLaser.waitMotorStop(self.Y, 100)
        self.checkLaser()
    def move_y_right(self):
        speed = self.TCT_laser.laser_stage_control.set_y_speed.value()
        self.motorsLaser.setMotorSpeed(self.Y, speed)
        position = self.motorsLaser.getMotorPosition(self.Y)
        self.motorsLaser.moveMotor(self.Y, position[0]+self.TCT_laser.laser_stage_control.y_step_size.value(), position[1])
        self.motorsLaser.waitMotorStop(self.Y, 100)
        self.checkLaser()
    def move_z_left(self):
        speed = self.TCT_laser.laser_stage_control.set_z_speed.value()
        self.motorsLaser.setMotorSpeed(self.Z, speed)
        position = self.motorsLaser.getMotorPosition(self.Z)
        self.motorsLaser.moveMotor(self.Z, position[0]-self.TCT_laser.laser_stage_control.z_step_size.value(), position[1])
        self.motorsLaser.waitMotorStop(self.Z, 100)
        self.checkLaser()
    def move_z_right(self):
        speed = self.TCT_laser.laser_stage_control.set_z_speed.value()
        self.motorsLaser.setMotorSpeed(self.Z, speed)
        position = self.motorsLaser.getMotorPosition(self.Z)
        self.motorsLaser.moveMotor(self.Z, position[0]+self.TCT_laser.laser_stage_control.z_step_size.value(), position[1])
        self.motorsLaser.waitMotorStop(self.Z, 100)
        self.checkLaser()
    
    def load_sequence(self):
        self.laserOff()
        self.settingsLaser.defaultFile()
        self.TCT_laser.laser_pulse_control.set_seq_info.setText("Sequence Loaded")

    def clear_sequence(self):
        self.laserOff()
        self.settingsLaser.clearLaserMCU()
        self.TCT_laser.laser_pulse_control.set_seq_info.setText("Sequence Cleared")

    def start_sequence(self):
        try:
            self.laserOff()
            self.settingsLaser.laserSeqMode(1)
            self.TCT_laser.laser_pulse_control.set_seq_info.setText("Sequence Started")
        except Exception as e:
            print(f"Failed to start sequence: {e}")
        # self.laserOff()
        # self.settingsLaser.laserSeqMode(1)
        # self.TCT_laser.laser_pulse_control.set_seq_info.setText("Sequence Started")

    def set_pulse_duration(self):
        try:
            self.laserOff()
            value = self.TCT_laser.laser_pulse_control.pulse_duration.value()
            value = (value - 440) / 180
            self.settingsLaser.sendLaserFrequency(int(value))
            self.TCT_laser.laser_pulse_control.set_seq_info.setText("Pulse Duration Set")
        except Exception as e:
            print(f"Failed to set pulse duration: {e}")
        # self.laserOff()
        # value = self.TCT_laser.laser_pulse_control.pulse_duration.value()
        # value = (value-440) / 180
        # self.settingsLaser.sendLaserFrequency(int(value))
        # self.TCT_laser.laser_pulse_control.set_seq_info.setText("Pulse Duration Set")

    def enable_ext_interrupts(self):
        try:
            self.laserOff()
            self.settingsLaser.toggleRIT(False)
            self.settingsLaser.toggleEXTInterrupt(True)
            self.TCT_laser.laser_pulse_control.set_seq_info.setText("External Interrupts Enabled")
        except Exception as e:
            print(f"Failed to enable external interrupts: {e}")
        # self.laserOff()
        # self.settingsLaser.toggleRIT(False)
        # self.settingsLaser.toggleEXTInterrupt(True)
        # self.TCT_laser.laser_pulse_control.set_seq_info.setText("External Interrupts Enabled")
        
    def enable_timer_interrupts(self):
        try:
            self.laserOff()
            self.settingsLaser.toggleEXTInterrupt(False)
            self.settingsLaser.toggleRIT(True)
            self.TCT_laser.laser_pulse_control.set_seq_info.setText("Timer Interrupts Enabled")
        except Exception as e:
            print(f"Failed to enable timer interrupts: {e}")
        # self.laserOff()
        # self.settingsLaser.toggleEXTInterrupt(False)
        # self.settingsLaser.toggleRIT(True)
        # self.TCT_laser.laser_pulse_control.set_seq_info.setText("Timer Interrupts Enabled")

    def send_seq_period(self):
        try:
            self.laserOff()
            value = self.TCT_laser.laser_pulse_control.seq_period.value()
            self.settingsLaser.laserInterruptPeriod(int(value))
            self.TCT_laser.laser_pulse_control.set_seq_info.setText("Sequence Period Sent")
        except Exception as e:
            print(f"Failed to send sequence period: {e}")
        # self.laserOff()
        # value = self.TCT_laser.laser_pulse_control.seq_period.value()
        # self.settingsLaser.laserInterruptPeriod(int(value))
        # self.TCT_laser.laser_pulse_control.set_seq_info.setText("Sequence Period Sent")

