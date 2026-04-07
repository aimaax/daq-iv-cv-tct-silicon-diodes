import numpy as np
import os
from PySide6.QtCore import QObject, Signal
from DAQ.AXIOM.Utils.TCTAnalysis import TCTAnalysis

class TCTAnalysisSequence(QObject):

    finished = Signal()

    def __init__(self, voltage_stop, voltage_start, voltage_step, analysis_active, path, plot_canvas):
        super().__init__()

        self.analysis_active = analysis_active
        self.plot_canvas = plot_canvas
        self.voltages = []
        self.path = path
        self.folder_name = os.path.basename(os.path.normpath(self.path))

        self.voltage_stop = voltage_stop
        self.voltage_start = voltage_start
        self.voltage_step = voltage_step

        self.voltage_step = abs(self.voltage_step)
        if self.voltage_stop < self.voltage_start:
            self.voltage_step = -self.voltage_step
        include_value = -1 if self.voltage_step < 0 else 1
        if self.voltage_step != 0:
            self.volt_list_TCT = range(self.voltage_start, self.voltage_stop+include_value, self.voltage_step)
        else:
            self.volt_list_TCT = [0]*10

        
        # Iterate directory
        self.files = []
        for file_path in os.listdir(self.path):
            # check if current file_path is a file
            if os.path.isfile(os.path.join(self.path, file_path)):
                if file_path.endswith(".npz"):
                    # add filename to list
                    self.files.append(file_path)
        self.analysis = TCTAnalysis(path=self.path, amplitude_perc=30, filter_intensity=5, graph_size=1, curve_sensitivity=300.0, num_bins=25, usage=0)
        
    
    def perform_analysis(self):
        #index = folder_name.find('_')
        #for _, v in enumerate(self.volt_list_TCT):
        for _, v in enumerate(self.files):
                if not self.analysis_active():
                    break
                #self.voltages.append(v)
                #content = np.load(self.path+"/"+folder_name[:index]+"_"+str(v)+folder_name[index:]+".npz")
                content = np.load(self.path+"/"+str(v))
                self.analysis.get_data(content, mode=0)
                self.analysis.display_metadata()
                self.analysis.convert_to_current()
                self.analysis.discard_waveforms()
                self.analysis.average_waveform()
                self.analysis.find_integration_paramaters()
                self.analysis.integrate_waveforms()
                self.analysis.plot_histogram()
        print("Storing in csv")
        self.analysis.store_in_csv()
        self.plot_canvas.clear_graph()
        self.plot_canvas.plot_graph_analysis(self.analysis.volt_dict,self.analysis.cce)
        self.finished.emit()

    