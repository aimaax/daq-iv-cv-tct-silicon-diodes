import io
import serial
from time import sleep


class ArduinoControl:
    """
    This class can read out the temperature and humidity from sensors connected via an Arduino and
    switch measurement types by writing to the Arduino controling the switch box.
    """

    def __init__(self, port: str = 'COM7'):
        """
        This constructor initializes the connection to the Arduino to read out the
        temperature and humidity sensors and change the measurement type via the switch box.

        :param port: string; The name of the serial port to the Arduino.
        """

        self.temp_pcb_old = None

        self.port = port
        self.baudrate = 9600
        self.timeout = 0.001
        
        # Connect Arduino
        self.connect_arduino()

    def connect_arduino(self):
        """ 
        Method to connect Arduino
        """
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)  # this should only be executed once
            self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser))
            self.sio.flush()  # it is buffering. required to get the data out *now*
            if not self.ser.isOpen():
                print('Arduino is not connected!')
        except serial.SerialException as e:
            print(f"Arduino connection failed: {e}")
          
    def read_temp_and_hum(self) -> tuple:
        """
        This method reads the current temperature values of the three temperature sensors
        and the current humidity values of the two humidity sensors via the Arduino.

        :return: tuple of floats; A tuple of the three temperature and two humidity values in the order
            (temperature PDB, temperature red sensor, temperature blue sensor, humidity red sensor, humidity blue sensor).
        """

        self.sio.flush()

        arduino_readout = ''
        while arduino_readout == '' or arduino_readout[:5] != 't_pcb':
            arduino_readout = self.sio.read()

        arduino_readout = arduino_readout.splitlines()[0].split(';')
        for readout in arduino_readout:
            measurement_type, value = readout.split(':')
            if measurement_type == 't_pcb':
                temp_pcb = float(value)
            elif measurement_type == 't_air_1':
                temp_air_1 = float(value)
            elif measurement_type == 't_air_2':
                temp_air_2 = float(value)
            elif measurement_type == 'h_1':
                humidity_1 = float(value)
            elif measurement_type == 'h_2':
                humidity_2 = float(value)

        if self.temp_pcb_old and abs(temp_pcb - self.temp_pcb_old) > 20:
            temp_pcb = self.temp_pcb_old
        self.temp_pcb_old = temp_pcb

        return temp_pcb, temp_air_1, temp_air_2, humidity_1, humidity_2

    def switch_measurement_type(self, measurement_type: int):
        """
        This method writes to the Arduino to control the switch box.

        :param measurement_type: integer; The output channel of the switch box. It can be 1, 2 or 3.
        """

        if measurement_type not in [1, 2, 3]:
            raise ValueError('The measurement type must be either 1, 2 or 3!')

        command = str(measurement_type)
        self.ser.write(command.encode())
        sleep(0.4)  # Give some time for the Arduino to process the command

    def close(self):
        self.ser.close()

    def reconnect(self):
        """ 
        Method to reconnect Arduino from Reconnect button on Temperature IV CV Control window.  
        """
        self.connect_arduino()