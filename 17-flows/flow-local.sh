#!/usr/bin/env bash
# Scenario 1 (offline): timestamp + audit log, run as a YAML flow.
set -euo pipefail
cd "$(dirname "$0")"
make -s setup
python3 run_flow.py local.flow.yaml --execute --allow 'time://*' --allow 'log://*'
