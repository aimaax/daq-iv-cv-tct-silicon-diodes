from time import sleep
import numpy as np
from datetime import datetime, timedelta
import csv
from PySide6.QtCore import QObject, Signal

from DAQ.AXIOM.Devices.ke2410 import ke2410  # power supply
from DAQ.AXIOM.Devices.ke6487 import ke6487  # picoammeter and votlage source for IV bias of -10 V


class MeasurementSequenceIV(QObject):

    finished = Signal()

    def __init__(self, plot_canvas, voltage_start, voltage_stop, voltage_step, compliance, measure_delay, sample_number, ramping_speed,
                 set_switchbox, measurement_active, measurement_filename, set_IV_indicator, set_CV_indicator, set_TCT_indicator,
                 receive_ramp_to_neg600V_checkbox_status_IV, uncheck_start_after_finished_measurement_checkboxes, vbias_set_neg600,
                 timer_start_measurement_checkbox, timer_value_start_measurement, start_temperature_log):
        super().__init__()

        self.measurement_filename = measurement_filename
        self.measurement_active = measurement_active
        self.set_IV_indicator = set_IV_indicator
        self.set_CV_indicator = set_CV_indicator
        self.set_TCT_indicator = set_TCT_indicator

        self.plot_canvas = plot_canvas
        self.voltage_start = voltage_start
        self.voltage_stop = voltage_stop
        self.voltage_step = voltage_step
        
        self.receive_ramp_to_neg600V_checkbox_status_IV = receive_ramp_to_neg600V_checkbox_status_IV
        self.uncheck_start_after_finished_measurement_checkboxes = uncheck_start_after_finished_measurement_checkboxes
        self.vbias_set_neg600 = vbias_set_neg600
        self.timer_start_measurement_checkbox = timer_start_measurement_checkbox
        self.timer_value_start_measurement = timer_value_start_measurement
        self.start_temperature_log = start_temperature_log
        
        self.set_IV_indicator(mode=1)
        self.set_CV_indicator(mode=4)
        self.set_TCT_indicator(mode=4)

        self.log_file = None
        self.log_writer = None

        ## Set switchbox to the correct channel
        set_switchbox(measurement_type=3)
        set_switchbox(measurement_type=3)
        set_switchbox(measurement_type=3)

        self.lim_cur_ke2410 = compliance * 1e-5 #* 1e-6  # compliance in [A]
        self.lim_cur_ke6487 = compliance * 1e-6  # compliance in [A] for the GCD, this should be 10 nA
        self.ramping_speed = ramping_speed
        self.perc_compliance = 0.95 # seeing as the measurement will never actually reach compliance, we set a percentage of the compliance to stop the measurement when it gets close

        self.voltage_step = abs(self.voltage_step)
        if self.voltage_stop < self.voltage_start:
            self.voltage_step = -self.voltage_step
        include_value = -1 if self.voltage_step < 0 else 1
        if self.voltage_step != 0:
            self.volt_list_IV = range(self.voltage_start, self.voltage_stop+include_value, self.voltage_step)
        else:
            self.volt_list_IV = [0]*10
        self.currents_IV = []

        self.nSampling_IV = sample_number

        self.delay_vol_IV = measure_delay  # delay between setting voltage and executing measurement in [s]

        ## KEITHLEY settings
        keithley2410_address = 4  # in the SSD lab gpib address of the power supply that does the IV scan
        self.keithley2410 = ke2410(keithley2410_address)

        ## Set up volt meter
        keithley6487_address = 22
        self.keithley6487 = ke6487(keithley6487_address)
        
    def reset_power_supplies(self, verbose = False):
        """ Reset power supply for IV measurement """
        if verbose:
            print("\nRamping down voltage...")
        self.keithley2410.ramp_down()
        if verbose:
            print("\nVoltage ramped down successfully")
        self.keithley2410.set_output_off()
        self.keithley2410.reset()
        self.keithley2410.set_source('voltage')
        self.keithley2410.set_sense('current')
        self.keithley2410.set_current_limit(self.lim_cur_ke2410)
        
        self.keithley2410.set_voltage(0)
            
        self.keithley2410.set_terminal('rear')
        # MARC keithley2410.set_interlock_on()
        self.keithley2410.set_output_off()
        sleep(1)

        # self.keithley6487.ramp_down()
        self.keithley6487.reset()
        self.keithley6487.setup_ammeter()
        self.keithley6487.set_nplc(2)
        self.keithley6487.set_range(self.lim_cur_ke6487)

    def execute_scan(self):
        if self.timer_start_measurement_checkbox:
            start_time = datetime.now() + timedelta(minutes=self.timer_value_start_measurement)
            while datetime.now() < start_time:
                if not self.measurement_active():
                    break
                # If measurement is active, wait 5 seconds and check again
                sleep(5)
                print(f"Waiting for {start_time - datetime.now()} to start measurement...")
            
        self.plot_canvas.clear_graph()
        self.start_temperature_log(measurement_filename=self.measurement_filename[:-4]+'_temperature.csv') # minus .csv then add _temperature.csv
        self.start_measurement_log(measurement_filename=self.measurement_filename)
        self.reset_power_supplies(verbose=False)

        try:
            ## starting the measurements
            self.keithley2410.set_output_on()

            ## Check settings
            # ke2410_lim_vol = self.keithley2410.check_voltage_limit()
            # ke2410_lim_cur = self.keithley2410.check_current_limit()

            ## Loop over voltages
            for iv, v in enumerate(self.volt_list_IV):
                if not self.measurement_active():
                    break

                self.keithley2410.ramp_voltage(v, ramping_step=self.ramping_speed, time_interval=1)
                sleep(self.delay_vol_IV)

                cur_tot = self.keithley2410.read_current()
                # print("cur_tot", cur_tot) # neg when measureing pad only, check abs value for compliance
                if abs(cur_tot) > self.perc_compliance * self.lim_cur_ke2410:
                    self.uncheck_start_after_finished_measurement_checkboxes()
                    break
                vol = self.keithley2410.read_voltage()

                measurements = []
                for _ in range(self.nSampling_IV):
                    act_current = self.keithley6487.read_current()
                    # print("act_tot", act_current) # neg when measureing pad only, check abs value for compliance
                    if abs(act_current) < self.perc_compliance * self.lim_cur_ke6487:
                        measurements.append(act_current)
                    else:
                        self.uncheck_start_after_finished_measurement_checkboxes()
                        break

                measurements = np.array(measurements)
                means = np.mean(measurements, axis=0)
                errors = np.std(measurements, axis=0) / np.sqrt(self.nSampling_IV)

                i = means
                di = errors
                # print("i curr", i) # neg when measureing pad only, check abs value for compliance
                if abs(i) > self.lim_cur_ke6487:
                    self.uncheck_start_after_finished_measurement_checkboxes()
                    break

                # === Write values to log file === #
                if self.log_writer:
                    self.log_writer.writerow([datetime.now().strftime('%H:%M:%S')] + [v, vol, i, di, cur_tot])

                # === Update the live plot === #
                self.plot_canvas.update_graph(new_voltage=vol, new_data=i, voltage_range=(self.voltage_start, self.voltage_stop))

        except BaseException as err:
            print(repr(err))

        self.set_IV_indicator(mode=3)
        ## Close connections
        # First reset power supplies of keithley2410 on address 4, to the left of big box in the lab (IV measurement)
        self.reset_power_supplies(verbose=True)

        # Then set the voltage of keithley2410 on address 7, above the big box in the lab (TCT measurement) to -600V if checkbox is checked
        if self.receive_ramp_to_neg600V_checkbox_status_IV() == True:
            self.vbias_set_neg600()

        self.stop_measurement_log()

        self.set_IV_indicator(mode=2)
        self.set_CV_indicator(mode=2)
        self.set_TCT_indicator(mode=2)
        self.finished.emit()

    def start_measurement_log(self, measurement_filename):
        # === Create log file === #
        self.log_file = open(measurement_filename, 'a', newline='', encoding='utf-8')
        self.log_writer = csv.writer(self.log_file, delimiter=';')
        self.log_writer.writerow(['time (' + datetime.now().strftime('%d.%m.%Y') + ')', 'set voltage (V)', 'real voltage (V)', 'current (A)',
                                  'delta current', 'input current (A)'])

    def stop_measurement_log(self):
        self.log_file.close()
        self.log_file = None
        self.log_writer = None
