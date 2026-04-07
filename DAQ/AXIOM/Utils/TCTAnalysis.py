import numpy as np # http://www.numpy.org/
from PySide6.QtCore import QObject
from scipy.stats import norm
import csv
import logging
import time
import os
from config import LOWER_INTEGRATION_LIMIT, UPPER_INTEGRATION_LIMIT

class TCTAnalysis(QObject):
    def __init__(self, path, amplitude_perc, filter_intensity, graph_size, curve_sensitivity, num_bins, usage):
        self.path = path
        self.folder_name = os.path.basename(os.path.normpath(self.path))
        if usage == 0:
            self.log_config()
        elif usage == 1:
            print("Automatic Calibration Analysis")
        logging.info("------------------------------------------- Analysis Started -------------------------------------------")
        
        self.num_bins = num_bins
        self.filter_intensity = filter_intensity
        self.graph_size = graph_size
        self.curve_sensitivity = curve_sensitivity
        self.amplitude_perc = amplitude_perc
        logging.info("Measurement folder:%s", self.folder_name)
        logging.info("Number of bins:%d", self.num_bins)
        logging.info("Graph size for integration:%f", self.graph_size)
        logging.info("Filter intensity:%f", self.filter_intensity)
        logging.info("Curve sensitivity:%f", self.curve_sensitivity)
        logging.info("Median discard percentage:%f", self.amplitude_perc)

        #dict of data for csv
        self.cce = []           # The mean of the array of charges
        self.cce2 = []          # The mu of the gaussian function
        self.mpv = []           # The mean of the peaks of all waveforms
        self.noise = []         # The RMS of the pedestal (before being filtered)
        self.error_mu = []      # The error of mu
        self.error_mean = []    # The error of the mean
        self.leak_curr = []     # The leakage current read from the keithley
        self.volt_dict = []

        # Integration limits to match with the older version
        self.lower_limit_position = LOWER_INTEGRATION_LIMIT
        self.upper_limit_position = UPPER_INTEGRATION_LIMIT
 
        #To run analysis only by class declaration
        #self.display_metadata()
        #self.convert_to_current()
        #self.discard_waveforms()
        #self.average_waveform()
        #self.find_integration_paramaters()
        #self.integrate_waveforms()
        #self.plot_histogram()

    def get_data(self, content, mode):
        self.data = content["array_to_save"]
        data_shape = self.data.shape
        self.num_wf = data_shape[0]
        self.points_per_wf = data_shape[2]
        if mode == 0:
            self.header = content["header"] 
            # self.term_volt = int(self.header[3])
            leak_curr = self.header[21]
            self.leak_curr.append(float(leak_curr))
            voltage = self.header[19]
            self.volt_dict.append(float(voltage))
        elif mode == 1:
            # self.term_volt = 50
            pass

        # print("Analysis get_data, self.data.ndim", self.data.ndim)
        # print("Analysis get_data, self.data.size", self.data.size)
        # print("Analysis get_data, self.data.shape", self.data.shape)

        # Analysis get_data, self.data.ndim 3
        # Analysis get_data, self.data.size 502500
        # Analysis get_data, self.data.shape (201, 2, 1250)

    def display_metadata(self):
        """This method displays the metadata that the compact file contains"""
        for i in range(0, len(self.header), 2):
            print(self.header[i]+" "+self.header[i+1])
            logging.info(self.header[i]+" "+self.header[i+1])
        

    def convert_to_current(self):
        """This method converts the data from voltage to current"""
        for j in range(self.num_wf):
            #self.data[j][1] =  [(i*1e3) / self.term_volt for i in self.data[j][1]]
            self.data[j][1] =  [i*1e3 for i in self.data[j][1]]

    def discard_waveforms(self):
        """This method discards the waveforms that have a peak that is too high or too low, compared to the median"""
        arrMax = []
        for i in range(self.num_wf):
            arrMaxBuff = np.max(self.data[i][1])
            arrMax.append(arrMaxBuff)


        median = np.median(arrMax) #finds the median of the peaks of the waveforms
        #The lower 2 are to determine a 10% margin to discard and waveforms with peaks higher or lower than the 10% margin
        upp_lim = ((self.amplitude_perc/100) + 1)*median
        low_lim = ((100-self.amplitude_perc)/100)*median

        amountElements = self.data.shape
        arrMax = []
        cnt = 0
        wf_deleted = 0

        #STAYS A WHILE LOOP BECAUSE AMOUNTELEMENTS[0] IS UPDATED AND NOT STATIC
        while cnt < amountElements[0]: 
                maxAmp = np.max(self.data[cnt][1])
                if maxAmp>upp_lim or maxAmp<low_lim:
                        self.data = np.delete(self.data, cnt, axis=0)
                        wf_deleted += 1
                        amountElements = self.data.shape
                else:
                    arrMax.append(maxAmp)
                    cnt+=1
        self.num_wf = amountElements[0]
        logging.info("%d waveforms discarded", wf_deleted)
        self.mpv.append(np.mean(arrMax))
        mpv = np.mean(arrMax)
        return mpv
    
    def average_waveform(self):
        """This method finds the averaged waveform"""
        self.dataMean = np.mean(self.data, axis=0) #averaged plot, with unsuitable waveforms removed --> in order to find pedestal and integration window
        scaled_time = self.dataMean[0]
        scaled_wave = self.dataMean[1]

        """
        This plots the averaged waveform and compares to all the waveforms
        fig = plt.figure()
        ax1 = fig.add_subplot()
        cnt = 0
        while cnt < self.num_wf: # plotting all waveforms, to compare to averaged
                ax1.plot(self.data[cnt][0], self.data[cnt][1], 'r-')
                cnt+=1
        ax1.plot(scaled_time, scaled_wave, 'b-')
        plt.show()
        """

    def find_integration_paramaters(self):
        """This method filters the average waveform and uses it in order to find the pedestal and integral range"""
        #Filtering the averaged waveform
        graph_size = int(self.points_per_wf * self.graph_size)
        scaled_time = self.dataMean[0]
        scaled_wave = self.dataMean[1]
        # b = [1.0 / self.filter_intensity] * self.filter_intensity
        # a = 1
        # yy = signal.lfilter(b, a, scaled_wave)
        yy = scaled_wave
        scaled_time = scaled_time[0:graph_size]
        yy = yy[0:graph_size]
        #plt.plot(self.scaled_time, self.yy, linewidth=1, linestyle="-", c="g")  # smooth by filter
        #plt.show()

        # def find_lower_limit():
        #     #Finding the lower limit of the curve of the averaged waveform
        #     lower_limit = KneeLocator(scaled_time, yy, S=self.curve_sensitivity, curve='convex', direction='decreasing', interp_method='interp1d')
        #     lower_limit = 1.9e-08
        #     logging.info("Lower Limit: " + str(lower_limit))
        #     #lower_limit.plot_knee()
        #     #print(lower_limit.knee)
        #     #plt.show()

        #     #Finding the upper limit of the curve of the averaged waveform
        #     upper_limit = KneeLocator(scaled_time, yy, S=self.curve_sensitivity, curve='convex', direction='increasing', interp_method='interp1d')
        #     upper_limit = 2.8e-08
        #     logging.info("Upper Limit: " + str(upper_limit))
        #     #upper_limit.plot_knee()
        #     #print(upper_limit.knee)
        #     #plt.show()

        #     #Finding the array position of the lower limit
        #     for i in range(self.dataMean[0].size):
        #         if lower_limit is None:
        #             self.lower_limit_position = 10
        #             break
        #         elif self.dataMean[0][i]>=lower_limit:
        #             self.lower_limit_position = i
        #             break

        #     #Finding the array position of the upper limit
        #     for i in range(self.dataMean[0].size):
        #         if upper_limit is None:
        #             self.upper_limit_position = 20
        #             break
        #         elif self.dataMean[0][i]>=upper_limit:
        #             self.upper_limit_position = i
        #             break
        
        #Finding the pedastal of the filtered average waveform
        pedAvg = [0,0]
        pedAvg[0] = scaled_time[0:self.lower_limit_position-60]
        pedAvg[1] = yy[0:self.lower_limit_position-60]
        self.pedestal = np.mean(pedAvg[1])
        noise = np.std(pedAvg[1])
        logging.info("Pedestal: " + str(self.pedestal))
        #plt.plot(pedAvg[0], pedAvg[1], linewidth=2, linestyle="-", c="g")
        #plt.show()

        #Finding the pedastal of the unfiltered average waveform
        # pedNoise = self.dataMean[1][0:self.lower_limit_position-40]
        # noise = np.sqrt(np.mean(pedNoise**2))
        self.noise.append(noise)

        #Making the pedestal an array of the same number (making a straight line)
        self.pedestal_array = np.full(shape=len(scaled_time), fill_value=self.pedestal,dtype=np.float64)

        return noise

    def integrate_waveforms(self):
        """
        This method integrates each waveform and finds the area under the curve. It uses the parameters found from the averaged waveform. (Pedestal and Integration range).
        It then stores the area of each waveform in an array.
        """
        #total_curve_area = np.trapz(x=self.scaled_time[self.lower_limit_position:self.upper_limit_position], y=self.yy[self.lower_limit_position:self.upper_limit_position])
        #pedestal_area = np.trapz(x=self.scaled_time[self.lower_limit_position:self.upper_limit_position], y=self.pedestal_array[self.lower_limit_position:self.upper_limit_position])
        #curve_area = total_curve_area - pedestal_area
        #print(total_curve_area)
        #print(pedestal_area)
        #print(curve_area)

        #plt.fill_between(color="blue", x=self.scaled_time, y1=self.yy, y2=self.pedestal_array, interpolate=True)
        #plt.fill_between(color="red", x=self.scaled_time[self.lower_limit_position:self.upper_limit_position], y1=self.yy[self.lower_limit_position:self.upper_limit_position], y2=self.pedestal, where=self.yy[self.lower_limit_position:self.upper_limit_position]>=self.pedestal, interpolate=True)
        #plt.show()

        graph_size = int(self.points_per_wf * self.graph_size)
        self.q_arr = []
        for i in range(self.num_wf):
            x = self.data[i][0][0:graph_size]
            y = self.data[i][1][0:graph_size]
            
            #plt.plot(x, y, linewidth=1, linestyle="-", c="g")  # smooth by filter
            #plt.fill_between(color="blue", x=x, y1=y, y2=self.pedestal_array, interpolate=True)
            #plt.fill_between(color="red", x=x[self.lower_limit_position:self.upper_limit_position], y1=y[self.lower_limit_position:self.upper_limit_position], y2=self.pedestal, where=y[self.lower_limit_position:self.upper_limit_position]>=self.pedestal, interpolate=True)
            #plt.show()

            total_curve_area = np.trapz(x=x[self.lower_limit_position:self.upper_limit_position], y=y[self.lower_limit_position:self.upper_limit_position])
            pedestal_area = np.trapz(x=x[self.lower_limit_position:self.upper_limit_position], y=self.pedestal_array[self.lower_limit_position:self.upper_limit_position])
            # total_curve_area = sum(y[self.lower_limit_position:self.upper_limit_position])*0.08/1e9
            # pedestal_area = sum(self.pedestal_array[self.lower_limit_position:self.upper_limit_position])*0.08/1e9
            # print('Pedestal area: ', pedestal_area)
            curve_area = (total_curve_area - pedestal_area)*1e9
            # curve_area = (total_curve_area)*1e9
            self.q_arr.append(curve_area)

        self.q_arr = np.array(self.q_arr)
        self.entry_amount = len(self.q_arr)
        mean = np.mean(self.q_arr)
        self.cce.append(mean)
        rms = np.std(self.q_arr)
        #print("RMS:", rms)
        self.error_mean.append(rms/(np.sqrt(self.entry_amount)))
        return mean


    def plot_histogram(self):
        """This method plots the histogram based on the charge of each waveform."""
        # best fit of data
        (mu, sigma) = norm.fit(self.q_arr)
        #print("sigma:", sigma)
        # the histogram of the data
        #n, bins, patches = plt.hist(self.q_arr, bins=self.num_bins, facecolor='blue', alpha=0.5, density=True)
        # add a 'best fit' line
        #y = norm.pdf(bins, mu, sigma)
        #l = plt.plot(bins, y, 'r--', linewidth=2)
        #plt.xlabel('Collected Charge')
        #plt.ylabel('Density')
        #plt.title('Histogram of Charge Collection:\n '
        #     fr'$\mu={mu}$, $\sigma={sigma}$')
        #plt.show()
        error_mu = (sigma/(np.sqrt(self.entry_amount)))
        self.error_mu.append(error_mu)
        self.cce2.append(mu)

    def store_in_csv(self):
        """This method stores all the data in a csv file"""
        orig_volt_dict = np.array(self.volt_dict)
        volt_dict = np.sort(self.volt_dict)

        with open(self.path+'/'+self.folder_name+'.csv', 'w', newline='') as csvfile:
            fieldnames = ['Num', 'Voltage', 'Ileak[nA]', 'CCE[a.u.]', 'CCE2[a.u.]', 'MPV[mV]', 'Noise[mV]', 'Error mu', 'Error mean']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for i in range(len(volt_dict)):
                index = np.where(orig_volt_dict == volt_dict[i])[0][0]
                writer.writerow({'Num': i, 
                                 'Voltage': volt_dict[i], 
                                 'Ileak[nA]': self.leak_curr[index], 
                                 'CCE[a.u.]': self.cce[index], 
                                 'CCE2[a.u.]': self.cce2[index], 
                                 'MPV[mV]': self.mpv[index], 
                                 'Noise[mV]': self.noise[index], 
                                 'Error mu': self.error_mu[index], 
                                 'Error mean': self.error_mean[index]})
                
    def log_config(self):
        year = time.strftime("%y")
        month = time.strftime("%m")
        day = time.strftime("%d")
        date = year+month+day+'_'
        if not os.path.exists(self.path+'/Logs'):
            os.makedirs(self.path+'/Logs')
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%H:%M:%S', filename=self.path+'/Logs/'+'Log_'+date+self.folder_name+'.log', encoding='utf-8', level=logging.INFO)
        #logging.debug('This message should go to the log file')
        #logging.info('So should this')
        #logging.warning('And this, too')
        #logging.error('And non-ASCII stuff, too, like Øresund and Malmö')