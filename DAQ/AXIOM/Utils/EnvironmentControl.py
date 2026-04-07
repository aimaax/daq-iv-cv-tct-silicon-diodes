from datetime import datetime
import csv
from os import path
from PySide6.QtCore import QTimer, QObject, Signal

from DAQ.AXIOM.TemperatureControl import temperature_config
from DAQ.AXIOM.TemperatureControl.ChillerCC505 import ChillerCC505
from DAQ.AXIOM.TemperatureControl.Pt1000 import Pt1000
from DAQ.AXIOM.TemperatureControl.PeltierElements import PeltierElements
from DAQ.AXIOM.TemperatureControl.ArduinoControl import ArduinoControl
from DAQ.AXIOM.TemperatureControl.AirFluxControl import AirFluxControl


from DAQ.AXIOM.LoggingCode.influxdb_logger import ParticularsMonitor


class EnvironmentControl(QObject):

    finished = Signal()
    peltier_in_operation = Signal(bool)

    def __init__(self, temp_monitoring_canvas, temp_config, set_chiller_indicator):
        super().__init__()

        self.temp_monitoring_canvas = temp_monitoring_canvas
        self.set_chiller_indicator = set_chiller_indicator
        self.timer = None
        self.log_file = None
        self.log_writer = None
        self.temp_config = temp_config

        # === Initialize connections to devices === #
        self.chiller = ChillerCC505(port='COM6')
        self.pt1000 = Pt1000(address=16)
        self.arduino = ArduinoControl(port='COM7')
        self.peltier = PeltierElements(measurement_config=self.temp_config, debug_mode=False)
        self.air_flow = AirFluxControl(port='COM8')
        self.grafana = ParticularsMonitor()

        self.set_switchbox(measurement_type=1)

    def start_temperature_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.main_loop)
        self.timer.start(2000)  # If the update frequency is changed, also the PID parameters have to be rescaled.

    def main_loop(self):
        # === Reload current measurment configuration === #
        measure_config = temperature_config.read(config_directory=path.abspath('./'))

        # === Read out current temperatures === #
        temp_chiller_intern = self.chiller.read_internal_temperature()
        setpoint_chiller = self.chiller.read_setpoint()
        temp_Pt1000 = self.pt1000.read_temperature()
        temp_pcb, temp_air_1, temp_air_2, humidity_1, humidity_2 = self.arduino.read_temp_and_hum()
        # if hasattr(self, 'chiller'):
        #     temp_chiller_intern = self.chiller.read_internal_temperature()
        #     setpoint_chiller = self.chiller.read_setpoint()
        # else:
        #     temp_chiller_intern = 0.0
        #     setpoint_chiller = 0.0

        # if hasattr(self, 'pt1000'):
        #     temp_Pt1000 = self.pt1000.read_temperature()
        # else:
        #     temp_Pt1000 = 0.0

        # if hasattr(self, 'arduino'):
        #     temp_pcb, temp_air_1, temp_air_2, humidity_1, humidity_2 = self.arduino.read_temp_and_hum()
        # else:
        #     temp_pcb, temp_air_1, temp_air_2, humidity_1, humidity_2 = 0.0, 0.0, 0.0, 0.0, 0.0

        target_temperature = measure_config['target_temperature']

         
        # === Read out air flow setpoint and current averaged measurement === #
        if hasattr(self, 'air_flow') and self.air_flow.sensor:
            air_flow_setpoint = self.air_flow.sensor.get_setpoint()
            air_flow_averaged_measured_value = float(self.air_flow.sensor.read_averaged_measured_value(20))
        else:
            air_flow_setpoint = 0.0
            air_flow_averaged_measured_value = 0.0

        # === Write values to log file === #
        if self.log_writer:
            self.log_writer.writerow([datetime.now().strftime('%H:%M:%S')] + ['{:.2f}'.format(value) for value in [target_temperature, setpoint_chiller,
                                                                              temp_chiller_intern, temp_air_1, temp_air_2, temp_pcb, temp_Pt1000, humidity_1, humidity_2]])

        # === Update the live plot === #
        self.temp_monitoring_canvas.update_graph(new_temperatures=[target_temperature, setpoint_chiller,
                                                                   temp_chiller_intern, temp_air_1, temp_air_2,
                                                                   temp_pcb, temp_Pt1000],
                                                 new_humidities=[humidity_1, humidity_2])
        
         
        # === Log to influxdb to show of Grafana === #
        self.grafana.execute(air_flow_setpoint=air_flow_setpoint, air_flow_averaged_measured_value=air_flow_averaged_measured_value, target_temperature=target_temperature, setpoint_chiller=setpoint_chiller, temp_chiller_intern=temp_chiller_intern, temp_air_1=temp_air_1, temp_air_2=temp_air_2, temp_pcb=temp_pcb, temp_Pt1000=temp_Pt1000, humidity_1=humidity_1, humidity_2=humidity_2)

        # === Check setpoint of the chiller === #
        new_setpoint = measure_config['chiller_setpoint']
        if abs(new_setpoint - setpoint_chiller) > 0.05:
            self.chiller.set_point(setpoint_temperature=new_setpoint)

        # === Check the status of the chiller === #
        status = self.chiller.check_status()
        mode = 1 if status == 1 else 2
        self.set_chiller_indicator(mode=mode)
    
        # === Reload current measurment configuration === #
        measure_config = temperature_config.read(config_directory=path.abspath('./'))

        # === Check if the temperature is safe to operate the Peltier elements and perform PID on them === #
        if temp_chiller_intern < measure_config['max_peltier_chiller_temp'] and temp_pcb < measure_config['max_peltier_PCB_temp'] and measure_config['voltage_output_on']:
            self.peltier.turn_on_off(mode='on')
            self.peltier_in_operation.emit(True)
            self.peltier.apply_PID_control(current_temp=temp_pcb, measurement_config=measure_config)
        else:
            self.peltier.turn_on_off(mode='off')
            self.peltier_in_operation.emit(False)

    # def reconnect_temp_sensors(self):
    #     self.pt1000 = Pt1000(address=16)
    #     self.arduino = ArduinoControl(port='COM7')

    def start_temperature_log(self, measurement_filename):
        # === Create log file === #
        self.log_file = open(measurement_filename, 'a', newline='', encoding='utf-8')
        self.log_writer = csv.writer(self.log_file, delimiter=';')
        self.log_writer.writerow(['time (' + datetime.now().strftime('%d.%m.%Y') + ')', 'target (PCB) temperature (C)', 'chiller setpoint (C)',
                                  'chiller temperature (internal) (C)', 'housing temperature (C)', 'sensor box temperature (C)', 'PCB temperature (C)',
                                  'Pt1000 temperature (C)', 'housing humidity (%)', 'sensor box humidity (%)'])

    def stop_temperature_log(self):
        self.log_file.close()
        self.log_writer = None
        self.log_file = None

    def set_switchbox(self, measurement_type: int):
        self.arduino.switch_measurement_type(measurement_type=measurement_type)

    def close_connections(self):
        print('\nConnections closed.')

        self.timer.stop()

        self.peltier.turn_on_off(mode='off')
        self.arduino.switch_measurement_type(measurement_type=1)
        self.arduino.close()
        self.chiller.close()
        if self.log_file:
            self.log_file.close()
        self.finished.emit()

    def reconnect_chiller(self):
        try:
            print("\nTrying to reconnect Chiller...")
            self.chiller.close()
            del self.chiller
            self.chiller = ChillerCC505(port='COM6')
            print("\nChiller reconnected successfully.")
        except Exception as e:
            print(f"\nFailed to reconnect to Chiller: {e}")

    def reconnect_peltier(self):
        try:
            print("\nTrying to reconnect Peltier...")
            self.peltier.turn_on_off(mode='off')
            del self.peltier
            self.peltier = PeltierElements(measurement_config=self.temp_config, debug_mode=False)
            print("\nPeltier reconnected successfully.")
        except Exception as e:
            print(f"\nFailed to reconnect to Peltier: {e}")

    def reconnect_pt1000(self):
        try:
            print("\nTrying to reconnect Pt1000...")
            del self.pt1000
            self.pt1000 = Pt1000(address=16)
            print("\nPt1000 reconnected successfully.")
        except Exception as e:
            print(f"\nFailed to reconnect to Pt1000: {e}")
    
    def reconnect_arduino(self):
        try:
            print("\nTrying to reconnect Arduino...")
            self.arduino.close()
            del self.arduino
            self.arduino = ArduinoControl(port='COM7')
            print("\nArduino reconnected successfully.")
        except Exception as e:
            print(f"\nFailed to reconnect to Arduino: {e}")

    def reconnect_air_flow(self):
        try:
            print("\nTrying to reconnect Air Flow...")
            self.air_flow.close()
            del self.air_flow
            self.air_flow = AirFluxControl(port='COM8')
            print("\nAir Flow reconnected successfully.")
        except Exception as e:
            print(f"\nFailed to reconnect to Air Flow: {e}")
    