# SmartParking (Mac + VS Code)

## Prereqs
- Python 3.9+
- MQTT broker running locally (e.g., Mosquitto on 127.0.0.1:1883)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup_db.py
```

## Run (separate terminals)
```bash
# terminal 1
python manager_parking.py

# terminal 2
python gate_relay_emulator.py 1

# terminal 3
python parking_sensor_emulator.py 1 3

# terminal 4
python payment_button_emulator.py 1

# terminal 5 (GUI)
python gui_parking.py
```

Or use the scripts in `scripts/` (first make them executable):
```bash
chmod +x scripts/*.sh
scripts/start_all.sh
```

## VS Code
Launch configs provided under `.vscode/launch.json` to run components with the debugger.
