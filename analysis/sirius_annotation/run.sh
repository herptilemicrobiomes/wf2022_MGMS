#!/bin/bash
# Local prep steps only (target selection, MGF export, sharding) -- these are
# fast and safe to rerun. Submitting the actual SIRIUS SLURM job and running
# merge/import afterwards are separate manual steps (see SIRIUS_ANNOTATION.md
# "Reproducibility"), because SIRIUS may only run one process project-wide at
# a time and a real run takes minutes (interesting) to ~a day (full) of
# cluster wall-clock -- not something to fire off unattended from here.
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:?usage: run.sh <interesting|full>}"

python3 scripts/select_targets.py --mode "$MODE"
python3 scripts/export_targets_mgf.py --mode "$MODE"
python3 scripts/shard_mgf.py "sirius_targets_${MODE}.mgf" --out-dir "shards_${MODE}" --spectra-per-shard 20

echo "Prep complete for mode=$MODE. Next: submit the SIRIUS SLURM job (see SIRIUS_ANNOTATION.md), then run merge_sirius_shards.py and import_sirius_annotations.py."
