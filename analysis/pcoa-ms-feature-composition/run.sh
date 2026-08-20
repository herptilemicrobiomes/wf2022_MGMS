#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/01_pcoa.py
echo "Analysis complete. Outputs in outputs/"
