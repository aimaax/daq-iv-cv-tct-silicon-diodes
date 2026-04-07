from pyvisa.errors import VisaIOError
from sympy import Symbol
from sympy.solvers import solve
from DAQ.AXIOM.Devices.ke2001 import ke2001


class Pt1000:
    """
    This class enables the communication between Python and the Pt1000 temperature sensor via a ke2001 multimeter.
    """

    def __init__(self, address: int = 16):
        """
        This constructor sets up the communication to the Pt1000 temperature sensor via a ke2001 multimeter.

        :param address: integer; The address of the ke2001 multimeter.
        """

        self.address = address
        
        # Connect Pt1000
        self.connect_pt1000()

    def connect_pt1000(self):
        try:
            self.multimeter = ke2001(address=self.address)
            self.multimeter.reset()
            self.multimeter.set_sense('resistance')
            # self.multimeter.set_terminal('rear')   The physical button at the Keithley has to be pressed!
            self.multimeter.set_nplc(10)
        except:
            self.multimeter = None
            print('Pt1000 is not connected!')
            
    def read_temperature(self) -> float:
        """
        This method reads out the current temperature from the Pt1000.

        :return: floating; The temperature which was determined by the Pt1000. If the Pt1000 is not
            connected, the float NaN is returned.
        """

        if not self.multimeter:
            return float('nan')

        try:
            R = float(self.multimeter.read_resistance().split(',')[0].replace('OHM', '').replace('N', ''))
        except (ValueError, VisaIOError):
            return float('nan')

        if 300 < R < 3000:
            return self.R2T_PTX_ITS90(R, 1000)
        else:
            return float('nan')

    @staticmethod
    def R2T_PTX_ITS90(R, R0):
        # PTX (X=R0) calibration with ITS-90 standard
        t = Symbol('t')
        A = 3.9083E-3
        B = -5.7750E-7
        C = 0.
        if R > R0: C = -4.183E-12
        T = solve(R - R0 * (1 + A * t + B * t * t + C * (t - 100) * t * t * t), t)
        return T[0]

    def reconnect(self):
        """ 
        Method to reconnect Pt1000 from Reconnect button on Temperature IV CV Control window.  
        """
        self.connect_pt1000()