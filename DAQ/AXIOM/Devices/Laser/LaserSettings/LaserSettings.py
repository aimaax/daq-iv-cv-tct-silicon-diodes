# my_client.py

from msl.loadlib import Client64
import sys
import os

# For correct usage of the 32server, you must add my_server to sys.path
# Specifies the current directory.
# server32_dir = os.path.abspath(os.path.dirname(__file__))
# sys.path.append(server32_dir)  # add my_server.py wrapper to python path

server32_dir = os.path.abspath(os.path.dirname(__file__))

# Remove the path if it already exists in sys.path
if server32_dir in sys.path:
    sys.path.remove(server32_dir)
    print('remove sys path')

# Add the current directory to sys.path
sys.path.append(server32_dir)


class LaserSettings(Client64):
    """Call a function in 'LaserLibrary.dll' via the 'MyServer' wrapper."""

    def __init__(self):
        # Specify the name of the Python module to execute on the 32-bit server (i.e., 'my_server')
        super(LaserSettings, self).__init__(module32='MyServer')

    """These functions are always used throughout the Particulars Software"""
    def checkDevice(self):
        return self.request32('checkDevice')

    def checkLaserState(self):
        return self.request32('checkLaserState')
    
    def turnLaserOff(self):
        return self.request32('turnLaserOff')

    """These functions are used in the Particulars Single Frequency tab."""
    def setLaserFrequency(self, frequency):
        return self.request32('setLaserFrequency', frequency)
    
    """These functions are used in the Particulars Pulse Control tab."""
    
    #dont use?
    def toggleHardSeq(self, state): #bool
        return self.request32('toggleHardSeq', state)
    #####

    def toggleEXTInterrupt(self, state): #bool
        return self.request32('toggleEXTInterrupt', state)
    
    def toggleRIT(self, state): #bool
        return self.request32('toggleRIT', state)
    
    def clearLaserMCU(self):
        return self.request32('clearLaserMCU')
    
    def laserInterruptPeriod(self, value): #long int
        return self.request32('laserInterruptPeriod', value)
    
    def laserSeqMode(self, mode): #int
        return self.request32('laserSeqMode', mode)
    
    def sendLaserFrequency(self, frequency): #int
        return self.request32('sendLaserFrequency', frequency)
    
    #dont use?
    def generateSeq(self):
        return self.request32('generateSeq')
    #####

    """These functions are used in the Particulars Pulse Width tab."""
    def toggleDAC(self, state): #bool
        return self.request32('toggleDAC', state)
    
    def setLaserDAC(self, value): #int
        return self.request32('setLaserDAC', value)

    """These functions are used in the Particulars General tab."""
    def laserADCData(self, channel): #int
        return self.request32('laserADCData', channel)
    
    def acquireLaserADC(self):
        return self.request32('acquireLaserADC')
    
    def defaultFile(self):
        return self.request32('defaultFile')
    
    def selectOutputFile(self, dFile): #char*
        return self.selectOutputFile('defaultFile', dFile)
    
    # def cleanup(self):
    #     try:
    #         self.turnLaserOff()
    #         self.disconnect()
    #     except Exception as e:
    #         print(f"Error during cleanup: {e}")

    # def disconnect(self):
    #     """
    #     This method handles the disconnection and cleanup of resources.
    #     Ensure that the laser is safely turned off and all connections are closed.
    #     """
    #     try:
    #         print("Disconnecting from laser...")
    #         self.request32('shutdown')
    #         print("Laser disconnected.")
    #     except Exception as e:
    #         print(f"Error during disconnection: {e}")