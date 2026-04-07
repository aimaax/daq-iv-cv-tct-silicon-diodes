#!/usr/bin/python

import time, os, sys
from optparse import OptionParser
import math

#interface to influxDB
from influxdb import InfluxDBClient
from datetime import datetime, timezone

import certifi
import urllib3

 
class ParticularsMonitor(object):
    """ Log humidty and temperature. """

    def __init__(self):
        urllib3.disable_warnings()
        http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())
        self.wait = 5                          # time between measurements
                                                # keep in mind that the pc measurement takes 60s
        self.client = InfluxDBClient(host='hidden', port=8081, username='hidden', password='hidden', database='hidden', ssl=True)

    def drop_measurement(self):
        """ Useful method if you have to change type of variables. """

        # Drop the entire measurement
        drop_query = 'DROP MEASUREMENT "setup_environment"'
        self.client.query(drop_query)
        print("Dropped the 'setup_environment' measurement from the database.")

    def execute(self, air_flow_averaged_measured_value : float, air_flow_setpoint, target_temperature, setpoint_chiller, temp_chiller_intern, temp_air_1, temp_air_2, temp_pcb, temp_Pt1000, humidity_1, humidity_2):
        fContinous = 1
        fSingle = 1
        fPrint = 0

        # Use only if you want to change type of a variable. 
        #This is where you would need to change: Uncomment once, start program. Close program, comment out again.
        #self.drop_measurement()


        try:
            while fContinous:

                ## Read measurements
                date = time.strftime("%Y-%m-%d", time.localtime())
                clock = time.strftime("%H:%M:%S", time.localtime())
                

                line = [date, clock, target_temperature, setpoint_chiller, temp_chiller_intern, temp_air_1, temp_air_2, 
                        temp_pcb, temp_Pt1000, humidity_1, humidity_2, air_flow_setpoint, air_flow_averaged_measured_value]
                
                # Handle NaN values by replacing them with 0.0 or another appropriate default
                if math.isnan(float(temp_Pt1000)):
                    temp_Pt1000 = 0.0 # default value for Pt1000, need when Pt1000 is not connected
                # print("setpoint_chiller log: ", setpoint_chiller)
                # print("temp_chiller_intern: ", temp_chiller_intern)
                # if math.isnan(float(setpoint_chiller)):
                #     setpoint_chiller = 0.0
                # if math.isnan(float(temp_chiller_intern)):
                #     temp_chiller_intern = 0.0

                #prepare database entry
                data = {
                    "measurement": "setup_environment",
                    "tags": {
                        "phase": "deployment"
                    },
                    "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),            #date needs to be in utc time!,
                    "fields": {
                        "target_temperature": target_temperature,
                        "setpoint_chiller": setpoint_chiller,
                        "temp_chiller_intern": temp_chiller_intern,
                        "temp_air_1": temp_air_1,
                        "temp_air_2": temp_air_2,
                        "temp_pcb": temp_pcb,
                        "temp_Pt1000": temp_Pt1000,
                        "humidity_1": humidity_1,
                        "humidity_2": humidity_2,
                        "air_flow_setpoint": air_flow_setpoint,
                        "air_flow_averaged_measured_value": air_flow_averaged_measured_value
                    }
                }

                ## Print feedback
                if fPrint:
                    print ('{:s}  {:s}  {:0.2f}  {:0.2f}  {:0.2f}  {:0.2f}  {:0.2f}  {:0.2f}  {:0.2f}  {:0.2f}  {:0.2f}'.format(*line))
                """
                ## One file per day
                file_name = time.strftime("%Y_%m_%d", time.localtime())

                ## Create log folder if it dpes not already exist
                if not (os.path.isdir(self.dat_path)):
                    os.makedirs(self.dat_path)

                ## Create file if it does not already exists
                if not (os.path.isfile(self.dat_path + '/' + file_name + '.txt')):
                    file = open(self.dat_path + '/' + file_name + '.txt', 'w')
                    file.write(hd)
                    file.close()

                ## Append file
                file = open(self.dat_path + '/' + file_name + '.txt', 'a')
                file.write('{:s}  {:s}  {:d}  {:d}\n'.format(*line))
                file.close()
                """
                #send to influxdb instance
                json_data = []
                json_data.append(data)
                self.client.write_points(json_data, database='particulars_monitordb')


                if fSingle:
                    fContinous = 0
                else:
                    time.sleep(self.wait)


        ## Break if keyboard interrupt
        except KeyboardInterrupt:
            print ("Keyboard interrupt.") #self.logging.error("Keyboard interrupt.")

#Run code individually:
#run = particulars_monitor()
#run.client.ping()
#run.execute(dew_1=0, dew_2=0, target_temperature=0, setpoint_chiller=0, temp_chiller_intern=0, temp_air_1=0, temp_air_2=0, temp_pcb=0, temp_Pt1000=0, humidity_1=0, humidity_2=0)
