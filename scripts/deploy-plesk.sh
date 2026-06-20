#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

# Build the static examples site and publish it to examples.ifuri.com (Plesk).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="${IFURI_DEPLOY_HOST:-ifuri@ifuri.com}"
DOCROOT="${IFURI_EXAMPLES_DOCROOT:-/var/www/vhosts/ifuri.com/examples.ifuri.com}"
OUT="${ROOT}/_site"

echo "== build static site =="
python3 "${ROOT}/scripts/build_site.py" "${OUT}"

echo "== deploy ${OUT} -> ${REMOTE}:${DOCROOT} =="
rsync -az --delete "${OUT}/" "${REMOTE}:${DOCROOT}/"
ssh "${REMOTE}" "cd '${DOCROOT}' && find . -type d -exec chmod 755 {} + && find . -type f -exec chmod 644 {} +"

echo "== verify =="
curl -fsSI "https://examples.ifuri.com/" | head -3 || true
echo "done"
