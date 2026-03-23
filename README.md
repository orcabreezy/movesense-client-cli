# Movesense Client Cli

A Python Command Line Interface to interact with Bluetooth Low Energy (BLE) devices specific client implementations for the [ble-ecg firmware](https://github.com/JonasPrimbs/movesense-ble-ecg-firmware)
---

## Prerequisites
- Python 3.14
---

## Setup

### 1) Clone the repository

```bash
git clone git@github.com/orcabreezy/movesense-client
cd movesense-client
```

### 2) Create a virtual environment

```bash
python -m venv .venv
```

### 3) Activate the virtual environment

#### Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```


#### Linux / macOS

```bash
source .venv/bin/activate
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the CLI app

From the project root, run `src/main.py` as a module:

```bash
python -m src.main
```

---

## Usage

The Cli starts by scanning for nearby devices. If your device was not found, try re-scanning. 
When you select your desired device, it will be connected to. Then you can choose to list the devices Gatt-Services and Characteristics or interact with an individual Characteristic by reading, writing binary values or subscribing (notify) to a Characteristic.

### Movesense ble-ecg firmware
If your device is running a valid version of the ble-ecg firmware, you can choose the movesense sub-menu after connecting to the device. The application will auto-detect the version the sensor is running and based on that will show you specific menu items. 

E.g. on version 0.7.0 you can receive Measurements from the Movesenses ECG and IMU sensors and store them in a file (will apper in a data directory) Additionally with version 0.8.0 you can start/stop recordings on the Movesenses internal storage and then later stream the storage contents.
