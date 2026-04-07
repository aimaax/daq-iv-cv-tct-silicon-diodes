import time # std module
import pyvisa as visa # http://github.com/hgrecco/pyvisa
import matplotlib.pyplot as plt # http://matplotlib.org/
import numpy as np # http://www.numpy.org/
from PySide6.QtCore import QTimer, QObject, Signal
from config import OSCILLOSCOPE_TIMEOUT


class Oscilloscope(QObject):

    finished = Signal()

    def __init__(self, visa_address):
        super().__init__()
        try:
            self.rm = visa.ResourceManager()
            self.scope = self.rm.open_resource(visa_address)
            self.scope.timeout = OSCILLOSCOPE_TIMEOUT
            self.scope.encoding = 'latin_1'
            self.scope.read_termination = '\n'
            self.scope.write_termination = None
            self.scope.write('*cls') # clears the status in the Event Status Register
        except:
            raise RuntimeError('Cant connect to oscilloscope!')

    def save_setup(self, file):
        path = "C:/"+file
        self.scope.write('SAVe:SETUp "'+path+'"')
    
    def recall_setup(self, file):
        """
        This method recalls a setup where the settings of the oscilloscope are stored.
        """
        path = "C:/"+file
        self.scope.write('RECALL:SETUP "'+path+'"') # autoset
        # t3 = time.perf_counter()
        r = self.scope.query('*opc?') # sync
        # t4 = time.perf_counter()
        # print('\nRecall time: {} s'.format(t4 - t3))

    def waveform_transer(self, channel, points_per_wf):
        """
        Use the commands in the Waveform Transfer Command Group to transfer
        waveform data points from the instrument. Waveform data points are a collection
        of values that define a waveform. One data value usually represents one data point
        in the waveform record. When working with envelope waveforms, each data
        value is either the minimum or maximum of a min/max pair.
        Before you transfer waveform data, you must specify the data format, record
        length, and waveform source
        """
        self.scope.write('HEADer 0') # turns off header, so doesnt return header command in query
        self.scope.write('DATa:SOUrce '+channel) # channel
        self.scope.write('DATa:START 1') # first sample
        self.scope.write('DATa:STOP '+points_per_wf) # final sample
        self.scope.write('DATa:ENCdg SRIBINARY') # format of outgoing waveform data
        self.record = int(self.scope.query('HORizontal:RECOrdlength?'))
        self.scope.write('WFMOutpre:BYT_Nr 1') # 1 byte per sample
        print(self.scope.query('WFMOutpre?'))
        return self.record

    def data_acq_settings(self): 
        """
        Acquisition commands set up the modes and functions that control how the
        instrument acquires signals and processes them into waveforms.
        """
        self.scope.write('acquire:state 0') # stop
        self.scope.write('acquire:stopafter SEQUENCE') # SEQUENCE for a single sequence or RUNSTop to continually acquire
        self.scope.write('acquire:state 1') # run
        # t5 = time.perf_counter()
        r = self.scope.query('*opc?') # sync
        # t6 = time.perf_counter()
        # print('acquire time: {} s'.format(t6 - t5))


    def data_acq_start(self):
        self.scope.write('acquire:state 1') # start

    def data_acq_stop(self):
        self.scope.write('acquire:state 0') # stop

    def retrieve_data(self):
        """
        This method retrieves the data from the oscilloscope by querying "curve?"
        """
        # t7 = time.perf_counter()
        self.bin_wave = self.scope.query_binary_values('curve?', datatype='b', container=np.array)
        # t8 = time.perf_counter()
        # print('transfer time: {} s'.format(t8 - t7))

    def retrieve_scale_factors(self, record):
        """
        This method retrieves the scaling factors for plotting the data
        """
        self.tscale = float(self.scope.query('wfmoutpre:xincr?'))
        self.tstart = float(self.scope.query('wfmoutpre:xzero?'))
        self.vscale = float(self.scope.query('wfmoutpre:ymult?')) # volts / level
        self.voff = float(self.scope.query('wfmoutpre:yzero?')) # reference voltage
        self.vpos = float(self.scope.query('wfmoutpre:yoff?')) # reference position (level)

        total_time = self.tscale * record
        tstop = self.tstart + total_time
        self.scaled_time = np.linspace(self.tstart, tstop, num=record, endpoint=False) # vertical (voltage)
        unscaled_wave = np.array(self.bin_wave, dtype='double') # data type conversion
        self.scaled_wave = (unscaled_wave - self.vpos) * self.vscale + self.voff

        return self.scaled_time, self.scaled_wave

    def check_errors(self):
        """
        This method checks for errors in the event status register
        """
        r = int(self.scope.query('*esr?'))
        print('event status register: 0b{:08b}'.format(r))
        r = self.scope.query('allev?').strip()
        print('all event messages: {}'.format(r))

    def close_osc(self):
        """
        This method closes the oscilloscope communication
        """
        self.scope.close()
        #self.rm.close()

    def save_to_file(self, directory, name, data, header):
        path = directory+name
        np.savez_compressed(path, array_to_save=data, header=header)        

    # def data_auto_align_settings(self):
    #     """
    #     Acquisition commands set up the modes and functions that control how the
    #     instrument acquires signals and processes them into waveforms.
    #     """
    #     self.scope.write('acquire:state 0') # stop
    #     self.scope.write('acquire:stopafter RUNSTop') # SEQUENCE for a single sequence or RUNSTop to continually acquire
    #     self.scope.write('acquire:state 1') # run
    #     t5 = time.perf_counter()
    #     r = self.scope.query('*opc?') # sync
    #     t6 = time.perf_counter()
    #     print('acquire time: {} s'.format(t6 - t5))

    # def data_area_scan_settings(self):
    #     """
    #     Acquisition commands set up the modes and functions that control how the
    #     instrument acquires signals and processes them into waveforms.
    #     """
    #     self.scope.write('acquire:state 0') # stop
    #     self.scope.write('acquire:stopafter RUNSTop') # SEQUENCE for a single sequence or RUNSTop to continually acquire
    #     self.scope.write('acquire:state 1') # run
    #     t5 = time.perf_counter()
    #     r = self.scope.query('*opc?') # sync
    #     t6 = time.perf_counter()
    #     print('acquire time: {} s'.format(t6 - t5))
