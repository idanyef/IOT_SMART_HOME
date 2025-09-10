#!/usr/bin/env bash
# Usage: ./scripts/run_payment_button.sh [spotId]
SPOT=${1:-1}
python3 payment_button_emulator.py "$SPOT"
