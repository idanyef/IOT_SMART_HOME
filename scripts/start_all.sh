#!/usr/bin/env bash
# Start everything in background tabs (within one terminal use &)
python3 parking_sensor_emulator.py 1 3 &
python3 parking_sensor_emulator.py 2 4 &
python3 parking_sensor_emulator.py 3 5 &
python3 payment_button_emulator.py 1 &
python3 payment_button_emulator.py 2 &
python3 payment_button_emulator.py 3 &
python3 gate_relay_emulator.py 1 &
python3 manager_parking.py &
python3 gui_parking.py &
wait
