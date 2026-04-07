Code Architecture: Particulars Setup
===

This document describes the software architecture, module structure, and design patterns of the Particulars Setup DAQ (Data Acquisition) system. For information on how to operate the setup and run measurements, see [README.md](README.md).

[TOC]

# Overview

The Particulars Setup software is a **PySide6 (Qt for Python)** desktop application used at CERN to characterize irradiated silicon test structures. It integrates:

- **IV** (Current-Voltage), **CV** (Capacitance-Voltage), and **TCT** (Transient Current Technique) measurements
- **Temperature and environment control** (chiller, Peltier PID, humidity, air flow)
- **Automated laser alignment** and 2D/3D scanning
- **Post-measurement analysis** (waveform integration, charge collection)
- **Data management** (file organization, CSV aggregation, Git sync to CERNBox)
- **Monitoring** (InfluxDB logging for Grafana dashboards)

The software is designed to run on the dedicated lab computer (`pcdttp04`) and communicates with instruments via GPIB (PyVISA), serial (pyserial), DLL/ctypes (laser), and gRPC (high-speed oscilloscope).


# Repository Structure

```
particulars_setup/
├── start_GUI.py                  # Application entry point
├── config.py                     # Global configuration constants
├── measurement_config.json       # Runtime PID / temperature / measurement config
├── requirements.txt              # Python dependencies (56 packages)
├── ARCHITECTURE.md               # This file
├── README.md                     # Operations manual (hardware, cabling, how to measure)
│
├── DAQ/                          # Data Acquisition software
│   ├── AXIOM/                    # Main Python DAQ system
│       ├── MainPanel.py          # Central GUI window (QMainWindow)
│       ├── Devices/              # Instrument driver classes
│       ├── GUI_TCT/              # TCT measurement GUI panels
│       ├── GUI_temp_IV_CV/       # IV/CV measurement and temperature GUI panels
│       ├── TemperatureControl/   # Temperature and environment subsystem
│       ├── Utils/                # Utilities, analysis, measurement sequences, plotting
│       └── LoggingCode/          # InfluxDB logger for Grafana
│
└── Documentation/
    └── Pictures/                 # Images used in README documentation
```


# Application Entry Point

The application is started by running `start_GUI.py` from the repository root:

```
python start_GUI.py
```

This file creates the Qt application, applies the Fusion style, instantiates `MainPanel` (the main window), and connects cleanup logic for a safe shutdown when the application exits.

```
start_GUI.py
    └── MainPanel (QMainWindow)
            ├── TemperatureControlPanel (left sidebar)
            ├── TempHumPlot (center: live temperature/humidity graphs)
            └── QTabWidget (right: measurement tabs)
                    ├── Tab 0: IVCVPanel (IV)
                    ├── Tab 1: IVCVPanel (CV)
                    └── Tab 2: TCTPanel
```


# Configuration

## `config.py` — Static Defaults

Contains compile-time constants imported throughout the codebase:

| Category | Examples |
|----------|---------|
| **Paths** | `CAMPAIGN_MEASUREMENT_DIRECTORY`, `REFERENCE_UIRAD_DIODE_DIRECTORY`, `PARTICULARS_ANALYSIS_DIRECTORY` |
| **TCT voltage defaults** | `TCT_START_VOLTAGE` (-900 V), `TCT_STOP_VOLTAGE` (-50 V), `TCT_VOLTAGE_STEP_SIZE` (50 V) |
| **IV/CV voltage defaults** | `IV_CV_START_VOLTAGE` (-25 V), `IV_CV_STOP_VOLTAGE` (-900 V), `IV_CV_VOLTAGE_STEP_SIZE` (25 V) |
| **Instrument settings** | `COMPLIANCE_VALUE_DEFAULT` (100 uA), `RAMPING_SPEED_DEFAULT` (5 V/s), `LCR_FREQ_DEFAULT` (2 kHz) |
| **Oscilloscope** | `OSCILLOSCOPEHSI` (True/False toggle), `OSCILLOSCOPEHSI_IP`, `WF_PER_VBIAS_DEFAULT` (200) |
| **Peltier limits** | `PELTIER_MAX_CURRENT` (5 A), `PELTIER_MAX_VOLTAGE` (12 V) |
| **Analysis** | `LOWER_INTEGRATION_LIMIT` (240), `UPPER_INTEGRATION_LIMIT` (360) |

## `measurement_config.json` — Runtime Settings

A JSON file read/written at runtime by the temperature control subsystem. Contains PID parameters (`Kp`, `Ki`, `Kd`), target temperature, chiller setpoint, and Peltier activation state. This file is managed through `TemperatureControl/temperature_config.py`.


# Main Panel (`MainPanel.py`)

`MainPanel` is the central `QMainWindow` that orchestrates the entire application. It is responsible for:

1. **GUI layout**: Arranges the temperature control sidebar, live monitoring plots, and measurement tab widget (IV, CV, TCT).
2. **Environment control**: Creates `EnvironmentControl` and runs it in a dedicated `QThread` with a 2-second update loop.
3. **Measurement orchestration**: Starts IV, CV, and TCT measurements in separate `QThread` workers.
4. **Measurement chaining**: Supports automatic IV → CV → TCT sequencing via checkboxes (priority order: IV > CV > TCT).
5. **Switchbox routing**: Routes signal paths between IV (channel 3), CV (channel 2), and TCT (channel 1) circuits.
6. **File management**: Automatically creates directories under `<campaign>/IVCV_onPCB/<sensor>` or `<campaign>/TCT/<sensor>`, checks for filename conflicts, and validates sensor name consistency.
7. **Data sync**: Aggregates CSV files into `_IV_ALL_CSV`, `_CV_ALL_CSV`, and `_TCT_ALL_CSV` folders per campaign, and pushes them to the `particulars-analysis` Git repository.
8. **Safety**: Ramps down all Keithley power supplies on exit via `cleanup_exit()`.


# Device Drivers (`DAQ/AXIOM/Devices/`)

All instrument communication is encapsulated in dedicated driver classes.

## Instrument Overview

| File | Class | Instrument | Communication | GPIB Address | Purpose |
|------|-------|-----------|---------------|-------------|---------|
| `KeithleyDevice.py` | `KeithleyDevice` | — (base class) | GPIB via PyVISA | — | Common Keithley functions: output on/off, voltage/current setting, ramping, limits |
| `ke2410.py` | `ke2410(KeithleyDevice)` | Keithley 2410 SourceMeter | GPIB via PyVISA | 4 (IV/CV) or 7 (TCT) | Voltage source for biasing the DUT. Two physical units in the setup |
| `ke6487.py` | `ke6487(KeithleyDevice)` | Keithley 6487 Picoammeter | GPIB via PyVISA | 22 | High-sensitivity current measurement for IV |
| `ke2001.py` | `ke2001` | Keithley 2001 Multimeter | GPIB via PyVISA | 16 | PT1000 resistance/temperature readout |
| `hp4980.py` | `hp4980` | Keysight E4980 LCR Meter | GPIB via PyVISA | 17 | Capacitance measurement for CV |
| `tsx3510P.py` | `tsx3510P` | TSX3510P DC PSU | GPIB via PyVISA | 6 | Peltier element power supply |
| `Oscillocope.py` | `Oscilloscope(QObject)` | Tektronix MSO54 | SCPI via PyVISA | — | Standard waveform acquisition via binary transfer |
| `OscilloScopeHSI.py` | `OscilloscopeHSI` | Tektronix MSO54 | TekHSI via gRPC | — | High-speed waveform acquisition with FastFrame support |

## Laser Subsystem (`Devices/Laser/`)

| Subdirectory | Class | Purpose | Interface |
|-------------|-------|---------|-----------|
| `LaserPos/` | `LaserPos` | XYZ motor stage positioning (Standa stages) | XIMC C library via ctypes. Axes: X=1 (left-right), Y=0 (front-back), Z=2 (up-down) |
| `LaserSettings/` | `LaserSettings` | Laser pulse control (frequency, DAC, sequences, pulse width) | `LaserLibrary.dll` via `MyServer.py` (msl-loadlib 32-bit server) |


# Measurement Sequences (`DAQ/AXIOM/Utils/MeasurementSequences/`)

Each measurement type is implemented as a `QObject` subclass that runs in a `QThread`. The sequences communicate back to the GUI via Qt `Signal` objects.

## Sequence Classes

### `MeasurementSequenceIV`
- **Devices**: `ke2410` (GPIB 4, voltage source) + `ke6487` (GPIB 22, picoammeter)
- **Switchbox**: Channel 3 (IV circuit)
- **Workflow**: Ramps voltage from start to stop in steps, measures current at each point with configurable delay and sample count. Checks compliance at each step.
- **Output**: CSV file with voltage and current data. Live plot updates during measurement.
- **Safety**: Ramps down on abort or compliance breach. Optional ramp to -600 V after measurement (for subsequent TCT).

### `MeasurementSequenceCV`
- **Devices**: `ke2410` (GPIB 4, voltage source) + `hp4980` (GPIB 17, LCR meter)
- **Switchbox**: Channel 2 (CV circuit)
- **Workflow**: Voltage sweep with optional fine steps in a configurable range. At each voltage point, queries LCR meter for capacitance. Supports open correction mode for calibration.
- **Output**: CSV file with voltage, capacitance (Cp, Cs), dissipation, 1/C^2, and leakage current. Live plot of C-V and 1/C^2-V curves.
- **Corrections**: Applies series/parallel equivalent circuit corrections via `correct_cv.py`.

### `MeasurementSequenceTCT`
- **Devices**: `ke2410` (GPIB 7, voltage source) + Oscilloscope (standard or HSI) + Laser
- **Switchbox**: Channel 1 (TCT circuit, default)
- **Workflow**: Sweeps bias voltage, acquires multiple waveforms at each step. Supports fine voltage steps. Saves waveform data with full metadata headers.
- **Output**: Compressed NumPy `.npz` files per voltage point, each containing an array of waveforms (shape: `[num_wf, 2, points_per_wf]` where channel 0 is time and channel 1 is voltage). A metadata header array stores sensor info, voltage, current, timestamps, and user info.
- **Modes**: Standard SCPI oscilloscope mode or High-Speed Interface (HSI) mode via gRPC with FastFrame support for faster multi-waveform acquisition.

### `TCTAreaScanSequence`
- **Purpose**: 2D XY raster scan at fixed bias voltage.
- **Devices**: Motor stages + oscilloscope + laser
- **Workflow**: Moves the laser across an XY grid, acquires waveforms at each position, computes collected charge in real time.
- **Output**: Live 2D heatmap of charge collection across the sensor surface.

### `TCTFocusScanSequence`
- **Purpose**: 2D focus scan (one XY axis + Z axis).
- **Devices**: Motor stages + oscilloscope + laser
- **Workflow**: Similar to area scan but scans one lateral axis against the vertical (Z) axis to find optimal focus.
- **Output**: Live 2D heatmap of charge vs. position and focus.

### `AutoAlignSequence`
- **Purpose**: Automatically align laser to the sensor pad center.
- **Devices**: Motor stages + oscilloscope + laser
- **Workflow**: Performs a broad XY scan to find the metal opening, then a fine scan to locate the maximum charge collection point. Moves motors to the optimal position.
- **Output**: Console log of alignment progress. Motors positioned at the center of the sensor opening.

### `TCTAnalysisSequence`
- **Purpose**: Batch post-measurement analysis of TCT data.
- **Workflow**: Iterates over all `.npz` files in a directory, runs the full `TCTAnalysis` pipeline (convert to current, discard outliers, average, find integration parameters, integrate, histogram fit), stores results in a CSV summary file, and plots CCE vs. voltage.


# TCT Analysis Engine (`DAQ/AXIOM/Utils/TCTAnalysis.py`)

The `TCTAnalysis` class performs offline waveform analysis. The processing pipeline is:

```
1. get_data()                    Load waveform array + metadata from .npz file
        │
2. convert_to_current()          Scale voltage waveforms to mV
        │
3. discard_waveforms()           Remove outliers (peaks outside ±N% of median amplitude)
        │
4. average_waveform()            Compute the mean waveform (for pedestal/window finding)
        │
5. find_integration_paramaters() Find pedestal level and integration window boundaries
        │
6. integrate_waveforms()         Integrate each waveform individually (trapezoidal rule,
        │                        subtract pedestal area) → charge array
7. plot_histogram()              Fit Gaussian to charge distribution → mu (CCE2), sigma
        │
8. store_in_csv()                Write summary CSV: Voltage, Ileak, CCE, CCE2, MPV,
                                 Noise, Error_mu, Error_mean
```

**Key outputs per voltage point:**
- **CCE** — Mean of integrated charge values (from `integrate_waveforms`)
- **CCE2** — Gaussian fit mu of the charge distribution (from `plot_histogram`)
- **MPV** — Mean peak amplitude of accepted waveforms
- **Noise** — Standard deviation of the pedestal region


# Temperature and Environment Control

## `EnvironmentControl` (`Utils/EnvironmentControl.py`)

Central coordinator that runs in a dedicated `QThread` on a **2-second timer loop**. On each tick, it:

1. Reads all sensor data:
   - **Chiller**: Internal temperature and setpoint (`ChillerCC505`, COM6)
   - **PT1000**: DUT-proximal temperature (`Pt1000`, GPIB 16 via Keithley 2001)
   - **Arduino**: PCB temperature, housing temperature, sensor box temperature, two humidity values (`ArduinoControl`, COM7)
   - **Air flow**: Setpoint and measured flow rate (`AirFluxControl`, COM8 via Sensirion SFX6xxx)
2. Runs **PID control** on the Peltier elements to maintain the target PCB temperature.
3. Updates the **live temperature/humidity plots** (`TempHumPlot`).
4. Logs all values to **InfluxDB** for Grafana monitoring (`ParticularsMonitor`).
5. Optionally writes a **temperature log CSV** during active measurements.

## Device Breakdown

| Class | Instrument | Connection | Purpose |
|-------|-----------|-----------|---------|
| `ChillerCC505` | Huber CC505 Chiller | Serial (COM6) | Ethanol cooling loop: start/stop, setpoint, internal temp readout |
| `Pt1000` | PT1000 sensor (via Keithley 2001) | GPIB 16 | High-precision temperature near the DUT |
| `ArduinoControl` | Arduino + sensors | Serial (COM7) | PCB temperature, housing/sensorbox temperatures, two humidity sensors |
| `PeltierElements` | 4x Peltier + TSX3510P PSU | GPIB 6 | PID-controlled heating/cooling. Fixed voltage (12 V), current regulated by PID loop |
| `AirFluxControl` | Sensirion SFX6xxx flow sensor | Serial (COM8) | Dry air flow monitoring and setpoint control |

## PID Control

The `PeltierElements` class implements a discrete PID controller. Parameters are stored in `measurement_config.json`:
- **Kp** = 1, **Ki** = 0.01, **Kd** = 50
- **I-term limit** = 5 A (prevents integrator windup)
- **Max current** = 5 A, **Max voltage** = 12 V
- **Target temperature** = -18.1 degC (default)
- **Chiller setpoint** = -30.0 degC

Safety interlocks prevent the Peltier from activating if the chiller temperature is above -10 degC or the PCB temperature is above 15 degC.


# GUI Panel Hierarchy

## Temperature Control Panel (left sidebar)
`GUI_temp_IV_CV/TemperatureControlPanel.py` — Displays chiller/Peltier controls, temperature setpoints, measurement directory selector, status indicators for all connected devices, switchbox manual controls, and a CSV sync button.

## IV/CV Panel
`GUI_temp_IV_CV/IVCVPanel.py` — Reused for both IV and CV tabs (parameterized by `measurement_type`). Contains voltage ramp settings (`VoltageSettings` widget), instrument parameter inputs (compliance, delay, sample count, ramping speed), start/abort buttons, live plot canvas, and status indicators.

## TCT Panel
`GUI_TCT/TCTPanel.py` — Container with its own sub-tab widget:

| Sub-tab | Panel Class | Purpose |
|---------|------------|---------|
| **Main** | `TCTMainTabPanel` | Sensor name, temperature, additional text, file naming, start/abort measurement, connect/disconnect TCT devices, measurement chaining checkboxes |
| **Laser** | `LaserPanel` | Laser pulse control (`LaserPulseControl`), motor stage control (`LaserStageControl`), pulse width configuration (`LaserPulseWidth`) |
| **Oscilloscope** | `OscilloscopePanel` | Connect/disconnect oscilloscope (standard or HSI), save/recall setup files |
| **Voltage Source** | `TCTVoltageSourcePanel` | Voltage ramp settings, compliance, delay, ramping speed |
| **Manual Control** | `ManualControlPanel` | Set bias to 0/-6/-600 V, toggle oscilloscope, live current/voltage display |
| **Analysis** | `AnalysisPanel` | Select directory, set analysis parameters, run `TCTAnalysisSequence` |
| **Auto-Align** | `AutoAlignPanel` | Configure broad/fine scan parameters, run `AutoAlignSequence` |
| **Top TCT Scan** | `TopTCTScanPanel` | Configure and run area scans (`TCTAreaScanSequence`) and focus scans (`TCTFocusScanSequence`) |


# Plotting Utilities (`DAQ/AXIOM/Utils/Plot/`)

| Class | File | Purpose |
|-------|------|---------|
| `IVCVPlot` | `IVCVPlot.py` | Live matplotlib canvas for IV curves (I vs V) and CV curves (C vs V, 1/C^2 vs V) |
| `TCTPlot` | `TCTPlot.py` | Live matplotlib canvas for TCT waveforms and CCE vs. voltage |
| `TempHumPlot` | `TempHumPlot.py` | Dual-axis live plot: 7 temperature lines + 2 humidity lines, continuously updated every 2 seconds |


# Threading Model

The application uses Qt's `QThread` + `moveToThread()` pattern for all long-running operations:

```
Main Thread (GUI)
│
├── temperature_thread (QThread)
│       └── EnvironmentControl.main_loop()     [2-second QTimer]
│
├── measurement_thread (QThread)               [created per IV/CV measurement]
│       └── MeasurementSequenceIV.execute_scan()
│       └── MeasurementSequenceCV.execute_scan()
│
├── TCT_thread (QThread)                       [created per TCT measurement]
│       └── MeasurementSequenceTCT.execute_scan()
│
├── analysis_thread (QThread)                  [created per analysis run]
│       └── TCTAnalysisSequence.run()
│
├── alignment_thread (QThread)                 [created per auto-align]
│       └── AutoAlignSequence.run()
│
└── scan_thread (QThread)                      [created per area/focus scan]
        └── TCTAreaScanSequence.run()
        └── TCTFocusScanSequence.run()
```

**Communication pattern**: Measurement sequences emit a `finished` Signal when done, which is connected to the thread's `quit()` slot and to `MainPanel.finish_measurement()` for cleanup. The GUI passes callback functions (e.g., `measurement_active`, `set_IV_indicator`) to the sequences so they can query abort status and update indicators.


# Switchbox Routing

The setup uses a physical switchbox to route signal paths between measurement types. The switchbox is controlled via `EnvironmentControl.set_switchbox()`:

| Channel | Measurement | HV Path | Signal Path |
|---------|-------------|---------|-------------|
| 1 (default) | TCT | Keithley 2410 (GPIB 7) → HV filter → DUT backside | DUT pad → Bias-T + amplifier → oscilloscope |
| 2 | CV | Keithley 2410 (GPIB 4) → decoupling box → DUT backside | DUT pad → decoupling box → LCR meter |
| 3 | IV | Keithley 2410 (GPIB 4, rear) → DUT backside | DUT pad → 50 Ohm termination (current measured by picoammeter in HV line) |

After each IV or CV measurement finishes, the switchbox automatically resets to channel 1 (TCT).


# Data Flow and File Organization

## Directory Structure on Disk

Measurement results are organized under the selected campaign directory:

```
<campaign_directory>/           (e.g., low_fluence_neutrons_2025/)
├── IVCV_onPCB/
│   └── <sensor_name>/
│       ├── <sensor>_<annealing>_IV.csv
│       ├── <sensor>_<annealing>_CV.csv
│       └── <sensor>_<annealing>_IV_temperature.csv
│
├── TCT/
│   └── <sensor_name>/
│       └── <sensor>_<temp>_<date>_<annealing>/
│           ├── <voltage_1>.npz
│           ├── <voltage_2>.npz
│           ├── ...
│           └── <folder_name>.csv          (analysis summary)
│
├── _IV_ALL_CSV/                (aggregated IV files)
├── _CV_ALL_CSV/                (aggregated CV files)
└── _TCT_ALL_CSV/               (aggregated TCT CSV files)
```

## Data Formats

| Measurement | Format | Contents |
|-------------|--------|----------|
| **IV** | `.csv` | Columns: Voltage, Current, timestamp |
| **CV** | `.csv` | Columns: Voltage, Cp, Cs, Dissipation, 1/C^2, Leakage current |
| **TCT waveforms** | `.npz` (compressed NumPy) | Array shape `[num_wf, 2, points_per_wf]` + metadata header array (26 fields: sensor info, voltage, current, timestamps, user) |
| **TCT analysis** | `.csv` | Columns: Num, Voltage, Ileak, CCE, CCE2, MPV, Noise, Error_mu, Error_mean |
| **Temperature log** | `_temperature.csv` | Timestamped temperature and humidity readings during measurements |

## Data Sync Pipeline

On application close (or manually via button), `MainPanel` runs:

```
copy_and_sync_to_git_all_csv_files()
    │
    ├── copy_IVCV_csv_files()        Walks campaign dirs, copies IV/CV CSVs
    │       │                         to _IV_ALL_CSV, _CV_ALL_CSV, and to
    │       │                         particulars-analysis Git repo
    │       └── Filters by valid annealing units (noadd, min, days, d)
    │
    ├── copy_TCT_csv_files()         Walks TCT dirs, copies analysis CSVs
    │       └── to _TCT_ALL_CSV and particulars-analysis Git repo
    │
    └── git_pull_push_sync_Git_Particulars_Analysis()
            └── git pull → git add Data/* → git commit → git push
```


# External / Third-Party Software

The repository also bundles standalone software from Particulars that is **not** part of the Python DAQ:

| Directory | Description | Technology |
|-----------|-------------|-----------|
| `Devices/Laser/LaserPos/ximc/` | Standa XIMC motor control library | C headers + platform-specific DLLs |
| `Devices/Laser/LaserSettings/include/` | Laser control DLLs (`LaserLibrary.dll`, `hidapi.dll`, `USBM3.dll`) | C DLLs |


# Key Dependencies

From `requirements.txt`, the main libraries used are:

| Package | Version | Purpose |
|---------|---------|---------|
| `PySide6` | 6.7.2 | Qt GUI framework |
| `PyVISA` | 1.14.1 | GPIB/VISA instrument communication |
| `pyserial` | 3.5 | Serial port communication (chiller, Arduino, air flow) |
| `numpy` | 1.26.4 | Numerical arrays, waveform data |
| `scipy` | 1.14.0 | Statistical analysis (Gaussian fitting) |
| `matplotlib` | 3.9.1 | Live and offline plotting |
| `pandas` | 2.2.2 | Data analysis and CSV handling |
| `TekHSI` | 1.0.0 | Tektronix High-Speed Interface for oscilloscope |
| `grpcio` | 1.74.0 | gRPC transport for TekHSI |
| `influxdb` | 5.3.2 | InfluxDB client for Grafana monitoring |
| `GitPython` | 3.1.44 | Git operations for data sync |
| `msl-loadlib` | 0.10.0 | 32-bit DLL loading from 64-bit Python (laser control) |
| `sensirion-*` | various | Sensirion air flow sensor drivers |


# Naming Conventions

## Sensor and File Naming

When a user presses **Apply** in the GUI, the following naming pattern is applied:

- **IV filename**: `<sensor_name>_<annealing_step>_IV.csv`
- **CV filename**: `<sensor_name>_<annealing_step>_CV.csv`
- **TCT directory**: `<sensor_name>_<temperature>_<YYMMDD>_<fluence>_<annealing_step>`

Valid annealing units: `noadd`, `min`, `days`, `d`. The software validates these and warns on mismatch.

## Campaign Directories

The software validates that the selected campaign directory is one of:

- `High_Fluence_neutrons_2023`
- `low_fluence_neutrons_2025`
- `Double_Irr_Neutron`
- `Proton_Campaign`
- `300um_UIRAD_Reference` (reference diode measurements)
