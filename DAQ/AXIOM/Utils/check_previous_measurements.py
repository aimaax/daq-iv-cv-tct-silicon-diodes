from PySide6.QtWidgets import QMessageBox
import os
import pandas as pd
import numpy as np
import re
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

def check_previous_voltage_settings(sensor_name: str, campaign_measurement_directory: str, CV_or_TCT: str = 'CV'):
    """
    Check voltage settings for previous measurements.
    Only for CV and TCT measurements.
    """

    if not sensor_name:
        QMessageBox.warning(
            None,
            "No Sensor Name",
            "Please enter a sensor name first."
        )
        return
    
    # Construct directory path
    directory = os.path.join(
        campaign_measurement_directory,
        "IVCV_onPCB" if CV_or_TCT == 'CV' else "TCT",
        sensor_name
    )
    
    # Check if directory exists
    if not os.path.exists(directory):
        QMessageBox.warning(
            None,
            "Directory Not Found",
            f"No measurements found for sensor: {sensor_name}\n\nPath: {directory}"
        )
        return
    

    # Find all CSV files in the directory (excluding temperature files)
    if CV_or_TCT == 'CV':
        csv_files = [
            f for f in os.listdir(directory) if f.lower().endswith("_cv.csv") 
        ]
    elif CV_or_TCT == 'TCT':
        subdirs = [
            d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))
        ]

        csv_files = [
            f for subdir in subdirs for f in os.listdir(os.path.join(directory, subdir)) if f == subdir + ".csv"
        ]

    if not csv_files:
        QMessageBox.information(
            None,
            "No Files Found",
            f"No CV measurement files found in:\n{directory}"
        )
        return
    
    # Parse voltage settings from each file
    measurements_data = []
    
    for csv_file in csv_files:
        if CV_or_TCT == 'CV':
            file_path = os.path.join(directory, csv_file)
        elif CV_or_TCT == 'TCT':
            subdir = csv_file.split('.')[0]
            file_path = os.path.join(directory, subdir, csv_file)
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path, delimiter=";") if CV_or_TCT == 'CV' else pd.read_csv(file_path, delimiter=",")
            
            # Extract set voltages from the second column
            if "set voltage (V)" in df.columns if CV_or_TCT == 'CV' else "Voltage" in df.columns:
                voltages = df["set voltage (V)"].values if CV_or_TCT == 'CV' else df["Voltage"].values
                
                # Calculate voltage settings
                start_voltage = voltages[0]
                stop_voltage = voltages[-1]

                # Calculate step sizes
                voltage_diffs = np.diff(voltages)
                unique_diffs = np.unique(np.abs(voltage_diffs))
                
                if len(unique_diffs) == 1:
                    # Uniform step size throughout
                    voltage_step_size = unique_diffs[0]
                    fine_voltage_start = "-"
                    fine_voltage_stop = "-"
                    fine_step_size = "-"
                else:
                    # Non-uniform step size (fine voltage enabled)
                    # Smallest step is fine step, largest is coarse step
                    fine_step_size = np.min(unique_diffs)
                    voltage_step_size = np.max(unique_diffs)
                    
                    # Find where fine voltage steps occur
                    # Look for steps that match the fine step size (to exclude transition steps)
                    abs_diffs = np.abs(voltage_diffs)
                    
                    # Find indices where step size equals fine step size
                    fine_indices = np.where(np.abs(abs_diffs - fine_step_size) < 1e-6)[0]
                    
                    if len(fine_indices) > 0:
                        # Fine voltage starts at the voltage where the first fine step begins
                        # The voltage at fine_indices[0] is the voltage BEFORE the first fine step
                        # So fine voltage starts at fine_indices[0] + 1
                        fine_voltage_start = voltages[fine_indices[0]]
                        
                        # Fine voltage stops at the voltage after the last fine step
                        # The voltage at fine_indices[-1] + 1 is the voltage AFTER the last fine step
                        fine_voltage_stop = voltages[fine_indices[-1] + 1]
                    else:
                        # Fallback: if no exact fine step matches, use the old logic
                        # Find indices where step size is smaller than coarse step
                        fine_indices = np.where(abs_diffs < voltage_step_size)[0]
                        
                        if len(fine_indices) > 0:
                            fine_voltage_start = voltages[fine_indices[0] + 1]
                            fine_voltage_stop = voltages[fine_indices[-1] + 1]
                        else:
                            fine_voltage_start = "-"
                            fine_voltage_stop = "-"
                
                measurements_data.append({
                    "FilePath": file_path,
                    "Filename": csv_file,
                    "Start Voltage": start_voltage,
                    "Stop Voltage": stop_voltage,
                    "Voltage Step": voltage_step_size,
                    "Fine Voltage Start": fine_voltage_start,
                    "Fine Voltage Stop": fine_voltage_stop,
                    "Fine Step": fine_step_size
                })
        
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
            continue
    
    if not measurements_data:
        QMessageBox.warning(    
            None,
            "No Valid Data",
            "Could not parse voltage settings from any files."
        )
        return

    # Sort measurements by annealing time (numerically, with 'noadd' at bottom)
    measurements_data.sort(key=lambda x: _extract_annealing_time(x["Filename"]), reverse=True)

    # Create QDialog to display the data
    _show_voltage_settings_dialog(measurements_data, sensor_name, CV_or_TCT)


def _show_voltage_settings_dialog(measurements_data, sensor_name, CV_or_TCT):
    """
    Display a QDialog with previous voltage settings in a table.
    Clicking a row displays the CV plot on the right.
    
    Args:
        measurements_data: List of dictionaries containing voltage settings
        sensor_name: Name of the sensor
    """
    
    dialog = QDialog()
    dialog.setWindowTitle(f"Previous CV Measurements - {sensor_name}")
    
    # Main horizontal layout (table on left, plot on right)
    main_layout = QHBoxLayout(dialog)
    
    # Left side: Table in a vertical layout
    left_layout = QVBoxLayout()
    
    # Create table
    table = QTableWidget(len(measurements_data), 6)
    table.setHorizontalHeaderLabels([
        "Filename",
        "Start Voltage",
        "Stop Voltage",
        "Voltage Step",
        "Fine Voltage Stop" if CV_or_TCT == 'CV' else "Fine Voltage Start",
        "Fine Step"
    ])

    # Set table properties
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    # Populate table and store file paths
    for row_idx, measurement in enumerate(measurements_data):
        # Store the full file path in the first column item's user data
        filename_item = QTableWidgetItem(measurement["Filename"])
        filename_item.setData(Qt.UserRole, measurement.get("FilePath", ""))
        table.setItem(row_idx, 0, filename_item)
        
        table.setItem(row_idx, 1, QTableWidgetItem(str(measurement["Start Voltage"])))
        table.setItem(row_idx, 2, QTableWidgetItem(str(measurement["Stop Voltage"])))
        table.setItem(row_idx, 3, QTableWidgetItem(str(measurement["Voltage Step"])))
        
        # Handle fine voltage settings
        if CV_or_TCT == 'CV':
            fine_stop_start = measurement["Fine Voltage Stop"]
        elif CV_or_TCT == 'TCT':
            fine_stop_start = measurement["Fine Voltage Start"]
        fine_step = measurement["Fine Step"]
        
        table.setItem(row_idx, 4, QTableWidgetItem(str(fine_stop_start)))
        table.setItem(row_idx, 5, QTableWidgetItem(str(fine_step)))
    
    # Resize columns to content
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.horizontalHeader().setStretchLastSection(True)
    
    left_layout.addWidget(table)
    
    # Right side: Matplotlib figure
    fig = Figure(figsize=(8, 6), dpi=150, constrained_layout=True)
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Voltage [V]", fontsize=12)
    if CV_or_TCT == 'CV':
        ax.set_ylabel("1/Capacitance² [1/F²]", fontsize=12)
    elif CV_or_TCT == 'TCT':
        ax.set_ylabel("Collected Charge [a.u.]", fontsize=12)
    ax.grid(True, linestyle=":", alpha=0.5)
    
    def update_plot(row_idx):
        """Update the plot when a row is clicked"""
        file_path = table.item(row_idx, 0).data(Qt.UserRole)
        filename = table.item(row_idx, 0).text()
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(dialog, "Error", f"File not found: {file_path}")
            return
        
        try:
            # Read the CSV file
            df = pd.read_csv(file_path, delimiter=";") if CV_or_TCT == 'CV' else pd.read_csv(file_path, delimiter=",")
            
            # Extract data
            if CV_or_TCT == 'CV':
                voltages = abs(df["set voltage (V)"].values)
                capacitance_inv_sq = df["1/serial capacitance^2"].values
            elif CV_or_TCT == 'TCT':
                voltages = abs(df["Voltage"].values)
                collected_charge = df["CCE2[a.u.]"].values
            
            # Clear and update plot
            ax.clear()
            if CV_or_TCT == 'CV':
                ax.plot(voltages, capacitance_inv_sq, marker="o", linestyle="-", markersize=5, color="#bf3333")
            elif CV_or_TCT == 'TCT':
                ax.plot(voltages, collected_charge, marker="o", linestyle="-", markersize=5, color="#bf3333")
            ax.set_xlabel("Voltage [V]", fontsize=12)
            if CV_or_TCT == 'CV':
                ax.set_ylabel("1/Capacitance² [1/F²]", fontsize=12)
            elif CV_or_TCT == 'TCT':
                ax.set_ylabel("Collected Charge [a.u.]", fontsize=12)
            ax.grid(True, linestyle=":", alpha=0.5)
            canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(
                dialog,
                "Error",
                f"Could not display data:\n{str(e)}"
            )
    
    # Connect row click to update plot
    def on_cell_clicked(row, column):
        update_plot(row)
    
    table.cellClicked.connect(on_cell_clicked)
    
    # Optionally, show first row by default
    if len(measurements_data) > 0:
        update_plot(0)
        table.selectRow(0)
    
    # Add layouts to main layout
    main_layout.addLayout(left_layout, stretch=1)  # Table takes 1 part
    main_layout.addWidget(canvas, stretch=1)  # Plot takes 1 part
    
    dialog.setLayout(main_layout)
    dialog.resize(1500, 700)
    dialog.exec()

def _extract_annealing_time(filename):
    """
    Extract annealing time from filename for sorting.
    Returns a tuple (time_value, filename) where time_value is:
    - The numeric annealing time if found (e.g., 735 from '735min')
    - 0 if 'noadd' is in the filename
    - 0 if no annealing info is found
    
    Args:
        filename: The CSV filename to parse
        
    Returns:
        Numeric value for sorting
    """
    filename_lower = filename.lower()
    
    # Check if 'noadd' is in filename 
    if "noadd" in filename_lower:
        return 0
    
    # Try to extract annealing time (e.g., '920min' -> 920)
    match = re.search(r"(\d+)min", filename_lower)
    if match:
        return int(match.group(1))
    
    # If no annealing info found, put at beginning
    return 0