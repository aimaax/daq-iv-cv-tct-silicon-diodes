# my_server.py

from msl.loadlib import Server32

class MyServer(Server32):
    """Wrapper around a 32-bit C++ library 'LaserLibrary.dll' that controls the settings of the Particulars Laser."""
    """For more information on the functions take a look at LaserLibrary.h. The function names are the same and there is a proper description."""

    def __init__(self, host, port, **kwargs):
        # Load the 'my_lib' shared-library file using ctypes.CDLL
        super(MyServer, self).__init__('./include/LaserLibrary.dll', 'cdll', host, port)

    def checkDevice(self):
        return self.lib.checkDevice()
    
    def checkLaserState(self):
        return self.lib.checkLaserState()
    
    def setLaserFrequency(self, frequency):
        return self.lib.setLaserFrequency(frequency)
    
    def turnLaserOff(self):
        return self.lib.turnLaserOff()
    
    def toggleHardSeq(self, state):
        return self.lib.toggleHardSeq(state)
    
    def toggleDAC(self, state):
        return self.lib.toggleDAC(state)
    
    def toggleEXTInterrupt(self, state):
        return self.lib.toggleEXTInterrupt(state)
    
    def toggleRIT(self, state):
        return self.lib.toggleRIT(state)
    
    def clearLaserMCU(self):
        return self.lib.clearLaserMCU()
    
    def setLaserDAC(self, value):
        return self.lib.setLaserDAC(value)
    
    def laserInterruptPeriod(self, value):
        return self.lib.laserInterruptPeriod(value)
    
    def laserADCData(self, channel):
        return self.lib.laserADCData(channel)
    
    def laserSeqMode(self, mode):
        return self.lib.laserSeqMode(mode)
    
    def sendLaserFrequency(self, frequency):
        return self.lib.sendLaserFrequency(frequency)
    
    def acquireLaserADC(self):
        return self.lib.acquireLaserADC()
    
    def generateSeq(self):
        return self.lib.generateSeq()
    
    def defaultFile(self):
        return self.lib.defaultFile()
    
    def selectOutputFile(self, dFile):
        return self.lib.selectOutputFile(dFile)
    
    # def shutdown(self):
    #     # Perform cleanup if the DLL provides such a function
    #     if hasattr(self, 'lib') and self.lib is not None:
    #         try:
    #             # Example: If your DLL has a cleanup function, call it here
    #             if hasattr(self.lib, 'CloseLibrary'):
    #                 self.lib.CloseLibrary()  # Replace with the actual cleanup function if available
    #             print("DLL cleanup completed.")
    #         except Exception as e:
    #             print(f"Error during DLL cleanup: {e}")