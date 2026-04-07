from PySide6.QtCore import QObject, Signal
import time
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
from DAQ.AXIOM.Utils.TCTAnalysis import TCTAnalysis

class TCTAreaScanSequence(QObject):

    finished = Signal()
    error_occurred = Signal(str)

    def __init__(
            self, 
            start_pos_x,
            start_pos_y,
            step_size_x,
            step_size_y,
            num_steps_x,
            num_steps_y,
            voltage, 
            ramping_interval,
            ramping_step, 
            set_top_TCT_scan_indicator, 
            motors, 
            osc, 
            keithley2410, 
            area_scan_active, 
            plot_canvas, 
        ):
        super().__init__()

        self.start_pos_x = start_pos_x
        self.start_pos_y = start_pos_y
        self.step_size_x = step_size_x
        self.step_size_y = step_size_y
        self.num_steps_x = num_steps_x
        self.num_steps_y = num_steps_y
   
        self.motors = motors
        self.osc = osc

        self.keithley2410 = keithley2410
        self.voltage = voltage
        self.ramping_step = ramping_step
        self.ramping_interval = ramping_interval
        
        self.area_scan_active = area_scan_active
        self.plot_canvas = plot_canvas
        self.set_top_TCT_scan_indicator = set_top_TCT_scan_indicator

        year = time.strftime("%y")
        month = time.strftime("%m")
        day = time.strftime("%d")
        self.date = year+month+day+'_'
        hour = time.strftime("%H")
        minute = time.strftime("%M")
        second = time.strftime("%S")
        self.curr_time = hour+minute+second+'_'

        self.analysis = TCTAnalysis(path='', 
                                 amplitude_perc=10, 
                                 filter_intensity=5, 
                                 graph_size=1, 
                                 curve_sensitivity=300.0, 
                                 num_bins=25, 
                                 usage=1)


        self.X = 1 #Left to right
        self.Y = 0 #Front to back
        self.Z = 2 #Up and down

        # Mode 0: Charge
        # Mode 1: Peak
        self.mode = 0

    def perform_area_scan(self):
        self.set_top_TCT_scan_indicator(mode=2)
        self.start_area_scan()
        self.finished_scan()
        self.set_top_TCT_scan_indicator(mode=4)

        # Send signal that the measurements are over to the thread
        self.finished.emit()

    def start_area_scan(self):
        """This method performs an area scan using x and y motors"""
        self.initpos = [] #x,y,z
        try:
            self.initpos.append(self.motors.getMotorPosition(self.X))
            self.initpos.append(self.motors.getMotorPosition(self.Y))
            self.initpos.append(self.motors.getMotorPosition(self.Z))
            print(self.initpos)
        except Exception as e:
            print(f"Error getting motor positions: {e}")

        self.motors.setMotorSpeed(self.X, 200)
        self.motors.setMotorSpeed(self.Y, 200)

        self.start_keithley()
        
        x_list = range(self.start_pos_x, self.start_pos_x+self.step_size_x*self.num_steps_x, self.step_size_x)
        y_list = range(self.start_pos_y, self.start_pos_y+self.step_size_y*self.num_steps_y, self.step_size_y)

        self.init_plot(x_list=x_list, y_list=y_list, number_steps_x=self.num_steps_x, number_steps_y=self.num_steps_y)

        try:
            for y in y_list:
                if self.area_scan_active():
                    self.motors.moveMotor(self.Y, y, self.initpos[1][1])
                    self.motors.waitMotorStop(self.Y, 500)
                    y_index = (y - self.start_pos_y) // self.step_size_y

                    for x in x_list:
                        if self.area_scan_active():
                            self.motors.moveMotor(self.X, x, self.initpos[0][1])
                            self.motors.waitMotorStop(self.X, 500)
                            x_index = (x - self.start_pos_x) // self.step_size_x

                            data = self.read_osc(channel="CH1", points_per_wf=1250, amount_wf=3) # n - 1 amount of waveforms, need 2 to make it work?
                            print("data", data)
                            print("data shape", data.shape)
                            value = self.perform_analysis(data, mode=self.mode)
                            print(f"x: {x}, y: {y}, x_index: {x_index}, y_index: {y_index}, value: {value}")

                            self.matrix[y_index][x_index] = value

                            self.axim1.set_data(self.matrix)
                            current_vmin, current_vmax = self.axim1.get_clim()
                            print("value:", value)
                            print("Current vmin", current_vmin)
                            print("Current vmax", current_vmax)
                            if value < current_vmin or value > current_vmax:
                                self.axim1.set_clim(vmin=min(current_vmin, value), vmax=max(current_vmax, value))
                                self.plot_canvas.cb.update_normal(self.axim1)
                            self.fig1.canvas.flush_events()
                        else:
                            self.return_motor_stages_orig_pos_xy()
                            self.finished_scan()
                            self.set_top_TCT_scan_indicator(mode=4)
                            self.finished.emit()
                            break
                else: 
                    self.return_motor_stages_orig_pos_xy()
                    self.finished_scan()
                    self.set_top_TCT_scan_indicator(mode=4)
                    self.finished.emit()
                    break
                
            # Finished the area scan, finish the scan
            self.return_motor_stages_orig_pos_xy()
            self.finished_scan()
            self.set_top_TCT_scan_indicator(mode=4)
            self.finished.emit()
            return
        except Exception as e:
            self.return_motor_stages_orig_pos_xy()
            self.finished_scan()
            self.set_top_TCT_scan_indicator(mode=4)
            self.error_occurred.emit(f"\nError during area scan: {e}")
            raise

        # plt.figure(plot_name)
        # self.fig1.savefig(f"./Results/Area_Scan/Plots/{self.date}{self.curr_time}_Area_Scan.png", bbox_inches='tight')
        # np.savez_compressed(f'./Results/Area_Scan/Data/{self.date}{self.curr_time}_Area_Scan', 
        #                 x_list=x_list, y_list=y_list, matrix=self.matrix)
        

    def init_plot(self, x_list, y_list, number_steps_x, number_steps_y):
        norm = Normalize(vmin=0, vmax=0.01)
        cmap = matplotlib.colormaps.get_cmap('Spectral')
        cmap = cmap.reversed()
        cmap.set_under(color='lightgrey')
        plt.ion()
        ax1 = self.plot_canvas.ax
        if ax1.get_legend():
            ax1.get_legend().remove()
        self.fig1 = self.plot_canvas.figure
        self.fig1.subplots_adjust(left=0.15, right=0.90, top=0.95, bottom=0.05)
        self.matrix = np.full(shape=(number_steps_y, number_steps_x), fill_value=-1000, dtype=np.float32)
        self.axim1 = ax1.imshow(self.matrix, extent =[min(x_list), max(x_list), max(y_list), min(y_list)], 
                                norm=norm,
                                cmap=cmap,
                                aspect='auto')
        ax1.set_xlim(min(x_list), max(x_list))
        ax1.set_ylim(max(y_list), min(y_list))
        ax1.set_box_aspect(1.0)
        self.plot_canvas.axim1 = self.axim1
        self.plot_canvas.matrix_init = self.matrix
        if self.plot_canvas.cb:
            self.plot_canvas.cb.remove()
        self.plot_canvas.cb = self.fig1.colorbar(
            self.axim1, 
            location='right', 
            orientation='vertical',
            fraction=0.035,
            pad=0.05
        )

    def start_keithley(self):
        self.keithley2410.set_output_on()
        self.keithley2410.ramp_voltage(self.voltage, 
                                       ramping_step=self.ramping_step, 
                                       time_interval=self.ramping_interval
                                    )
        
    def return_motor_stages_orig_pos_xy(self):
        # Move back to the start position
        self.motors.moveMotor(self.X, self.initpos[0][0], self.initpos[0][1])
        self.motors.waitMotorStop(self.X, 500)
        self.motors.moveMotor(self.Y, self.initpos[1][0], self.initpos[1][1])
        self.motors.waitMotorStop(self.Y, 500)

    
    def read_osc(self, channel, points_per_wf, amount_wf, peak_bolean = False):
        """This method pulls waveforms from the oscilloscope"""
        print("Start retrieving waveforms")
        channel = str(channel)
        points_per_wf = str(points_per_wf)
        amount_wf = str(amount_wf)
        record = self.osc.waveform_transer(channel, points_per_wf)
        allData = np.zeros((1,2,int(points_per_wf))) # initializes the first of the array with a 0
        for i in range(1, int(amount_wf)):
            print("Waveform number: "+str(i))
            self.osc.data_acq_settings() # starts data acquisition
            self.osc.retrieve_data() # retrieves data from osc to pc
            loaded_data = self.osc.retrieve_scale_factors(record) # scale factors for plotting
            self.osc.check_errors() # checks for errors
            bufferData = np.array([loaded_data])
            allData = np.concatenate((allData,bufferData), axis=0)
        self.osc.data_acq_stop()
        print("Done retrieveing waveforms")
        return allData


    def perform_analysis(self, data, mode):
        print("Starting analysis")
        content = {"array_to_save": data}
        self.analysis.get_data(content=content, mode=1)
        self.analysis.convert_to_current()
        peak_avg = self.analysis.discard_waveforms()
        self.analysis.average_waveform()
        pedestal = self.analysis.find_integration_paramaters()
        charge = self.analysis.integrate_waveforms()
        # if mode == 0:
        return charge
        # elif mode == 1:
        #     return peak_avg
        # elif mode == 2:
        #     return pedestal

    def finished_scan(self):
        self.keithley2410.ramp_down()
        self.keithley2410.set_output_off()
        self.keithley2410.reset()
        self.keithley2410.set_source('voltage')
        self.keithley2410.set_sense('current')
        self.keithley2410.set_voltage(0)
        self.keithley2410.set_terminal('rear')
        self.keithley2410.set_output_off()
        time.sleep(1)
    