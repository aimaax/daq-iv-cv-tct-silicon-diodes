
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from os import path
from PySide6.QtCore import QObject, Signal, QTimer
from DAQ.AXIOM.Utils.TCTAnalysis import TCTAnalysis
from DAQ.AXIOM.Devices.Laser.LaserPos.LaserPos import LaserPos
from DAQ.AXIOM.Devices.Oscillocope import Oscilloscope
from DAQ.AXIOM.Devices.ke2410 import ke2410  # power supply
from matplotlib.colors import Normalize
import time
import matplotlib

# Laser = 1000Hz, 75%DAC through labview software
# Keithley = 300V through this code
# First calibrate charge and peak max/min values

# Now relative to the starting position of the motors

 
class AutoAlignSequence(QObject):

    finished = Signal()

    def __init__(self, plot_canvas, voltage, keithley2410, osc, motors, ramping_step, ramping_interval):
        super().__init__()
        year = time.strftime("%y")
        month = time.strftime("%m")
        day = time.strftime("%d")
        self.date = year+month+day+'_'
        hour = time.strftime("%H")
        minute = time.strftime("%M")
        second = time.strftime("%S")
        self.curr_time = hour+minute+second+'_'
        self.analysis = TCTAnalysis(path='', amplitude_perc=10, filter_intensity=5, graph_size=1, curve_sensitivity=300.0, num_bins=25, usage=1)
        self.motors = motors
        self.osc = osc

        self.plot_canvas = plot_canvas
        self.keithley2410 = keithley2410
        self.keithley2410.set_output_on()
        self.keithley2410.ramp_voltage(voltage, ramping_step=ramping_step, time_interval=ramping_interval)

        self.X = 1 #Left to right
        self.Y = 0 #Front to back
        self.Z = 2 #Up and down

        self.initpos = [] #x,y,z
        self.initpos.append(self.motors.getMotorPosition(self.X))
        self.initpos.append(self.motors.getMotorPosition(self.Y))
        self.initpos.append(self.motors.getMotorPosition(self.Z))
        print(self.initpos)
        self.broad_scan_size = 1.5
        self.fine_scan_size = 3/5

        # Mode 0: Charge
        # Mode 1: Peak
        self.mode = 0

        # These values must be set after calibration
        self.sensor_size = [500, 500, 225] #x size, y size and +- radius

        # Charge are getting from finding maximum and minimum values when doing a first broad scan, now dynamic so no use
        # self.charge_min = 0 #18  #-0.9e-11
        # self.charge_max = 1.2 #7000 #7.9e-11
        # self.peak_min = 0
        # self.peak_max = 1000

    def return_start_pos(self):
        self.motors.moveMotor(self.X, self.initpos[0][0], self.initpos[0][1])
        self.motors.waitMotorStop(self.X, 500)
        self.motors.moveMotor(self.Y, self.initpos[1][0], self.initpos[1][1])
        self.motors.waitMotorStop(self.Y, 500)
        self.motors.moveMotor(self.Z, self.initpos[2][0], self.initpos[2][1])
        self.motors.waitMotorStop(self.Z, 500)
        sleep(5)
        return self.initpos

    def single_point_cal(self, posX, posY):
        """This method is used for calibration, it returns the value of the peak or charge of a specific point"""
        #self.motors.setMotorSpeed(self.X, 1000)
        #self.motors.setMotorSpeed(self.Y, 1000)
        self.motors.moveMotor(self.Y, posY, 0)
        self.motors.waitMotorStop(self.Y, 500)
        self.motors.moveMotor(self.X, posX, 0)
        self.motors.waitMotorStop(self.X, 500)
        sleep(1)
        data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=20)
        value = self.perform_analysis(data, mode=self.mode)
        return value
    
    def init_calibration(self):
        """This method is used to see whether the laser is positioned inside or outside of the sensor"""
        data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=20)
        #noise = self.perform_analysis(data, mode=2)
        init_value = self.perform_analysis(data, mode=self.mode)
        #Move to the right 750 on the x axis, to compare values
        second_value = self.single_point_cal(posX=(self.initpos[0][0]+750), posY=self.initpos[1][0])
        if init_value > (second_value*5): #init value is inside sensor, second value is outside
            self.return_start_pos()
            return 1
        elif second_value > (init_value*5): #init value is outside sensor, second value is inside
            return 1
        else:
            self.return_start_pos() 
            return 0 #both values are outside sensor (both inside sensor is not possible)

    def broad_scan(self, fine_scan = False):
        """This method performs a broad scan using x and y motors"""
        if fine_scan:
            print('Fine scan')
            interval = 30
            scan_size = [self.fine_scan_size * self.sensor_size[0], self.fine_scan_size * self.sensor_size[1]]
            plot_name = "fine_scan"
        else:
            print('Broad scan')
            interval = 100
            scan_size = [self.broad_scan_size * self.sensor_size[0], self.broad_scan_size * self.sensor_size[1]]
            plot_name = "broad_scan"

        scan_size[0] = int(scan_size[0])
        scan_size[1] = int(scan_size[1])
        print(scan_size)
        #self.return_start_pos()
        #sleep(10)
        #self.motors.setMotorSpeed(self.X, 1000)
        #self.motors.setMotorSpeed(self.Y, 1000)
        
        if fine_scan:
            startPosX = int(self.initpos[0][0] - (self.sensor_size[0]/2) * self.fine_scan_size)
            startPosY = int(self.initpos[1][0] - (self.sensor_size[1]/2) * self.fine_scan_size)
        else:
            startPosX = int(self.initpos[0][0] - (self.sensor_size[0]/2) * self.broad_scan_size)
            startPosY = int(self.initpos[1][0] - (self.sensor_size[1]/2) * self.broad_scan_size)
        #print(startPosX)
        #print(startPosY)
        x_list = range(startPosX, startPosX+scan_size[0], interval)
        y_list = range(startPosY, startPosY+scan_size[1], interval)
        # print(x_list)
        # print(y_list)

        self.init_plot(x_list=x_list, y_list=y_list)

        print("1, ", self.initpos[0][0])
        print("2, ", self.initpos[1][0])
        print("3, ",x_list)
        print("4, ",y_list)
        highest_point = [0,0,0]
        for _, y in enumerate(y_list):
            self.motors.moveMotor(self.Y, y, self.initpos[1][1])
            self.motors.waitMotorStop(self.Y, 500)
            y_index = y - min(y_list) # absolute position
            print("y, initpos[1][1], y_index", y, self.initpos[1][1], y_index)
            for _, x in enumerate(x_list):
                self.motors.moveMotor(self.X, x, self.initpos[0][1])
                self.motors.waitMotorStop(self.X, 500)
                x_index = x - min(x_list) # absolute position
                print("x, initpos[0][1], x_index", x, self.initpos[0][1], x_index)
                data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=5)
                # data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=5, peak_bolean=True)
                value = self.perform_analysis(data, mode=self.mode)
                # print("data:, ",data)
                # value = data
                print("value:, ", value)
                

                if value > highest_point[0]:
                     highest_point[0] = value
                     highest_point[1] = x
                     highest_point[2] = y
                for i in range(interval):
                    # if y+i == max(y_list)-min(y_list):
                    if y_index+i == max(y_list)-min(y_list):
                        break
                    # self.matrix[y+i][x:x+interval] = value
                    self.matrix[y_index+i][x_index:x_index+interval] = value
                # print("matrix: ", self.matrix)
                self.axim1.set_data(self.matrix)
                current_vmin, current_vmax = self.axim1.get_clim()
                if value < current_vmin or value > current_vmax:
                    # Update the normalization
                    self.axim1.set_clim(vmin=min(current_vmin, value), vmax=max(current_vmax, value))
                    self.plot_canvas.cb.update_normal(self.axim1)
                self.fig1.canvas.flush_events()
        print("highest point: ", highest_point[1], highest_point[2])

        # plt.figure(plot_name)
        self.fig1.savefig(f"./DAQ/AXIOM/GUI_temp_IV_CV/auto_align_figures/{self.date}{self.curr_time}_{plot_name}.png", bbox_inches='tight')
        # plt.savefig(f"./DAQ/AXIOM/GUI_temp_IV_CV/auto_align_figures/{self.date}{self.curr_time}_{plot_name}.png")
        np.savez_compressed(f'./DAQ/AXIOM/GUI_temp_IV_CV/auto_align_data/{self.date}{self.curr_time}_{plot_name}', 
                        x_list=x_list, y_list=y_list, matrix=self.matrix)
        
        #move to the highest point found
        self.motors.moveMotor(self.X, highest_point[1], self.initpos[0][1])
        self.motors.waitMotorStop(self.X, 500)
        self.motors.moveMotor(self.Y, highest_point[2], self.initpos[1][1])
        self.motors.waitMotorStop(self.Y, 500)

        # Update pos for new scan
        self.initpos = [list(pos) for pos in self.initpos]
        self.initpos[0][0] = highest_point[1]
        self.initpos[1][0] = highest_point[2]
        self.initpos = [tuple(pos) for pos in self.initpos]
    
    # def clear_plot_and_matrix(self):
    #     """Clears the plot and reinitializes the matrix."""
    #     if hasattr(self.plot_canvas, 'axim1') and self.plot_canvas.axim1 is not None:
    #         self.plot_canvas.axim1.remove()
    #     if hasattr(self.plot_canvas, 'cb') and self.plot_canvas.cb is not None:
    #         self.plot_canvas.cb.remove()
    #     if hasattr(self, 'fig1') and self.fig1 is not None:
    #         self.fig1.clf()
    #     self.matrix = None

    def focus_scan(self):
        """This method performs a focus scan using x and z motors"""
        pass
    
    # def three_point_scan(self):
    #     """This method performs a 3 point scan using x and y motors"""
    #     test_max_value = 0
    #     test_min_value = 0
    #     interval = 20
    #     min_value = (self.charge_max/100) * 50 # the drop off is lower than 50% of the max

    #     startPosX = int(self.initpos[0][0])
    #     startPosY = int(self.initpos[1][0])

    #     self.three_points = []

    #     right_list = range(startPosX, startPosX+self.sensor_size[0], interval)
    #     left_list = range(startPosX, startPosY-self.sensor_size[0], -interval)
    #     forward_list = range(startPosY, startPosY+self.sensor_size[1], interval)
    #     print(right_list, left_list, forward_list)

    #     #Start scan to the right
    #     for _, x in enumerate(right_list):
    #             self.motors.moveMotor(self.X, x, self.initpos[0][1])
    #             self.motors.waitMotorStop(self.X, 500)
    #             data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=10)
    #             value = self.perform_analysis(data, mode=self.mode)
    #             # data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=10, peak_bolean=True)
    #             # value = data
    #             # print(value) 
    #             if value < test_min_value:
    #                  test_min_value = value
    #             if value > test_max_value:
    #                  test_max_value = value 
    #             print(test_min_value, test_max_value)
    #             # self.three_points.append([x, self.initpos[1][0]])
    #             if value < min_value:
    #                 self.three_points.append([x, self.initpos[1][0]])
    #                 print("First point found.")
    #                 break
    #     print("FIRST SCAN FINISHED:")
    #     print(self.three_points)


    #     #Start scan to the left
    #     self.return_start_pos()
    #     for _, x in enumerate(left_list):
    #             self.motors.moveMotor(self.X, x, self.initpos[0][1])
    #             self.motors.waitMotorStop(self.X, 500)
    #             # data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=10)
    #             # value = self.perform_analysis(data, mode=self.mode)
    #             data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=10, peak_bolean=True)
    #             value = data
    #             print(value)
    #             if value < test_min_value:
    #                  test_min_value = value
    #             if value > test_max_value:
    #                  test_max_value = value 
    #             print(test_min_value, test_max_value)
    #             # self.three_points.append([x, self.initpos[1][0]])
    #             if value < min_value:
    #                 self.three_points.append([x, self.initpos[1][0]])
    #                 print("Second point found.")
    #                 break
    #     print("SECOND SCAN FINISHED:")
    #     print(self.three_points)

    #     #Start scan forward
    #     self.return_start_pos()
    #     for _, y in enumerate(forward_list):
    #             self.motors.moveMotor(self.Y, y, self.initpos[1][1])
    #             self.motors.waitMotorStop(self.Y, 500)
    #             # data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=10)
    #             # value = self.perform_analysis(data, mode=self.mode)
    #             data = self.read_osc(channel=1, points_per_wf=1250, amount_wf=10, peak_bolean=True)
    #             value = data
    #             print(value)
    #             if value < test_min_value:
    #                  test_min_value = value
    #             if value > test_max_value:
    #                  test_max_value = value 
    #             print(test_min_value, test_max_value)
    #             # self.three_points.append([self.initpos[0][0], y])
    #             if value < min_value:
    #                 self.three_points.append([self.initpos[0][0], y])
    #                 print("Third point found.")
    #                 break
    #     print("THIRD SCAN FINISHED:")
    #     print(self.three_points)
    #     self.return_start_pos()

    #     value = self.calculate_midpoint()
    #     print("value, ", value)
    #     if value[2] > (self.sensor_size[2]*0.75) or value[2] < (self.sensor_size[2]*1.75):
    #         # make sure the radius is within a 25% margin of the given sensor radius
    #         self.motors.moveMotor(self.X, value[0], self.initpos[0][1])
    #         self.motors.waitMotorStop(self.X, 500)
    #         self.motors.moveMotor(self.Y, value[1], self.initpos[1][1])
    #         self.motors.waitMotorStop(self.Y, 500)
    #     else: print("ERROR: Calculated radius does not correspond to the given radius!")

    def read_osc(self, channel, points_per_wf, amount_wf, peak_bolean = False):
        """This method pulls waveforms from the oscilloscope"""
        print("Start retrieving waveforms")
        channel = str(channel)
        points_per_wf = str(points_per_wf)
        amount_wf = str(amount_wf)
        record = self.osc.waveform_transer(channel, points_per_wf)
        self.osc.data_auto_align_settings() # starts data acquisition
        allData = a=np.zeros((1,2,int(points_per_wf))) # initializes the first of the array with a 0
        for i in range(1, int(amount_wf)):
                    print("Waveform number: "+str(i))
                    #self.osc.data_acq_settings() # starts data acquisition
                    self.osc.data_acq_start() # start data acq
                    self.osc.retrieve_data() # retrieves data from osc to pc
                    loaded_data = self.osc.retrieve_scale_factors(record) # scale factors for plotting
                    self.osc.check_errors() # checks for errors
                    bufferData = np.array([loaded_data])
                    allData = np.concatenate((allData,bufferData), axis=0)
                    self.osc.data_acq_stop()
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
        if mode == 0:
                return charge
        elif mode == 1:
                return peak_avg
        elif mode == 2:
                return pedestal
        
    def init_plot(self, x_list, y_list):
        norm = Normalize(vmin=0, vmax=0.1)

        # if self.mode == 0:
        #      vmin = self.charge_min*1.1
        #      vmax = self.charge_max*0.9
        # elif self.mode == 1:
        #      vmin = self.peak_min*1.1
        #      vmax = self.peak_max*0.9
        cmap = matplotlib.colormaps.get_cmap('jet')
        cmap.set_under(color='lightgrey')
        plt.ion()
        ax1 = self.plot_canvas.ax
        if ax1.get_legend():
                ax1.get_legend().remove()
        self.fig1 = self.plot_canvas.figure
        self.fig1.tight_layout()
        self.matrix = np.full(shape=(max(y_list)-min(y_list), max(x_list)-min(x_list)), fill_value=-1000, dtype=np.float32)
        self.axim1 = ax1.imshow(self.matrix, extent =[min(x_list), max(x_list), max(y_list), min(y_list)], 
                                # vmin=vmin, vmax=vmax, 
                                norm=norm,
                                cmap=cmap)
        ax1.set_xlim(min(x_list), max(x_list))
        ax1.set_ylim(max(y_list), min(y_list))
        self.plot_canvas.axim1 = self.axim1
        self.plot_canvas.matrix_init = self.matrix
        if self.plot_canvas.cb:
            self.plot_canvas.cb.remove()
        self.plot_canvas.cb = self.fig1.colorbar(self.axim1, location='bottom', orientation='horizontal')

    # def old_data_plot(self):
    #      content = np.load("./DAQ/AXIOM/GUI_temp_IV_CV/auto_align_data/231221_190605_broad_scan.npz")
    #      matrix = content["matrix"]
    #      x_list = content["x_list"]
    #      y_list = content["y_list"]
    #      max_val = np.nanmax(matrix)
    #      index = np.where(matrix == max_val)
    #      print(index)
    #      #self.init_plot(x_list=x_list, y_list=y_list)
    #      #self.axim1.set_data(matrix)
    #      #self.fig1.canvas.flush_events()
    #      #sleep(10)

    def finished_align(self):
        self.keithley2410.ramp_down()
        self.keithley2410.set_output_off()
        self.keithley2410.reset()
        self.keithley2410.set_source('voltage')
        self.keithley2410.set_sense('current')
        self.keithley2410.set_voltage(0)
        self.keithley2410.set_terminal('rear')
        self.keithley2410.set_output_off()
        time.sleep(1)

    def calculate_midpoint(self):
        #self.three_points = [[1470, 0], [1050, 0], [1250, 200]]
        print(self.three_points)
        x1 = self.three_points[0][0]
        y1 = self.three_points[0][1]
        x2 = self.three_points[1][0]
        y2 = self.three_points[1][1]
        x3 = self.three_points[2][0]
        y3 = self.three_points[2][1]

        s1 = x1**2 + y1**2
        s2 = x2**2 + y2**2
        s3 = x3**2 + y3**2
        M11 = x1*y2 + x2*y3 + x3*y1 - (x2*y1 + x3*y2 + x1*y3)
        M12 = s1*y2 + s2*y3 + s3*y1 - (s2*y1 + s3*y2 + s1*y3)
        M13 = s1*x2 + s2*x3 + s3*x1 - (s2*x1 + s3*x2 + s1*x3)
        x0 =  0.5*M12/M11
        y0 = -0.5*M13/M11
        r0 = ((x1 - x0)**2 + (y1 - y0)**2)**0.5
        return (x0, y0, r0)