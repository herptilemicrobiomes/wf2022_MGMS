#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/01_screen_features.py
echo "Analysis complete. Outputs in outputs/"
