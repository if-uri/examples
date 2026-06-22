#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./run_prompt.sh 'crm: utwórz lead "Acme z promptu NL"'
./run_prompt.sh 'support: zgłoszenie "Nie działa lokalny worker"'
./run_prompt.sh 'shop: zamów produkt "URI Test Subscription" qty 3'
./run_prompt.sh 'docs: dokument "Notatka z testu lokalnej autonomii"'
