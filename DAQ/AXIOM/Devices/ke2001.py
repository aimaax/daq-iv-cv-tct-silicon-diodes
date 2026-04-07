from DAQ.AXIOM.Devices.KeithleyDevice import KeithleyDevice


class ke2001(KeithleyDevice):
    """ 
    Keithley 2001 multimeter.
    
    Example:
    -------------
    dev = ke2001(address=24)
    dev.print_idn()
    dev.set_sense('current')
    dev.set_current_limit(0.00005)
    dev.set_output_on()
    print dev.read_current()
    print dev.read_voltage()
    print dev.read_resistance()
    dev.set_output_off()
    dev.reset()
    """
    
    def __init__(self, address):
        super().__init__(address=address)
    
    def clear_status(self):
        self.ctrl.write("*CLS")
        return 0

    def self_test(self):
        return self.ctrl.query("*TST?")

    # Set attribute functions
    # ---------------------------------

    def set_nplc(self, value):
        self.ctrl.write(":SENSE:CURR:NPLC %d" % value)
        self.ctrl.write(":SENSE:VOLT:NPLC %d" % value)
        return 0

    def check_nplc(self):
        return self.ctrl.write(":SENSE:VOLT:NPLC?"), self.ctrl.write(":SENSE:CURR:NPLC?")

    def setup_voltmeter(self, nplc=1, dig=9, rang=0):
        self.ctrl.write(":SENS:VOLT")
        if rang == 0:
            self.ctrl.write(":SENS:VOLT:RANG AUTO")
        else:
            self.ctrl.write(":SENS:VOLT:RANG %E" % rang)
        self.ctrl.write(":SENS:VOLT:DIG %d" % dig)
        self.ctrl.write(":SENS:VOLT:NPLC %d" % nplc)

    def setup_ammeter(self, nplc=1, dig=9, rang=0):
        #self.ctrl.write(":SENS:CURR")
        #if rang == 0:
        #    self.ctrl.write(":SENS:CURR:RANG AUTO 1")
        #else:
        #    self.ctrl.write(":SENS:CURR:RANG %E" % rang)
        self.ctrl.write(":CURR:DIG %d" % dig)
        self.ctrl.write(":CURR:NPLC %d" % nplc)
        return 0

        # :RANG?
        # :RANG:AUTO? 
        # :DIG?
        # :DIG:AUTO <b>
        # :DIG:AUTO?

    # Read attribute functions
    # ---------------------------------

    def read_voltage(self):
        val = self.ctrl.query(":MEAS:VOLT?")
        return float(val)

    def read_voltage_ac(self):
        val = self.ctrl.query(":MEAS:VOLT:AC?")
        return float(val)

    def read_current(self):
        val = self.ctrl.query(":MEAS:CURR?")
        return float(val[0:11])


    def read_current_ac(self):
        val = self.ctrl.query(":MEAS:CURR:AC?")
        return float(val)

    def read_resistance(self):
        val = self.ctrl.query(":MEAS:RES?")
        #return float(val)
        return val

    def read_temperature(self):
        val = self.ctrl.query(":MEAS:TEMP?")
        return float(val)

    def read_frequency(self):
        val = self.ctrl.query(":MEAS:FREQ?")
        return float(val)
