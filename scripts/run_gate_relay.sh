#!/usr/bin/env bash
# Usage: ./scripts/run_gate_relay.sh [gateId]
GID=${1:-1}
python3 gate_relay_emulator.py "$GID"
