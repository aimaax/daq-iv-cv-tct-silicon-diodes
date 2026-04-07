import numpy as np
from tekhsi import TekHSIConnect
from tm_data_types import AnalogWaveform
import pyvisa
import time
import os
from config import OSCILLOSCOPEHSI_IP, OSCILLOSCOPE_TIMEOUT
from PySide6.QtCore import Signal

class OscilloscopeHSI:
    
    finished = Signal()
    
    def __init__(self, visa_address: str):
        """
        Oscilloscope driver using:
        - pyvisa (SCPI) for setup/control
        - TekHSI (gRPC) for high-speed waveform transfer
        - IP address: 128.141.104.233
        """

        try:
            # SCPI connection (for control commands)
            rm = pyvisa.ResourceManager()
            self.scope = rm.open_resource(visa_address)
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
        self.scope.query('*opc?') # wait until operation is complete on oscilloscope
    
    def recall_setup(self, file):
        """
        This method recalls a setup where the settings of the oscilloscope are stored.
        """
        path = "C:/"+file
        self.scope.write('RECALL:SETUP "' + path + '"') # autoset
        self.scope.query('*opc?') # wait until operation is complete on oscilloscope
        
    def set_channel(self, channel: str):
        self.channel = channel
        
    def set_number_of_frames(self, amount_wf: int):
        self.number_of_frames = amount_wf * 50
        
    def set_record_length(self, record_length_per_frame: int):
        self.record_length_per_frame = record_length_per_frame
        
    def fastframe_configuration(self):
        self.scope.write("ACQuire:MODe SAMple")                                 # set acquisition mode to sample, before it was average with 50 frames. Average can't be used with fastframe
        self.scope.write("HORizontal:FASTframe:STATE ON")                       # enable fastframe
        self.scope.write(f"HORizontal:FASTframe:COUNt {self.number_of_frames}")   # set number total frames to be acquired. 50 frames average per waveform was before so the total number of frames is amount_wf * 50
        
    def set_fastframe_summary(self, summary_frame: bool):
        self.summary_frame = summary_frame
        
        if self.summary_frame:
            self.scope.write("HORizontal:FASTframe:SUMFrame:STATE ON")             # enable last frame to be average of all frames
        else:
            self.scope.write("HORizontal:FASTframe:SUMFrame:STATE OFF")             # disable last frame to be average of all frames
        
        
    def run_single_seq_stop_after_one(self):
        self.scope.write("ACQuire:SEQuence:NUMSEQuence 1")                      # set number of sequences to 1 = single sequence
        self.scope.write("ACQuire:STOPAfter SEQuence")                          # next acquistition to the instrument will be single single sequence
        self.scope.write("ACQuire:STATE ON")                                    # (pressing Single / Seq Stops after 1 button on osc), with fast frame acquistition this obtains self.amount_wf * 50 frame
        
        # Wait until operation is complete on oscilloscope
        while True:
            state = int(self.scope.query("ACQuire:STATE?"))  # 1 = running, 0 = stopped
            if state == 0:
                break
            time.sleep(0.1)

    def transfer_fastframe_data(self, channels_list: list[str]):
        """
        Transfer all fastframe waveforms for multiple channels using CURVe? and DATa:FRAMESTART/STOP.
        Returns a dict: {channel_name: np.array of shape (number_of_frames, 2, points_per_frame)}.
        """
        results = {}

        for channel in channels_list:
            # Configure data transfer for all fastframes from the oscilloscope's memory for a specific channel
            self.scope.write(f'DATa:SOUrce {channel}')                  # specificy which channel to transfer
            self.scope.write('DATa:ENCDG SRIBINARY')                    # fast binary format
            self.scope.write('DATa:BYT_NR 1')                           # 1 byte per sample
            # print(f"total acquired frames: {self.scope.query('ACQuire:NUMFRAMESACQ?')}")
            
            if self.summary_frame:
                # set frame to last and transfer that frame
                self.scope.write('HORizontal:FASTframe:SELECTED 10001')
                self.scope.write('DATa:FRAMESTART 10001')
                self.scope.write('DATa:FRAMESTOP 10001')
                self.number_of_frames = 1
                # print(f"waveform start {self.scope.query('DATa:FRAMESTART?')} and waveform stop {self.scope.query('DATa:FRAMESTOP?')}")
            else:
                # set frame to first and transfer that frame
                self.scope.write('DATa:FRAMESTART 1')                       # first fastframe
                self.scope.write('DATa:FRAMESTOP 10001')                      # last fastframe
            
            # Get waveform preamble to calculate scaling
            tscale = float(self.scope.query('WFMOutpre:XINCR?'))
            tstart = float(self.scope.query('WFMOutpre:XZERO?'))
            vscale = float(self.scope.query('WFMOutpre:YMULT?'))
            voff = float(self.scope.query('WFMOutpre:YZERO?'))
            vpos = float(self.scope.query('WFMOutpre:YOFF?'))

            # Query waveform
            self.scope.write('CURVe?')

            # Binary block format: Header (#<x><yy>), Data (<data>), Terminator (\n) 
            bytes_per_sample = 1
            bytes_per_header_start = 1 # = '#'
            bytes_per_number_of_digits_of_data_block = 1 # = <x>
            bytes_per_actual_length_of_data_block = 4 # = <yy> = len(str(self.record_length_per_frame)) = len(str(1250)) = 4
            bytes_per_terminator = 1 # = \n
            
            bytes_per_data_frame = (bytes_per_header_start + 
                                    bytes_per_number_of_digits_of_data_block + 
                                    bytes_per_actual_length_of_data_block + 
                                    (bytes_per_sample * int(self.record_length_per_frame)) + 
                                    bytes_per_terminator)
            
            all_raw_binary_data = self.scope.read_bytes(self.number_of_frames * bytes_per_data_frame) # self.number_of_frames * 1257 

            # Convert entire binary block to numpy array of bytes
            all_raw_bytes_data = np.frombuffer(all_raw_binary_data, dtype=np.uint8) # dtype = int8 = 8 bits = 1 byte from -128 to 127
            
            # Reshape into (number_of_frames, bytes_per_data_frame) still including header, data and separator
            all_raw_bytes_data_reshaped = all_raw_bytes_data.reshape(self.number_of_frames, bytes_per_data_frame)
            
            # Extract only data part of each frame (excluding header and separator), should now be of shape (number_of_frames, bytes_per_sample * record_length_per_frame)
            data_start = bytes_per_header_start + bytes_per_number_of_digits_of_data_block + bytes_per_actual_length_of_data_block # = 6
            data_end = data_start + (bytes_per_sample * int(self.record_length_per_frame)) # = 6 + 1250 = 1256
            all_raw_bytes_data_frames = all_raw_bytes_data_reshaped[:, data_start:data_end]
            
            all_raw_waveforms_np_array = all_raw_bytes_data_frames.astype(np.int8).astype(np.float64) # convert unsigned uint8 to int8 then to float64, for scaling without losing precision

            # print(f"all_raw_waveforms_np_array: {all_raw_waveforms_np_array}") # (10000, 1250)
            # print(f"Dimension of all_raw_waveforms_np_array: {all_raw_waveforms_np_array.shape}")

            # Convert raw data unit signal to volts
            converted_raw_unit_signal_to_volts = (all_raw_waveforms_np_array - vpos) * vscale + voff
            # print("Before averaging:", converted_raw_unit_signal_to_volts.shape) # (10000, 1250)

            # Average over groups of 50 frames
            n_group = 50
            n_frames, n_points = converted_raw_unit_signal_to_volts.shape
            converted_raw_unit_signal_to_volts = (
                converted_raw_unit_signal_to_volts
                .reshape(n_frames // n_group, n_group, n_points)
                .mean(axis=1)
            )
            # print("After averaging:", converted_raw_unit_signal_to_volts.shape)  # (200, 1250)

            # Update number of frames to match the averaged result
            updated_number_of_frames = converted_raw_unit_signal_to_volts.shape[0]

            # Create convert_unit_time_to_seconds axis for each frame
            converted_raw_unit_time_to_seconds = np.linspace(tstart, tstart + tscale * int(self.record_length_per_frame), num=int(self.record_length_per_frame), endpoint=False)

            # Merge time and waveform into (number_of_frames, 2, points_per_frame)
            stacked_time_waveform_array = np.stack([np.tile(converted_raw_unit_time_to_seconds, (updated_number_of_frames, 1)), converted_raw_unit_signal_to_volts], axis=1)
            
            # Store in results dict
            results[channel] = stacked_time_waveform_array

        return results
    
    def save_to_file(self, directory, name, data, header):
        if not os.path.exists(directory):
            os.makedirs(directory)
        np.savez_compressed(os.path.join(directory, name), array_to_save=data, header=header)


    def close_osc(self):
        self.scope.close()
    
    
    # ================================================================================================================================
    # ================================ Methods for individual acquisition frames (Manual Control Tab) ================================
    
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
        r = self.scope.query('*opc?') # sync

    def retrieve_data(self):
        """
        This method retrieves the data from the oscilloscope by querying "curve?"
        """
        self.bin_wave = self.scope.query_binary_values('curve?', datatype='b', container=np.array)
        
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
        
    def data_acq_stop(self):
        self.scope.write('acquire:state 0') # stop