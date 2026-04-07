from time import sleep
import numpy as np
import csv
from PySide6.QtCore import QObject, Signal
import os
import time

from config import (
    BEAM_MONITOR_DIRECTORY,
    OSCILLOSCOPEHSI, 
    OSCILLOSCOPEHSI_SUMMARY_FRAME, 
    RECORD_VOLTAGE_CURRENT_RAMPING_DATA,
    OSCILLOSCOPE_RECALL_DEFAULT
)

class MeasurementSequenceTCT(QObject):

    finished = Signal()
    error_occurred = Signal(str)
    

    def __init__(self, display_curr, display_volt, display_event, measurement_active, osc, plot_canvas, channel, beam_monitor_channel, points_per_wf, keithley2410, amount_wf, directory, date, sensorName, temp, addText,
                 voltage_start, voltage_stop, voltage_step, voltage_fine_checkbox, voltage_fine_start, voltage_fine_step, compliance, measure_delay, ramping_speed, user, comment, ramping_interval, set_CV_indicator, set_IV_indicator, set_TCT_indicator,
                 uncheck_start_after_finished_measurement_checkboxes=None):
        super().__init__()
        self.plot_canvas = plot_canvas
        self.osc = osc
        self.measurement_active = measurement_active
        self.channel = channel
        self.beam_monitor_channel = beam_monitor_channel
        self.points_per_wf = points_per_wf
        self.keithley2410 = keithley2410
        self.amount_wf = amount_wf
        self.ramping_interval = ramping_interval

        self.display_curr = display_curr
        self.display_volt = display_volt
        self.display_event = display_event

        self.set_IV_indicator = set_IV_indicator
        self.set_CV_indicator = set_CV_indicator
        self.set_TCT_indicator = set_TCT_indicator
        self.set_CV_indicator(mode=4)
        self.set_IV_indicator(mode=4)
        self.set_TCT_indicator(mode=1)

        self.measure_delay = measure_delay
        self.ramping_speed = ramping_speed
        self.lim_cur_ke2410 = compliance * 1e-5 #1e-6  # compliance in [A]

        self.directory = directory
        self.date = date
        self.sensorName = sensorName
        self.temp = temp
        self.addText = addText
        self.user = user
        self.comment = comment

        self.uncheck_start_after_finished_measurement_checkboxes = uncheck_start_after_finished_measurement_checkboxes

        self.voltage_stop = voltage_stop
        self.voltage_start = voltage_start
        self.voltage_step = voltage_step
        
        # Voltage steps for finer steps (voltage fine step always positive)
        self.voltage_fine_checkbox = voltage_fine_checkbox
        self.voltage_fine_start = voltage_fine_start
        self.voltage_fine_step = voltage_fine_step

        self.voltage_step = abs(self.voltage_step)
        self.voltage_fine_step = abs(self.voltage_fine_step)
        if self.voltage_stop < self.voltage_start:
            self.voltage_step = -self.voltage_step
            self.voltage_fine_step = -self.voltage_fine_step
        include_value = -1 if self.voltage_step < 0 else 1
        if self.voltage_fine_step != 0 and self.voltage_fine_checkbox == False:
            self.volt_list_TCT = range(self.voltage_start, self.voltage_stop+include_value, self.voltage_step)
        elif self.voltage_step != 0 and self.voltage_fine_checkbox == True and self.voltage_fine_step !=0:
            normal_voltage_list = list(range(self.voltage_start, self.voltage_fine_start+include_value, self.voltage_step))
            fine_voltage_list = list(range(self.voltage_fine_start, self.voltage_stop+include_value, self.voltage_fine_step))
            self.volt_list_TCT = np.unique(np.concatenate((normal_voltage_list, fine_voltage_list)))
        else:
            self.volt_list_TCT = [0]*10
    
    def manual_control(self):
        try:
            # Attempt to read the current from the Keithley instrument
            cur_tot = self.keithley2410.read_current()
            self.display_curr.setText("Current(A): " + f"{cur_tot}")
        except Exception as e:
            print(f"Failed to read current: {e}")
            raise
        try:
            # Recall default oscilloscope settings
            self.osc.recall_setup(OSCILLOSCOPE_RECALL_DEFAULT)
            # Attempt to transfer waveform data
            record = self.osc.waveform_transer(self.channel, self.points_per_wf)
        except Exception as e:
            print(f"Failed to transfer waveform data: {e}")
            raise
        try:
            # Begin data acquisition loop
            while self.measurement_active():
                try:
                    self.osc.data_acq_settings()  # Start data acquisition
                    self.osc.retrieve_data()  # Retrieve data from oscilloscope to PC
                    loaded_data = self.osc.retrieve_scale_factors(record)  # Scale factors for plotting
                    self.osc.check_errors()  # Check for any errors

                    # Clear and plot data on the canvas
                    self.plot_canvas.clear_graph()
                    self.plot_canvas.plot_graph(loaded_data[0][0:int(self.points_per_wf)], loaded_data[1])
                except Exception as e:
                    self.error_occurred.emit(f"\nError during data acquisition loop: {e}")
                    raise

            # Stop data acquisition
            self.osc.data_acq_stop()
            print("Measurement completed successfully.")
            self.finished.emit()
            
        except Exception as e:
            self.osc.data_acq_stop()
            return

    def execute_scan(self):
        try:
            # Initiate voltage current data recording (empty list plus start global timer)
            if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
                self.keithley2410.initiate_voltage_current_data_recording()
                
            if not OSCILLOSCOPEHSI:
                record = self.osc.waveform_transer(self.channel, self.points_per_wf)
            else:
                self.osc.set_channel(self.channel)
                self.osc.set_number_of_frames(self.amount_wf)
                self.osc.set_record_length(self.points_per_wf)
                self.osc.fastframe_configuration()
                self.osc.set_fastframe_summary(summary_frame=OSCILLOSCOPEHSI_SUMMARY_FRAME)
       
            ## starting the measurements
            self.keithley2410.set_output_on()
        except Exception as e:
            self.error_occurred.emit(f"\nError with waveform transfer in TCT measurement: {e}")
            raise
        
        try:
            beam_monitor_log = []
            for _, v in enumerate(self.volt_list_TCT):
                if self.measurement_active():
                    # Create an empty array to store data
                    all_data_per_voltage_list = []
                    
                    if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
                        self.keithley2410.ramp_voltage_with_recording(v, ramping_step=self.ramping_speed, time_interval=self.ramping_interval, sample_rate=0.01)
                        time_start = time.time()
                        while time.time() - time_start < self.measure_delay:
                            self.keithley2410.record_voltage_current_data()
                            time.sleep(0.05)
                    else:
                        self.keithley2410.ramp_voltage(v, ramping_step=self.ramping_speed, time_interval=self.ramping_interval)
                        sleep(self.measure_delay)
                        

                    cur_tot = self.keithley2410.read_current()
                    self.display_volt.setText("Voltage(V): " + f"{v}")
                    self.display_curr.setText("Current(A): " + f"{cur_tot}")
                    # print("cur tot", cur_tot)
                    # print("lim cur", self.lim_cur_ke2410)
                    
                    if cur_tot > self.lim_cur_ke2410:
                        # To avoid starting next measurement if compliance is reached, uncheck checkboxes
                        self.uncheck_start_after_finished_measurement_checkboxes()
                        print('Compliance break during TCT measurement, stopping measurement...')
                        self.stop_and_reset_TCT_measurement()
                        self.finished.emit()
                        break
                    
                    # Retrieve all frames in one call via HSI
                    if OSCILLOSCOPEHSI:
                        if self.measurement_active():
                            self.osc.run_single_seq_stop_after_one() # run single sequence and stop after one, acquire number of frames signals, data is on oscilloscope
                            # all_data_per_voltage_dict = self.osc.transfer_data_with_HSI(channels_list=[self.channel]) # data is dictionary with key as channel and value as (number_of_frames, 2, samples_per_frame)
                            all_data_per_voltage_dict = self.osc.transfer_fastframe_data(channels_list=[self.channel, self.beam_monitor_channel]) # data is dictionary with key as channel and value as (number_of_frames, 2, samples_per_frame)
                            # print(f"all_data_per_voltage_dict: {all_data_per_voltage_dict}")
                            # Plot average of all frames
                            all_data_per_voltage = all_data_per_voltage_dict[self.channel]
                            # print(f"dimension of all_data_per_voltage: {all_data_per_voltage.shape}") # should be (number_of_frames, 2, samples_per_frame)
                            time_axes = all_data_per_voltage[0, 0, :]
                            avg_waveform = all_data_per_voltage[:, 1, :].mean(axis=0)
                            self.plot_canvas.clear_graph()
                            self.plot_canvas.plot_graph(time_axes, avg_waveform)
                        else:
                            self.stop_and_reset_TCT_measurement()
                            self.finished.emit()
                            break
                        
                    else:
                        for i in range(self.amount_wf):
                            if self.measurement_active():
                                self.display_event.setText("Event: " + f"{i + 1}" + f"/{self.amount_wf}") # + 1 for human readability 
                                self.osc.data_acq_settings() # starts data acquisition
                                self.osc.retrieve_data() # retrieves data from osc to pc
                                loaded_data = self.osc.retrieve_scale_factors(record) # scale factors for plotting, list of 2 array [time, voltage], each np.array (1250,)
                                all_data_per_voltage_list.append(np.array(loaded_data)) # np.array([time, voltage]) -> dimension (2, points_per_wf), append -> len(all_data_per_voltage) = 200 after 200 waveforms
                                # self.osc.check_errors() # checks for errors
                                self.plot_canvas.clear_graph()
                                self.plot_canvas.plot_graph(loaded_data[0][0:int(self.points_per_wf)],loaded_data[1])
                                # bufferData = np.array([loaded_data])
                                # allData = np.concatenate((allData, bufferData), axis=0)

                                if i % 50 == 0:
                                    if self.beam_monitor_channel != "":
                                        beam_monitor_record = self.osc.waveform_transer(self.beam_monitor_channel, self.points_per_wf)
                                        self.osc.data_acq_settings()
                                        self.osc.retrieve_data()
                                        beam_monitor_data = self.osc.retrieve_scale_factors(beam_monitor_record)
                                        max_beam_monitor_data = np.max(beam_monitor_data[1])
                                        beam_monitor_log.append([v, max_beam_monitor_data])
                                        # print(f"Voltage: {v}, Beam Monitor: {max_beam_monitor_data}")
                                        record = self.osc.waveform_transer(self.channel, self.points_per_wf)
                            else:
                                self.stop_and_reset_TCT_measurement()
                                self.finished.emit()
                                break
                    
                    if not OSCILLOSCOPEHSI:
                        # Need to convert all_data_per_voltage from list of amount_wf times (2, points_per_wf) to np.array (amount_wf, 2, points_per_wf)
                        all_data_per_voltage = np.stack(all_data_per_voltage_list, axis=0) # (amount_wf, 2, points_per_wf)
                    
                    # extract start and end time of the measurement
                    start_time = all_data_per_voltage[0, 0, 0]
                    end_time = all_data_per_voltage[0, 0, -1]
                    time_between_points = (end_time - start_time) / int(self.points_per_wf)
                    
                    self.name = self.sensorName + "_" + str(v) + "_" + self.temp + "_" + self.date + "_" + self.addText
                    self.header = [ "Reading file: ",self.name,
                                    "Terminal voltage oscilloscope: ",50,
                                    "Number of events per file: ",self.amount_wf,
                                    "Date: ",self.date,
                                    "Points per event: ",self.points_per_wf,
                                    "Time between points: ",time_between_points,
                                    "Start time: ",start_time,
                                    "Number of channels:", 1,
                                    "Num. of U: ","-",
                                    "Voltage: ",v,
                                    "Current: ",cur_tot,
                                    "Temperature: ",self.temp,
                                    "*************************", "",
                                    "Sample: ",self.sensorName,
                                    "User: ",self.user,
                                    "Comment: ",self.comment,
                                    "*************************", ""]
                    self.osc.save_to_file(
                        name=self.name, 
                        directory=self.directory, 
                        data=all_data_per_voltage, 
                        header=self.header
                    )

                    if OSCILLOSCOPEHSI and self.beam_monitor_channel != "":
                        all_data_per_voltage_beam_monitor = all_data_per_voltage_dict[self.beam_monitor_channel]
                        start_time_beam_monitor = all_data_per_voltage_beam_monitor[0, 0, 0]
                        end_time_beam_monitor = all_data_per_voltage_beam_monitor[0, 0, -1]
                        time_between_points_beam_monitor = (end_time_beam_monitor - start_time_beam_monitor) / int(self.points_per_wf)
                        save_name_beam_monitor = self.sensorName + "_" + str(v) + "_" + self.temp + "_" + self.date + "_" + self.addText + "_BM"
                        header_beam_monitor = [ "Reading file: ",save_name_beam_monitor,
                                                "Terminal voltage oscilloscope: ",50,
                                                "Number of events per file: ",self.amount_wf,
                                                "Date: ",self.date,
                                                "Points per event: ",self.points_per_wf,
                                                "Time between points: ",time_between_points_beam_monitor,
                                                "Start time: ",start_time_beam_monitor,
                                                "Channel: ",self.beam_monitor_channel,
                                                "Num. of U: ","-",
                                                "Voltage: ",v,
                                                "Current: ",cur_tot,
                                                "Temperature: ",self.temp,
                                                "*************************", "",
                                                "Sample: ","beam monitor",
                                                "User: ",self.user,
                                                "Comment: ",self.comment,
                                                "*************************", ""]
                        self.osc.save_to_file(
                            name=save_name_beam_monitor,
                            directory=os.path.join(self.directory, "Beam_Monitor"),
                            data=all_data_per_voltage_beam_monitor,
                            header=header_beam_monitor
                        )
                    # print("allData.ndim", allData.ndim)
                    # print("allData.size", allData.size)
                    # print("allData.shape", allData.shape)

                    # allData.ndim 3
                    # allData.size 502500
                    # allData.shape (201, 2, 1250)
                    
                    # If summary frame 
                    # allData.shape (1, 2, 1250)

                    # allData = np.zeros((1,2,int(self.points_per_wf)))
                else:
                    self.stop_and_reset_TCT_measurement()
                    self.finished.emit()
                    break
                
            if not OSCILLOSCOPEHSI:
                # save beam monitor data to csv file
                beam_monitor_name = f"beam_monitor_{self.date}_{self.sensorName}_{self.addText}.csv"
                beam_monitor_path = os.path.join(BEAM_MONITOR_DIRECTORY, beam_monitor_name)
                with open(beam_monitor_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Voltage', 'Beam_Monitor_Max_Value'])
                    writer.writerows(beam_monitor_log)

                
        except Exception as e:
            self.stop_and_reset_TCT_measurement()
            self.error_occurred.emit(f"\nError during TCT measurement: {e}")
            raise

        # Stop data acquisition and reset power supplies
        self.stop_and_reset_TCT_measurement()
        print("TCT measurement finished")   

        # Signal thread that TCT measurement is finished
        self.finished.emit()
        
    def stop_and_reset_TCT_measurement(self):
        if not OSCILLOSCOPEHSI:
            self.osc.data_acq_stop()
        if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
            self.keithley2410.ramp_down_with_recording(time_interval=1, sample_rate=0.01)
        else:
            self.keithley2410.ramp_down()
        self.set_ALL_indicators(mode=2)
        
        if RECORD_VOLTAGE_CURRENT_RAMPING_DATA:
            # Save voltage current data to csv file
            self.keithley2410.save_voltage_current_data(os.path.join(self.directory, f"{self.sensorName}_TCT_ramping_recording.csv"))
        
            # Stop voltage current data recording
            self.keithley2410.reset_voltage_current_data_recording()

    def set_ALL_indicators(self, mode):
        self.set_CV_indicator(mode=mode)
        self.set_IV_indicator(mode=mode)
        self.set_TCT_indicator(mode=mode)

    def reset_power_supplies(self):
        """ Reset power supply for TCT measurement """
        self.keithley2410.ramp_down()
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
 