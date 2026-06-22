#!/usr/bin/env bash
# Pretend this is your EXISTING shell job — a cron script, a backup, a report.
# A third runtime, adopted under the same shop:// surface via a shell-template.
set -euo pipefail
DATE="${1:-today}"
printf '{"date":"%s","orders":12,"revenue":2480.50}\n' "$DATE"
