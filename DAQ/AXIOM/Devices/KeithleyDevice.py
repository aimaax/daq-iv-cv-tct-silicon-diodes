import time
import pyvisa as visa


class KeithleyDevice:
    """
    Base class which contains the basic functions to control most Keithley power devices.
    """

    def __init__(self, address: int = 24):
        ## Set up control
        try:  
            rm = visa.ResourceManager()
            self.ctrl = rm.open_resource('GPIB0::%s::INSTR' % address)
        except:
            raise RuntimeError('Keithley with GPIB %s is not connected!' % address)

        self.ctrl.write("*RST")

    def print_idn(self):
        print(self.ctrl.query("*IDN?"))

    def get_idn(self):
        return self.ctrl.query("*IDN?")

    def reset(self):
        self.ctrl.write("*RST")

    # Output functions
    # ---------------------------------

    def set_output_on(self):
        self.ctrl.write("OUTP ON")

    def set_output_off(self):
        self.ctrl.write("OUTP OFF")

    def set_output_auto(self, ctrl: bool = False):
        if ctrl:
            self.ctrl.write(":SOUR:CLE:AUTO ON")
        else:
            self.ctrl.write(":SOUR:CLE:AUTO OFF")

    def check_output(self):
        return self.ctrl.query("OUTP:STAT?")

    def set_interlock_on(self):
        self.ctrl.write(":OUTP:INT:STAT ON")

    def set_interlock_off(self):
        self.ctrl.write(":OUTP:INT:STAT OFF")

    def check_output_interlock(self):
        return self.ctrl.query(":OUTP:INT:TRIP?")

    def set_terminal(self, terminal: str):
        if terminal =='front':
            self.ctrl.write(":ROUT:TERM FRON")
        elif terminal =='rear':
            self.ctrl.write(":ROUT:TERM REAR")
        else:
            raise ValueError("This terminal doesn't exist on this device.")

    def check_terminal(self):
        return self.ctrl.query(":ROUT:TERM?")


    # Set attribute functions
    # ---------------------------------

    def set_voltage(self, value: float):
        self.ctrl.write(":SOUR:VOLT %f" % value)

    def set_current(self, value: float):
        self.ctrl.write(":SOUR:CURR %f" % value)

    def ramp_voltage(self, value: int, ramping_step: int, time_interval: int = 1):
        now = round(self.read_voltage())
        ramping_step = abs(ramping_step)

        ramping_step = -ramping_step if now > value else ramping_step

        for v in range(now, value, ramping_step):
            self.ctrl.write(":SOUR:VOLT %f" % v)
            time.sleep(time_interval)
        self.ctrl.write(":SOUR:VOLT %f" % value)

    def ramp_down(self, time_interval: int = 1):
        time.sleep(time_interval)
        now = round(self.read_voltage())

        for v in range(now, 0, -10 if now > 0 else 10):
            self.ctrl.write(":SOUR:VOLT %f" % v)
            time.sleep(time_interval)

        self.ctrl.write(":SOUR:VOLT 0")

    def set_voltage_range(self, value: float):
        self.ctrl.write(":SENS:VOLT:RANG %.2f" % value)

    def set_current_range(self, value):
        self.ctrl.write(":SENS:CURR:RANG %E" % value)

    def check_compliance(self):
        return self.ctrl.query(":SENS:CURR:PROT:TRIP?")

    def set_sense(self, prop: str):
        if prop == 'voltage':
            self.ctrl.write(":SENS:FUNC 'VOLT' ")
        elif prop == 'current':
            self.ctrl.write(":SENS:FUNC 'CURR' ")
        elif prop == 'resistance':
            self.ctrl.write(":SENS:FUNC 'RES' ")
        else:
            raise ValueError('Choosen property cannot be measured by this device!')

    def set_source(self, prop: str):
        if prop == 'voltage':
            self.ctrl.write(":SOUR:FUNC VOLT")
        elif prop == 'current':
            self.ctrl.write(":SOUR:FUNC CURR")
        else:
            raise ValueError('Choosen property cannot be supplied by this device!')

    def set_voltage_limit(self, value: float):
        self.ctrl.write(':SENS:VOLT:PROT %f' % value)
        return self.ctrl.query(":SENS:VOLT:PROT:LEV?")

    def set_current_limit(self, value: float):
        self.ctrl.write(":SENS:CURR:PROT %f" % value)
        return self.ctrl.query(":SENS:CURR:PROT:LEV?")

    def check_voltage_limit(self):
        return float(self.ctrl.query(":SENS:VOLT:PROT:LEV?"))

    def check_current_limit(self):
        return float(self.ctrl.query(":SENS:CURR:PROT:LEV?"))
