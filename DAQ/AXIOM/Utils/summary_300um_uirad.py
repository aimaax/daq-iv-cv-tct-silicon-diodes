import os
import pandas as pd
import re
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import REFERENCE_UIRAD_DIODE_DIRECTORY, ROOT_DIRECTORY

def create_300um_uirad_summary_csv():
    results = []

    folder_pattern = re.compile(r"300um_UIRAD_253_(\d{6})_Laser(\d+)")

    if not os.path.exists(REFERENCE_UIRAD_DIODE_DIRECTORY):
        print(f"Error: Directory '{REFERENCE_UIRAD_DIODE_DIRECTORY}' does not exist")
        print("Did not create summary. Please check the path in the config.py file")
        return
    
    if not os.path.exists(ROOT_DIRECTORY):
        print(f"Error: Directory '{ROOT_DIRECTORY}' does not exist")
        print("Please write a valid root directory in the config.py file")
        return

    for entry in os.listdir(REFERENCE_UIRAD_DIODE_DIRECTORY):
        folder_path = os.path.join(REFERENCE_UIRAD_DIODE_DIRECTORY, entry)
        if os.path.isdir(folder_path):
            match = folder_pattern.match(entry)
            if match:
                date = match.group(1)
                laser_value = match.group(2)

                csv_filename = f"{entry}.csv"
                csv_path = os.path.join(folder_path, csv_filename)

                if os.path.isfile(csv_path):
                    try:
                        df = pd.read_csv(csv_path)
                        mean_cce2 = df["CCE2[a.u.]"].mean()
                        results.append({
                            "Date": date,
                            "Laser_mV": int(laser_value),
                            "MeanCC": int(round(mean_cce2, ndigits=0)),
                            "CSVPath": csv_path
                        })
                    except Exception as e:
                        print(f"Error processing {csv_path}: {e}")

    output_df = pd.DataFrame(results)

    if not output_df.empty:
        output_df = output_df.sort_values("Date")  # Ensure chronological order

    save_directory = os.path.join(ROOT_DIRECTORY, "Results")
    os.makedirs(save_directory, exist_ok=True)
    save_path = os.path.join(save_directory, "300um_UIRAD_summary.csv")
    output_df.to_csv(save_path, index=False)

    print(f"Processing complete. Output saved to '{save_path}'")

    if not output_df.empty:
        latest_5 = output_df.tail(5)
        show_latest_5_with_plot(latest_5)


def show_latest_5_with_plot(df_latest_5):
    """
    Popup with latest 5 rows and a matplotlib figure below.
    Clicking a row updates the plot to show that CSV's raw data.
    """
    dialog = QDialog()
    dialog.setWindowTitle("Latest 5 Measurements & Raw Plot")
    layout = QVBoxLayout(dialog)

    # --- Table for latest 5 measurements ---
    table = QTableWidget(len(df_latest_5), 3)
    table.setHorizontalHeaderLabels(["Date", "Laser (mV)", "Mean CC"])
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setEditTriggers(QTableWidget.NoEditTriggers)

    for row_idx, (_, row) in enumerate(df_latest_5.iterrows()):
        table.setItem(row_idx, 0, QTableWidgetItem(str(row["Date"])))
        table.setItem(row_idx, 1, QTableWidgetItem(str(row["Laser_mV"])))
        table.setItem(row_idx, 2, QTableWidgetItem(str(row["MeanCC"])))
        # Store CSV path in vertical header
        table.setVerticalHeaderItem(row_idx, QTableWidgetItem(row["CSVPath"]))

    layout.addWidget(table)

    # --- Matplotlib figure ---
    fig = Figure(figsize=(6, 4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.set_title("Charge Collection of 300um UIRAD")
    ax.set_xlabel("Voltage [V]")
    ax.set_ylabel("Charge Collection [a.u.]")
    ax.grid(True)

    layout.addWidget(canvas)

    def update_plot(row_idx):
        csv_path = table.verticalHeaderItem(row_idx).text()
        try:
            df = pd.read_csv(csv_path)
            ax.clear()
            ax.plot(df["Voltage"], df["CCE2[a.u.]"], marker="o", linestyle='None')
            ax.set_title(f"Charge Collection of 300um UIRAD - {os.path.basename(csv_path)}")
            ax.set_xlabel("Voltage [V]")
            ax.set_ylabel("Charge Collection [a.u.]")
            ax.grid(True)
            canvas.draw()
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Could not display data:\n{e}")

    # Connect row click to update plot
    def on_cell_clicked(row, column):
        update_plot(row)

    table.cellClicked.connect(on_cell_clicked)

    # Optionally, show first row by default
    if df_latest_5.shape[0] > 0:
        update_plot(0)

    dialog.setLayout(layout)
    dialog.resize(1250, 600)
    dialog.exec()