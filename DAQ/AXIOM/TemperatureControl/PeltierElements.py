from time import time
from pyvisa.errors import VisaIOError
import numpy as np

from DAQ.AXIOM.Devices.tsx3510P import tsx3510P
from DAQ.AXIOM.TemperatureControl.LivePlot import LivePlot


class PeltierElements:
    """
    This class enables the communication and PID control with Peltier elements.
    """

    def __init__(self, measurement_config: dict, address: int = 6, min_time: float = 0.1, debug_mode: bool = False):
        """
        This constructor initializes the communication and PID control with the Peltier elements.

        :param measurement_config: dictionary; The current values of the measurement configuration file.
        :param address: integer; The GPIB address of the power supply.
        :param min_time: float; The minimum time span between two PID updating cycles.
        :param debug_mode: boolean; If True an additional plot is shown with the live temperature and PID values.
        """

        self.is_active = False
        self.debug_mode = debug_mode
        self.address = address
        
        # Connect peltier
        self.connect_peltier()

        self.tsx.set_voltage(measurement_config['fixed_voltage'])
        self.tsx.set_current(0)  # use constant voltage and regulate via current

        self.Kp = 0
        self.Ki = 0
        self.Kd = 0

        self.last_time = []
        self.last_error = []
        self.min_time = min_time

        self.Pterm = 0
        self.Iterm = 0
        self.Dterm = 0

        if self.debug_mode:
            self.live_plot = LivePlot(labels=['target temperature', 'current temperature'],
                                      line_colors=['black', 'orange'], y_axis_range=(-23, -17))

    def connect_peltier(self):
        """ 
        Method to connect peltier. 
        """
        try:
            self.tsx = tsx3510P(self.address)
        except VisaIOError:
            raise RuntimeError('The power supply for the Peltier elements is not connected!')
        
    def turn_on_off(self, mode: str):
        """
        This method can turn the Peltier elements on or off.

        :param mode: string; This parameter can be set to "on" or "off".
        """
        try: 
            if mode == 'on':
                if not self.is_active:
                    self.tsx.set_current(0)
                    self.tsx.set_output_on()
                self.is_active = True
            elif mode == 'off':
                if self.is_active:
                    self.tsx.set_current(0)
                    self.tsx.set_output_off()
                self.is_active = False
            else:
                print('The value for the parameter "mode" can only be "on" or "off"!')
        except Exception as e:
            print(f'Error while turning {"on" if mode == "on" else "off"} the Peltier elements: {e}')

    def apply_PID_control(self, current_temp: float, measurement_config: dict):
        """
        This method calculates the current PID update value and sets the determined current to
        the Peltier elements.

        :param current_temp: float; The current temperature in °C.
        :param measurement_config: dictionary; The current values of the measurement configuration file.
            If the system has a non-linear relation between the calculated current and the actually
            applied cooling power, a limit can be set for the I-term of the PID algorithm in measurement_config.json.
            This parameter is the absolute value of the limit.
        """

        if self.is_active:
            self.Kp = measurement_config['Kp']
            self.Ki = measurement_config['Ki']
            self.Kd = measurement_config['Kd']

            max_current = measurement_config['max_current']
            target_temp = measurement_config['target_temperature']
            ITerm_limit = measurement_config['I_Term_limit']

            if (current_temp - target_temp) > 3:
                self.tsx.set_current(max_current)

            else:
                target_current = self._update_PID(feedback_value=current_temp, target_value=target_temp,
                                                  ITerm_limit=ITerm_limit)

                if target_current is not None:
                    target_current = -target_current

                    if self.debug_mode:
                        print('Calculated current: {:.2f}'.format(target_current))
                        self.live_plot.update(new_temperatures=[target_temp, current_temp])

                    target_current_cap = max(min(target_current, max_current), 0.01)
                    self.tsx.set_current(target_current_cap)

    def _update_PID(self, feedback_value: float, target_value: float, ITerm_limit: float = None):
        """Calculates PID value for given reference feedback

        .. math::
            u(t) = K_p e(t) + K_i \int_{0}^{t} e(t)dt + K_d {de}/{dt}
        """
        error = target_value - feedback_value
        current_time = time()

        if len(self.last_time) == 0:
            self.last_time = [current_time]
            self.last_error = [error]
            return None

        delta_time_long = current_time - (self.last_time[0] + self.last_time[-1])/2
        delta_time_short = current_time - self.last_time[-1]

        if delta_time_short <= self.min_time:
            return None

        self.Pterm = error

        self.Iterm += error * delta_time_short
        if ITerm_limit is not None and abs(self.Iterm * self.Ki) > abs(ITerm_limit):
            self.Iterm = np.sign(self.Iterm) * abs(ITerm_limit) / self.Ki

        delta_error = error - np.mean(self.last_error)
        self.Dterm = delta_error / delta_time_long

        # Remember last time and last error for next calculation
        self.last_time.append(current_time)
        self.last_time = self.last_time[-3:]
        self.last_error.append(error)
        self.last_error = self.last_error[-3:]

        if self.debug_mode:
            print('---')
            print('P-Term: {:.2f}'.format(self.Kp * self.Pterm))
            print('I-Term: {:.2f}'.format(self.Ki * self.Iterm))
            print('D-Term: {:.2f}'.format(self.Kd * self.Dterm))

        return (self.Kp * self.Pterm) + (self.Ki * self.Iterm) + (self.Kd * self.Dterm)

    def reconnect(self):
        """ 
        Method to reconnect Peltier from Reconnect button on Temperature IV CV Control window.  
        """
        self.connect_peltier()