from DAQ.AXIOM.Devices.KeithleyDevice import KeithleyDevice


class ke6487(KeithleyDevice):
    """
    Keithley 6487 pico ammeter.

    Example:
    -------------
    dev = ke6487(address=23)
    print dev.get_idn()
    dev.reset()
    dev.self_test()
    dev.set_range(2E-8)
    print dev.get_range()
    dev.set_nplc(2)
    print dev.get_nplc()
    dev.setup_ammeter()
    print dev.read_current()
    """

    def __init__(self, address):
        super().__init__(address=address)

    def clear_status(self):
        self.ctrl.write("*CLS")

    def self_test(self):
        return self.ctrl.query("*TST?")

    # Read attribute functions
    # ---------------------------------

    def read_current(self):
        val = self.ctrl.query("READ?")
        try:
            return float(val.split(',')[0][:-1])
        except ValueError:
            print(val.split(','))

    def read_resistance(self):
        val = self.ctrl.query("READ?")
        try:
            return float(val.split(',')[1][:-1])
        except ValueError:
            print(val.split(','))

    # Set attribute functions
    # ---------------------------------

    def set_range(self, value):
        return self.ctrl.write(":SENS:CURR:RANG %E" % value)

    def get_range(self):
        return self.ctrl.query(":RANG?")

    def set_auto_range(self, value):
        return self.ctrl.write(":RANG:AUTO %d" % value)

    def get_auto_range(self):
        return self.ctrl.query(":RANG:AUTO?")

    def set_digits(self, value):
        return self.ctrl.write(":DISP:DIG %.1f" % value)

    def get_digits(self):
        return self.ctrl.query(":DIG?")

    def set_nplc(self, value):
        self.ctrl.write("CURR:NPLC %d" % value)

    def get_nplc(self):
        return self.ctrl.query("CURR:NPLC?")

    def setup_ohmmeter(self, nplc=1, dig=9, rang=0):
        self.ctrl.write("FORM:ELEM READ,UNIT")
        self.ctrl.write("SOUR:VOLT:RANG 10")
        self.ctrl.write("SOUR:VOLT 10")
        self.ctrl.write("SOUR:VOLT:ILIM 2.5e-3")
        self.ctrl.write("SENS:OHMS ON")
        self.ctrl.write("SOUR:VOLT:STAT ON")
        self.ctrl.write("SYST:ZCH OFF")

    def setup_ammeter(self):
        self.ctrl.write("FUNC 'CURR'")
        self.ctrl.write("SYST:ZCH OFF")
        self.ctrl.write(":CURR:RANG:AUTO ON")
        self.ctrl.write(":CURR:RANG:AUTO:ULIM 2E-4")
        self.ctrl.write(":CURR:RANG:AUTO:LLIM 2E-7")

    def zero_correction(self):
        print('Nothing there yet.')
        # SYST:ZCH ON ' Enable zero check.'
        # CURR:RANG 2e-9 ' Select the 2nA range.'
        # INIT ' Trigger reading to be used as zero correction'

        # SYST:ZCOR:STAT OFF ' Turn zero correct off.'
        # SYST:ZCOR:ACQ ' Use last reading taken as zero correct value.'
        # SYST:ZCOR ON ' Perform zero correction.'
        # CURR:RANG:AUTO ON ' Enable auto range.'
        # SYST:ZCH OFF ' Disable zero check.'
