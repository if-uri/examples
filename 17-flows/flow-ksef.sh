#!/usr/bin/env bash
# Scenario 5: KSeF challenge + send, as a dry-run flow (no live call, no secret).
set -euo pipefail
cd "$(dirname "$0")"
make -s setup
python3 run_flow.py ksef-send.flow.yaml   # dry-run: shows the plan, resolves nothing
