from ctypes import *
import time
import os
import sys
import platform
import tempfile
import re

from PySide6.QtCore import QObject, Signal

if sys.version_info >= (3, 0):
    import urllib.parse

# Dependences

# For correct usage of the library libximc,
# you need to add the file pyximc.py wrapper with the structures of the library to python path.
# Specifies the current directory.
cur_dir = os.path.abspath(os.path.dirname(__file__))
# Formation of the directory name with all dependencies. The dependencies for the examples are located in the ximc directory.
ximc_dir = os.path.join(cur_dir, "ximc")
# Formation of the directory name with python dependencies.
ximc_package_dir = os.path.join(
    ximc_dir, "crossplatform", "wrappers", "python")
sys.path.append(ximc_package_dir)  # add pyximc.py wrapper to python path

# Depending on your version of Windows, add the path to the required DLLs to the environment variable
# bindy.dll
# libximc.dll
# xiwrapper.dll
if platform.system() == "Windows":
    # Determining the directory with dependencies for windows depending on the bit depth.
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"
    libdir = os.path.join(ximc_dir, arch_dir)
    if sys.version_info >= (3, 8):
        os.add_dll_directory(libdir)
    else:
        # add dll path into an environment variable
        os.environ["Path"] = libdir + ";" + os.environ["Path"]

try:
    from pyximc import *
except ImportError as err:
    print("Can't import pyximc module. The most probable reason is that you changed the relative location of the test_Python.py and pyximc.py files. See developers' documentation for details.")
    exit()
except OSError as err:
    # print(err.errno, err.filename, err.strerror, err.winerror) # Allows you to display detailed information by mistake.
    if platform.system() == "Windows":
        # The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.
        if err.winerror == 193:
            print("Err: The bit depth of one of the libraries bindy.dll, libximc.dll, xiwrapper.dll does not correspond to the operating system bit.")
            # print(err)
        # One of the library bindy.dll, libximc.dll, xiwrapper.dll files is missing.
        elif err.winerror == 126:
            print(
                "Err: One of the library bindy.dll, libximc.dll, xiwrapper.dll is missing.")
            print("It is also possible that one of the system libraries is missing. This problem is solved by installing the vcredist package from the ximc\\winXX folder.")
            # print(err)
        else:           # Other errors the value of which can be viewed in the code.
            print(err)
        print("Warning: If you are using the example as the basis for your module, make sure that the dependencies installed in the dependencies section of the example match your directory structure.")
        print(
            "For correct work with the library you need: pyximc.py, bindy.dll, libximc.dll, xiwrapper.dll")
    else:
        print(err)
        print("Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")
    exit()


# START OF CODE INTEGRATION
 
# class LaserControl(QObject):
class LaserPos(QObject):
    finished = Signal()

    def __init__(self):
        super().__init__()

        ## variable 'lib' points to a loaded library
        ## note that ximc uses stdcall on win
        #print("Stage motors library loaded")

         
        sbuf = create_string_buffer(64)
        lib.ximc_version(sbuf)
        #sbuf = create_string_buffer(64)
        #lib.ximc_version(sbuf)
        #print("Library version: " + sbuf.raw.decode().rstrip("\0"))

        # This is device search and enumeration with probing. It gives more information about devices.
        probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
        enum_hints = b"addr="
        # enum_hints = b"addr=" # Use this hint string for broadcast enumerate
        self.devenum = lib.enumerate_devices(probe_flags, enum_hints)
        #print("Device enum handle: " + repr(self.devenum))
        #print("Device enum handle type: " + repr(type(self.devenum)))

        self.dev_count = lib.get_device_count(self.devenum)
        #print("Device count: " + repr(self.dev_count))

        controller_name = controller_name_t()
        for dev_ind in range(0, self.dev_count):
            enum_name = lib.get_device_name(self.devenum, dev_ind)
            result = lib.get_enumerate_device_controller_name(
                self.devenum, dev_ind, byref(controller_name))
            #if result == Result.Ok:  
            #     print("Enumerated device #{} name (port name): ".format(
            #         dev_ind) + repr(enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")


    # START OF NEW FUNCTIONS
    # def laserPos_connect(self):
    #     try:
    #         sbuf = create_string_buffer(64)
    #         lib.ximc_version(sbuf)
    #         probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
    #         enum_hints = b"addr="
    #         self.devenum = lib.enumerate_devices(probe_flags, enum_hints)
    #         self.dev_count = lib.get_device_count(self.devenum)
    #         controller_name = controller_name_t()
    #         for dev_ind in range(0, self.dev_count):
    #             enum_name = lib.get_device_name(self.devenum, dev_ind)
    #             result = lib.get_enumerate_device_controller_name(
    #                 self.devenum, dev_ind, byref(controller_name))
    #     except Exception as e:
    #         print("Failed to connect to laser position")

    # def laserPos_disconnect(self):
    #     if self.connected and self.devenum:
    #         try:
    #             for dev_ind in range(self.dev_count):
    #                 device_name = lib.get_device_name(self.devenum, dev_ind)
    #                 device_id = lib.open_device(device_name)
    #                 if device_id > 0:
    #                     lib.close_device(byref(cast(device_id, POINTER(c_int))))
    #                     print(f"Device {dev_ind} ({device_name}) disconnected.")

    #             del self.devenum
    #             self.devenum = None
    #             self.connected = False
    #             print("Disconnected from all laser position devices.")
    #         except Exception as e:
    #             print(f"Error during disconnection: {e}")
    #     else:
    #         print("No device to disconnect.")

    """This function checks the amount of devices(motors) connected. As there is x,y,x positioning, there should be 3 devices."""
    def checkMotors(self):
       result = lib.get_device_count(self.devenum)
       return result

    """This function gets the current position of the chosen motor"""
    def getMotorPosition(self, axis_id):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)

        position = self.test_get_position(lib, device_id)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done")
        return position

    """This function moves the motor to the left""" 
    def scanLeft(self, axis_id):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)

        self.test_right(lib, device_id)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done") 
        return 

    """This function moves the motor to the right"""
    def scanRight(self, axis_id):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)

        self.test_right(lib, device_id)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done") 
        return   

    """This function moves the motor to a specific destination"""
    def moveMotor(self, axis_id, distance, udistance):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
            open_name = open_name.encode()
        device_id = lib.open_device(open_name)
        distance = c_int(int(distance))
        udistance = c_int(int(udistance))
        self.test_move(lib, device_id, distance, udistance)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done")
        return

    """This function waits for the motor to stop moving"""
    def waitMotorStop(self, axis_id, interval):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)

        self.test_wait_for_stop(lib, device_id, interval)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done")
        return
        

    """This function gets the current speed that is set for the motor"""
    def getMotorSpeed(self, axis_id, return_bolean=False):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)

        speed = self.test_get_speed(lib, device_id, return_bolean)
        if return_bolean:
            return speed
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done")
        return speed

    """This function sets the motor speed in units/sec (mm/s?)"""
    def setMotorSpeed(self, axis_id, speed):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)
        if speed < 200:
             speed = 200
        self.test_set_speed(lib, device_id, speed)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done")
        return

    """This function gets the status of the motor"""
    def motorStatus(self, axis_id):
        open_name = lib.get_device_name(self.devenum, axis_id)
        if type(open_name) is str:
                open_name = open_name.encode()
        device_id = lib.open_device(open_name)

        status = self.test_status(lib, device_id)
        lib.close_device(byref(cast(device_id, POINTER(c_int))))
        print("Done")
        return status


    # START OF EXAMPLE FUNCTIONS NOT USED  
        

    # START OF THE EXAMPLE CODE
    # def test_info(self, lib, device_id):
    #     print("\nGet device info")
    #     x_device_information = device_information_t()
    #     result = lib.get_device_information(
    #         device_id, byref(x_device_information))
    #     print("Result: " + repr(result))
    #     if result == Result.Ok:
    #         print("Device information:")
    #         print(" Manufacturer: " +
    #               repr(string_at(x_device_information.Manufacturer).decode()))
    #         print(" ManufacturerId: " +
    #               repr(string_at(x_device_information.ManufacturerId).decode()))
    #         print(" ProductDescription: " +
    #               repr(string_at(x_device_information.ProductDescription).decode()))
    #         print(" Major: " + repr(x_device_information.Major))
    #         print(" Minor: " + repr(x_device_information.Minor))
    #         print(" Release: " + repr(x_device_information.Release))

    def test_status(self, lib, device_id):
        print("\nGet status")
        x_status = status_t()
        result = lib.get_status(device_id, byref(x_status))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Status.Ipwr: " + repr(x_status.Ipwr))
            print("Status.Upwr: " + repr(x_status.Upwr))
            print("Status.Iusb: " + repr(x_status.Iusb))
            print("Status.Flags: " + repr(hex(x_status.Flags)))

    def test_get_position(self, lib, device_id):
        print("\nRead position")
        x_pos = get_position_t()
        result = lib.get_position(device_id, byref(x_pos))
        print("Result: " + repr(result))
        if result == Result.Ok:
            print("Position: {0} steps, {1} microsteps".format(
                x_pos.Position, x_pos.uPosition))
        return x_pos.Position, x_pos.uPosition

    def test_left(self, lib, device_id):
        print("\nMoving left")
        result = lib.command_left(device_id)
        print("Result: " + repr(result))

    def test_right(self, lib, device_id):
        print("\nMoving right")
        result = lib.command_right(device_id)
        print("Result: " + repr(result))    

    def test_move(self, lib, device_id, distance, udistance):
        print("\nGoing to {0} steps, {1} microsteps".format(
            distance.value, udistance.value
            # distance, udistance
            ))
        result = lib.command_move(device_id, distance, udistance)
        print("Result: " + repr(result))

    def test_wait_for_stop(self, lib, device_id, interval):
        print("\nWaiting for stop")
        result = lib.command_wait_for_stop(device_id, interval)
        print("Result: " + repr(result))

    # def test_serial(self, lib, device_id):
    #     print("\nReading serial")
    #     x_serial = c_uint()
    #     result = lib.get_serial_number(device_id, byref(x_serial))
    #     if result == Result.Ok:
    #         print("Serial: " + repr(x_serial.value))

    def test_get_speed(self, lib, device_id, return_bolean=False):
        print("\nGet speed")
        # Create move settings structure
        mvst = move_settings_t()
        # Get current move settings from controller
        result = lib.get_move_settings(device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        print("Read command result: " + repr(result))
        if return_bolean and result == -1: # return bolean if motor stages are connected or not
            return False
        elif return_bolean and result != -1:
            return True
        else:
            return mvst.Speed

    def test_set_speed(self, lib, device_id, speed):
        print("\nSet speed")
        # Create move settings structure
        mvst = move_settings_t()
        # Get current move settings from controller
        result = lib.get_move_settings(device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        print("Read command result: " + repr(result))
        print("The speed was equal to {0}. We will change it to {1}".format(
            mvst.Speed, speed))
        # Change current speed
        mvst.Speed = int(speed)
        # Write new move settings to controller
        result = lib.set_move_settings(device_id, byref(mvst))
        # Print command return status. It will be 0 if all is OK
        print("Write command result: " + repr(result))

    # def test_set_microstep_mode_256(self, lib, device_id):
    #     print("\nSet microstep mode to 256")
    #     # Create engine settings structure
    #     eng = engine_settings_t()
    #     # Get current engine settings from controller
    #     result = lib.get_engine_settings(device_id, byref(eng))
    #     # Print command return status. It will be 0 if all is OK
    #     print("Read command result: " + repr(result))
    #     # Change MicrostepMode parameter to MICROSTEP_MODE_FRAC_256
    #     # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
    #     eng.MicrostepMode = MicrostepMode.MICROSTEP_MODE_FRAC_256
    #     # Write new engine settings to controller
    #     result = lib.set_engine_settings(device_id, byref(eng))
    #     # Print command return status. It will be 0 if all is OK
    #     print("Write command result: " + repr(result))


    # START OF TESTING MOVEMENT OF ALL 3 MOTORS
    ## This now works, should be changed in order to automatically calibrate laser
    # def test_laser_control(self):
    #     axis_id = 0
    #     while axis_id < 3:
    #         flag_virtual = 0
    #         open_name = None
    #         if len(sys.argv) > 1:
    #             open_name = sys.argv[1]
    #         elif self.dev_count > 0:
    #             # This is where you choose which device to move!!! right now the second parameter is a number, but could maybe make a for loop?
    #             open_name = lib.get_device_name(self.devenum, axis_id)
    #             # device 0 is axis 2 (front to back) y
    #             # device 1 is axis 1 (left to right) x
    #             # device 2 is axis 3 (up and down) z
    #         elif sys.version_info >= (3, 0):
    #             # use URI for virtual device when there is new urllib python3 API
    #             tempdir = tempfile.gettempdir() + "/testdevice.bin"
    #             if os.altsep:
    #                 tempdir = tempdir.replace(os.sep, os.altsep)
    #             # urlparse build wrong path if scheme is not file
    #             uri = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme="file",
    #                                                                     netloc=None, path=tempdir, params=None, query=None, fragment=None))
    #             open_name = re.sub(r'^file', 'xi-emu', uri).encode()
    #             flag_virtual = 1
    #             print("The real controller is not found or busy with another app.")
    #             print("The virtual controller is opened to check the operation of the library.")
    #             print("If you want to open a real controller, connect it or close the application that uses it.")

    #         if not open_name:
    #             exit(1)

    #         if type(open_name) is str:
    #             open_name = open_name.encode()

    #         print("\nOpen device " + repr(open_name))
    #         device_id = lib.open_device(open_name)
    #         print("Device id: " + repr(device_id))

    #         self.test_info(lib, device_id)
    #         self.test_status(lib, device_id)
    #         #self.test_set_microstep_mode_256(lib, device_id)
    #         #current_speed = self.test_get_speed(lib, device_id)
    #         self.test_set_speed(lib, device_id, 3968/2)

    #         startpos, ustartpos = self.test_get_position(lib, device_id)
            
    #         # first move
    #         self.test_move(lib, device_id, -1000, 0)
    #         self.test_wait_for_stop(lib, device_id, 100)

    #         # first move
    #         self.test_move(lib, device_id, 1000, 0)
    #         self.test_wait_for_stop(lib, device_id, 100)
            
    #         ## second move
    #          
    #         self.test_move(lib, device_id, 50, 0)
    #         # self.test_move(lib, device_id, 0, 0)
    #         self.test_wait_for_stop(lib, device_id, 100)
    #         #self.test_status(lib, device_id)
    #         #self.test_serial(lib, device_id)

    #         print("\nClosing")

    #         # The device_t device parameter in this function is a C pointer, unlike most library functions that use this parameter
    #         lib.close_device(byref(cast(device_id, POINTER(c_int))))
    #         print("Done")

    #         if flag_virtual == 1:
    #             print(" ")
    #             print("The real controller is not found or busy with another app.")
    #             print("The virtual controller is opened to check the operation of the library.")
    #             print("If you want to open a real controller, connect it or close the application that uses it.")

    #         self.finished.emit()
    #         axis_id = axis_id + 1
