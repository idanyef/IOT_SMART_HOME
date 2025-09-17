#!/usr/bin/env bash
# Kills all SmartParking processes safely
pkill -f parking_sensor_emulator.py || true
pkill -f payment_button_emulator.py || true
pkill -f gate_relay_emulator.py    || true
pkill -f gui_parking.py            || true
pkill -f manager_parking.py        || true
echo "🛑 Stopped all SmartParking processes."




