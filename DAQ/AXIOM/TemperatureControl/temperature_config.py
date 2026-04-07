import os
import json


def initialize(config_directory: str) -> dict:
    """
    This function reads or creates the JSON-file containing the measurement configuration.

    :param config_directory: string; The path to the measurement directory.
    :return: A dictionary containing all values from the measurement configuration file.
    """

    if os.path.isfile(config_directory + '/measurement_config.json'):
        temperature_config = read(config_directory)

    else:
        temperature_config = {'Kp': 1,
                              'Ki': 0.01,
                              'Kd': 50,
                              'I_Term_limit': 5,
                              'target_temperature': -18.1,
                              'fixed_voltage': 12,
                              'max_current': 5,
                              'voltage_output_on': False,
                              'max_peltier_chiller_temp': -10,
                              'max_peltier_PCB_temp': 15,
                              'chiller_setpoint': -30.0,
                              'measurement_type': 1}    # 1: TCT; 2: CV; 3: IV

        with open(config_directory + '/measurement_config.json', 'w') as config_file:
            json.dump(obj=temperature_config, fp=config_file, indent=4)

    return temperature_config


def write(config_directory: str, Kp: float = 1, Ki: float = 0.01, Kd: float = 50,
          I_Term_limit: float = 5, target_temperature: float = -20, fixed_voltage: float = 12,
          max_current: float = 5, voltage_output_on: bool = False, max_peltier_chiller_temp: float = -10,
          max_peltier_PCB_temp: float = 15, chiller_setpoint: float = -30, measurement_type: int = 1) -> dict:

    temperature_config = {'Kp': Kp,
                          'Ki': Ki,
                          'Kd': Kd,
                          'I_Term_limit': I_Term_limit,
                          'target_temperature': target_temperature,
                          'fixed_voltage': fixed_voltage,
                          'max_current': max_current,
                          'voltage_output_on': voltage_output_on,
                          'max_peltier_chiller_temp': max_peltier_chiller_temp,
                          'max_peltier_PCB_temp': max_peltier_PCB_temp,
                          'chiller_setpoint': chiller_setpoint,
                          'measurement_type': measurement_type}    # 1: TCT; 2: CV; 3: IV

    with open(config_directory + '/measurement_config.json', 'w') as config_file:
        json.dump(obj=temperature_config, fp=config_file, indent=4)

    return temperature_config


def read(config_directory: str) -> dict:
    """
    This function reads the current values from the configuration file and returns them as a dictionary.

    :param config_directory: string; The path to the measurement directory.
    :return: A dictionary containing all values from the measurement configuration file.
    """

    with open(config_directory+'/measurement_config.json', 'r') as config_file:
        temperature_config = json.load(config_file)

    return temperature_config
