#!/usr/bin/env bash
# Scenario 2: is example.com up, read its DOM in real Chrome, log it.
set -euo pipefail
cd "$(dirname "$0")"
make -s setup
python3 run_flow.py web-recon.flow.yaml --execute \
  --allow 'httpcheck://*' --allow 'browser://*' --allow 'log://*'
