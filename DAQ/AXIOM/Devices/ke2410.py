from DAQ.AXIOM.Devices.KeithleyDevice import KeithleyDevice
import time
import pandas as pd


class ke2410(KeithleyDevice):
    """
    Keithley 2410 source meter.

    Example:
    -------------
    dev = ke2410(address=24)
    dev.print_idn()
    dev.set_source('voltage')
    dev.set_voltage(10)
    dev.set_sense('current')
    dev.set_current_limit(0.00005)
    dev.set_output_on()
    print dev.read_current()
    print dev.read_voltage()
    print dev.read_resistance()
    dev.set_output_off()
    dev.reset()
    """

    def __init__(self, address: int = 24):
        super().__init__(address=address)

    def set_nplc(self, value: float):
        self.ctrl.write(":SENSE:CURR:NPLC %f" % value)
        #self.ctrl.write(":SENSE:VOLT:NPLC %f" % val)

    # Read attribute functions
    # ---------------------------------

    def read_voltage(self):
        # self.ctrl.write(":SENS:FUNC VOLT")
        self.ctrl.write(":FORM:ELEM:SENS VOLT")
        val = self.ctrl.query(":MEAS:VOLT?")
        return float(val)

    def read_current(self):
        # self.ctrl.write(":SENS:FUNC CURR")
        self.ctrl.write(":FORM:ELEM:SENS CURR")
        val = self.ctrl.query(":MEAS:CURR?")
        return float(val)

    def read_resistance(self):
        # self.ctrl.write(":SENS:FUNC RES")
        self.ctrl.write(":FORM:ELEM:SENS RES")
        val = self.ctrl.query(":MEAS:RES?")
        return float(val)

    # Record attribute functions
    # ---------------------------------
    
    def ramp_voltage_with_recording(self, value: int, ramping_step: int, time_interval: int = 1, sample_rate: float = 0.05):
        """
        Ramp the voltage to 'value' in steps, while recording time, measured voltage, and current.
        
        time_interval: how long to wait at each step (s)
        sample_rate: how often to record measurements (s)
        """
        
        current_voltage = round(self.read_voltage())
        ramping_step = abs(ramping_step)
        ramping_step = -ramping_step if current_voltage > value else ramping_step

        for v in range(current_voltage, value, ramping_step):
            # Apply voltage
            self.ctrl.write(":SOUR:VOLT %f" % v)
            
            # Record data during the time interval
            time_start = time.time()
            while time.time() - time_start < time_interval:
                self.record_voltage_current_data()
                time.sleep(sample_rate)

        self.ctrl.write(":SOUR:VOLT %f" % value)
        
        # Record one last point at final voltage
        self.record_voltage_current_data()
        
    def ramp_down_with_recording(self, time_interval: int = 1, sample_rate: float = 0.05):
        time_start = time.time()
        while time.time() - time_start < time_interval:
            self.record_voltage_current_data()
            time.sleep(sample_rate)

        current_voltage = round(self.read_voltage())

        for v in range(current_voltage, 0, -10 if current_voltage > 0 else 10):
            self.ctrl.write(":SOUR:VOLT %f" % v)
            time_start = time.time()
            while time.time() - time_start < time_interval:
                self.record_voltage_current_data()
                time.sleep(sample_rate)

        self.ctrl.write(":SOUR:VOLT 0")
        
        # Record one last point at final voltage
        time_start = time.time()
        while time.time() - time_start < 15: # record for 15 seconds at 0V
            self.record_voltage_current_data()
            time.sleep(sample_rate)
    
    def initiate_voltage_current_data_recording(self):
        """Start a new recording session."""
        self.voltage_current_data = []
        self.time_zero = time.time()
        
    def record_voltage_current_data(self):
        """Record one sample of time, voltage, current."""
        if self.time_zero is None:
            raise RuntimeError("Recording has not been initiated. Call initiate_voltage_current_data_recording() first.")
        
        current = self.read_current()
        voltage = self.read_voltage()
        elapsed = time.time() - self.time_zero
        self.voltage_current_data.append([elapsed, voltage, current])
        
    def save_voltage_current_data(self, filename: str):
        """Save recorded data to a CSV file."""
        df = pd.DataFrame(self.voltage_current_data, columns=['time', 'voltage', 'current'])
        df.to_csv(filename, index=False)
        
    def reset_voltage_current_data_recording(self, clear_data: bool = True):
        """Stop the recording session and reset timer."""
        self.time_zero = None
        if clear_data:
            self.voltage_current_data = []