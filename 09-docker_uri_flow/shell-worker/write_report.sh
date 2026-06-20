#!/usr/bin/env sh
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

set -eu

slug="$1"
text="$2"
path="${REPORT_DIR:-/data}/${slug}.txt"

printf 'report=%s\n' "$text" > "$path"
printf '%s\n' "$path"
