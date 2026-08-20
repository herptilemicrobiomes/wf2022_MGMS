#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/01_pcoa.py
python3 scripts/02_age_variable_correlation.py
echo "Analysis complete. Outputs in outputs/"
