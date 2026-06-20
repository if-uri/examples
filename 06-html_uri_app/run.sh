#!/usr/bin/env sh
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

set -eu

DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python3 "$DIR/backend.py"
