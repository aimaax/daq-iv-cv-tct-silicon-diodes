from time import sleep
import numpy as np
from datetime import datetime, timedelta
import csv
import time

from PySide6.QtCore import QObject, Signal

from DAQ.AXIOM.Devices.ke2410 import ke2410  # power supply
from DAQ.AXIOM.Devices.hp4980 import hp4980  # switch
from DAQ.AXIOM.Utils.correct_cv import lcr_series_equ, lcr_parallel_equ

from config import (
    RECORD_VOLTAGE_CURRENT_RAMPING_DATA
)


class MeasurementSequenceCV(QObject):

    finished = Signal()

    def __init__(self, plot_canvas, voltage_start, voltage_stop, voltage_step, voltage_fine_stop, voltage_fine_step, voltage_fine_checkbox, compliance, measure_delay, sample_number, ramping_speed,
                 lcr_voltage, lcr_frequency, set_switchbox, measurement_active, measurement_filename, set_IV_indicator, set_CV_indicator, set_TCT_indicator,
                 open_c_status, open_c_label, leakage_current_monitor,
                 receive_ramp_to_neg600V_checkbox_status_CV, uncheck_start_after_finished_measurement_checkboxes, vbias_set_neg600,
                 timer_start_measurement_checkbox, timer_value_start_measurement, start_temperature_log
                 ):
        super().__init__()

         
        self.open_c_status = open_c_status
        self.open_c_label = open_c_label
        self.leakage_current_monitor = leakage_current_monitor

        self.measurement_filename = measurement_filename
        self.measurement_active = measurement_active
        self.set_IV_indicator = set_IV_indicator
        self.set_CV_indicator = set_CV_indicator
        self.set_TCT_indicator = set_TCT_indicator
        
        self.receive_ramp_to_neg600V_checkbox_status_CV = receive_ramp_to_neg600V_checkbox_status_CV
        self.uncheck_start_after_finished_measurement_checkboxes = uncheck_start_after_finished_measurement_checkboxes
        self.vbias_set_neg600 = vbias_set_neg600
        self.timer_start_measurement_checkbox = timer_start_measurement_checkbox
        self.timer_value_start_measurement = timer_value_start_measurement
        self.start_temperature_log = start_temperature_log
        
        self.plot_canvas = plot_canvas
        self.voltage_start = voltage_start
        self.voltage_stop = voltage_stop
        self.voltage_step = voltage_step

        self.voltage_fine_checkbox = voltage_fine_checkbox
        self.voltage_fine_stop = voltage_fine_stop
        self.voltage_fine_step = voltage_fine_step

        self.set_CV_indicator(mode=1)
        self.set_IV_indicator(mode=4)
        self.set_TCT_indicator(mode=4)

        self.log_file = None
        self.log_writer = None

        ## Set switchbox to the correct channel
        set_switchbox(measurement_type=2)
        set_switchbox(measurement_type=2)
        set_switchbox(measurement_type=2)

        ## KEITHLEY settings
        ke2410_address = 4  # in the SSD lab gpib address of the power supply that does the CV scan

        ## LCR meter settings
        lcr_meter_address = 17  # in the SSD lab this is 9
        self.lcr_freq = lcr_frequency * 1000     # Frequency in [Hz]
        self.lim_cur_ke2410 = compliance * 1e-5 #* 1e-6  # compliance in [A]
        self.perc_compliance = 0.95 # seeing as the measurement will never actually reach compliance, we set a percentage of the compliance to stop the measurement when it gets close

        # self.voltage_step = abs(self.voltage_step)
        # self.voltage_fine_step = abs(self.voltage_fine_step)
        # if self.voltage_stop < self.voltage_start:
        #     self.voltage_step = -self.voltage_step
        #     self.voltage_fine_step = -self.voltage_fine_step
        # include_value = -1 if self.voltage_step < 0 else 1
        # if self.voltage_fine_step != 0 and self.voltage_fine_checkbox == False:
        #     self.volt_list_CV = range(self.voltage_start, self.voltage_stop+include_value, self.voltage_step)
        # elif self.voltage_step != 0 and self.voltage_fine_checkbox == True and self.voltage_fine_step !=0:
        #     fine_voltage_list = list(range(self.voltage_start, self.voltage_fine_stop+include_value, self.voltage_fine_step))
        #     normal_voltage_list = list(range(self.voltage_fine_stop, self.voltage_stop+include_value, self.voltage_step))
        #     self.volt_list_CV = np.unique(np.concatenate((fine_voltage_list, normal_voltage_list)))
        #     self.volt_list_CV = self.volt_list_CV[::-1] # reverse list to go from -25 to -900
        # else:
        #     self.volt_list_CV = [0]*10



        # Voltage range works in both directions, voltage fine stop works both as "stop" and "start" depending on sweep direction

        # Ensure positive step sizes
        self.voltage_step = abs(self.voltage_step)
        self.voltage_fine_step = abs(self.voltage_fine_step)

        direction = 1 if self.voltage_stop > self.voltage_start else -1
        self.voltage_step *= direction
        self.voltage_fine_step *= direction

        include_value = direction

        if self.voltage_fine_checkbox is False or self.voltage_fine_step == 0:
            # Pure coarse sweep
            self.volt_list_CV = list(
                range(self.voltage_start,
                    self.voltage_stop + include_value,
                    self.voltage_step)
            )

        elif self.voltage_step != 0:

            if self.voltage_start > self.voltage_stop: 
                # from -25 to -900
                fine_range = range(self.voltage_start, self.voltage_fine_stop + include_value, self.voltage_fine_step)
                normal_voltage_range = range(self.voltage_fine_stop, self.voltage_stop + include_value, self.voltage_step)
                self.volt_list_CV = np.unique(np.concatenate((fine_range, normal_voltage_range)))
            else:
                # from -900 to -25
                normal_voltage_range = range(self.voltage_start, self.voltage_fine_stop + include_value, self.voltage_step)
                fine_range = range(self.voltage_fine_stop, self.voltage_stop + include_value, self.voltage_fine_step)
                self.volt_list_CV = np.unique(np.concatenate((normal_voltage_range, fine_range)))

            self.volt_list_CV = np.unique(np.concatenate((normal_voltage_range, fine_range))) # np.unique sorts the values from low to high
            if self.voltage_start > self.voltage_stop:
                self.volt_list_CV = sorted(self.volt_list_CV, reverse=True)
            else:
                self.volt_list_CV = sorted(self.volt_list_CV, reverse=False)
        else:
            self.volt_list_CV = [0] * 10
            
        # Ensure that there are no voltages above 0 
        self.volt_list_CV = [v for v in self.volt_list_CV if v <= 0]

        self.nSampling_CV = sample_number
        self.delay_vol_CV = measure_delay  # delay between setting voltage and executing measurement in [s]
        self.ramping_speed = ramping_speed

        ## initialize the devices
        self.keithley2410 = ke2410(ke2410_address)

        ## Set up lcr meter
        self.lcr_meter = hp4980(lcr_meter_address)
        self.lcr_meter.reset()
        self.lcr_meter.set_voltage(lcr_voltage)      # ac voltage amplitude in [V]
        self.lcr_meter.set_frequency(self.lcr_freq)  # ac voltage frequency in [Hz]
        self.lcr_meter.set_mode('RX')

    def reset_power_supplies(self, verbose = False):
        """ Reset power supply for CV measurement """
        if verbose:
            print("\nRamping down voltage...")
        if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
            self.keithley2410.ramp_down_with_recording(time_interval=1, sample_rate=0.01)
        else:
            self.keithley2410.ramp_down()
        if verbose:
            print("\nVoltage ramped down successfully")
        self.keithley2410.set_output_off()
        self.keithley2410.reset()
        self.keithley2410.set_source('voltage')
        self.keithley2410.set_sense('current')
        self.keithley2410.set_current_limit(self.lim_cur_ke2410)
        
        self.keithley2410.set_voltage(0)
            
        self.keithley2410.set_terminal('front')
        # MARC keithley2410.set_interlock_on()
        self.keithley2410.set_output_off()
        sleep(1)

    def execute_scan(self):
        # Initiate voltage current data recording (empty list plus start global timer)
        if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
            self.keithley2410.initiate_voltage_current_data_recording()
         
        if self.open_c_status == 0:
            if self.timer_start_measurement_checkbox:
                start_time = datetime.now() + timedelta(minutes=self.timer_value_start_measurement)
                while datetime.now() < start_time:
                    if not self.measurement_active():
                        break
                    # If measurement is active, wait 5 seconds and check again
                    sleep(5)
                    print(f"Waiting for {start_time - datetime.now()} to start measurement...")
                
            self.start_temperature_log(measurement_filename=self.measurement_filename[:-4]+'_temperature.csv') # minus .csv then add _temperature.csv
            self.start_measurement_log(measurement_filename=self.measurement_filename)
        elif self.open_c_status == 1:
            self.volt_list_CV = [0] * 5
            self.open_c_label.setText("Open Correction: Starting...")
            self.open_c_values = []
        self.plot_canvas.clear_graph()
        self.reset_power_supplies(verbose=False)

        try:
            ## starting the measurements
            self.keithley2410.set_output_on()

            ## Loop over voltages
            for iv, v in enumerate(self.volt_list_CV):
                if not self.measurement_active():
                    break

                if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
                    self.keithley2410.ramp_voltage_with_recording(v, ramping_step=self.ramping_speed, time_interval=1, sample_rate=0.01)
                    time_start = time.time()
                    while time.time() - time_start < self.delay_vol_CV:
                        self.keithley2410.record_voltage_current_data()
                        time.sleep(0.05)
                else:
                    self.keithley2410.ramp_voltage(v, ramping_step=self.ramping_speed, time_interval=1)
                    sleep(self.delay_vol_CV)

                cur_tot = self.keithley2410.read_current()
                self.leakage_current_monitor.setText(f"{cur_tot:.4e} A")
                
                if abs(cur_tot) > self.perc_compliance * self.lim_cur_ke2410:
                    self.uncheck_start_after_finished_measurement_checkboxes()
                    break

                vol = self.keithley2410.read_voltage()

                measurements = np.array([self.lcr_meter.execute_measurement() for _ in range(self.nSampling_CV)])
                means = np.mean(measurements, axis=0)
                errors = np.std(measurements, axis=0) / np.sqrt(self.nSampling_CV)

                r, x = means
                dr, dx = errors
                z = np.sqrt(r ** 2 + x ** 2)
                phi = np.arctan(x / r)
                r_s, c_s, l_s, D = lcr_series_equ(self.lcr_freq, z, phi)
                r_p, c_p, l_p, D = lcr_parallel_equ(self.lcr_freq, z, phi)

                one_over_c_s2 = 1 / c_s**2

                # === Write values to log file === #
                if self.log_writer:
                    self.log_writer.writerow([datetime.now().strftime('%H:%M:%S')] + [v, vol, c_s, one_over_c_s2, c_p, self.lcr_freq, r, dr, x, dx, cur_tot])

                # === Update the live plot === #
                self.plot_canvas.update_graph(new_voltage=vol, new_data=one_over_c_s2, voltage_range=(self.voltage_start, self.voltage_stop))
                 
                if self.open_c_status:
                    self.open_c_values.append(c_s)
                    self.open_c_label.setText("Open Correction: "+str(c_s))

        except BaseException as err:
            print(repr(err))

        self.set_CV_indicator(mode=3)
        
        ## Close connections
        # Reset power supplies of keithley2410 on address 4, to the left of big box in the lab (CV measurement)
        self.reset_power_supplies(verbose=True)
        
        if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
            # Save voltage current data to csv file
            self.keithley2410.save_voltage_current_data(self.measurement_filename[:-4]+'_ramping_recording.csv')
        
            # Stop voltage current data recording
            self.keithley2410.reset_voltage_current_data_recording()

        # Then set the voltage of keithley2410 on address 7, above the big box in the lab (TCT measurement) to -600V if checkbox is checked
        if self.receive_ramp_to_neg600V_checkbox_status_CV() == True:
            self.vbias_set_neg600()
            
        self.stop_measurement_log()

        self.set_CV_indicator(mode=2)
        self.set_IV_indicator(mode=2)
        self.set_TCT_indicator(mode=2)
        self.finished.emit()

    def start_measurement_log(self, measurement_filename):
        # === Create log file === #
        self.log_file = open(measurement_filename, 'a', newline='', encoding='utf-8')
        self.log_writer = csv.writer(self.log_file, delimiter=';')
        self.log_writer.writerow(['time (' + datetime.now().strftime('%d.%m.%Y') + ')', 'set voltage (V)', 'real voltage (V)', 'serial capacitance',
                                  '1/serial capacitance^2', 'parallel capacitance', 'LCR frequency (Hz)', 'r', 'delta r', 'x', 'delta x',  'sample current'])

    def stop_measurement_log(self):
         
        if self.open_c_status == 0: 
            self.log_file.close()
        elif self.open_c_status == 1:
            self.open_c_label.setText("Open Correction Mean: "+str(np.mean(self.open_c_values)))
        #self.log_file.close() delete from laser_dev
        self.log_file = None
        self.log_writer = None
