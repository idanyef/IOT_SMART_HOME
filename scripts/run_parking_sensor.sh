#!/usr/bin/env bash
# Usage: ./scripts/run_parking_sensor.sh <spotId>
SID=${1:-1}
python3 parking_sensor_emulator.py "$SID"
