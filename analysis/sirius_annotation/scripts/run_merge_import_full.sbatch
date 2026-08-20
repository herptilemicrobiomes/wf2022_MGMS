#!/bin/bash
#SBATCH --job-name=sirius-herptile-full-merge
#SBATCH --partition=short
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/sirius_full_merge_%j.log
#
# Runs automatically after the full-run array job (submitted with
# --dependency=afterok:<array_jobid>) completes ALL its tasks successfully.
# Merges the 177 shard outputs and imports them into sirius_annotations.tsv
# so the whole full-set SIRIUS run finishes unattended, without requiring an
# interactive Claude Code session to still be running.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"

python3 scripts/merge_sirius_shards.py --shard-root sirius_results_full --out-dir sirius_results_full/merged
python3 scripts/import_sirius_annotations.py --merged-dir sirius_results_full/merged --label "full_$(date +%F)"

echo "MERGE_IMPORT_DONE $(date -Iseconds)" > FULL_RUN_COMPLETE.marker
echo "Full-run merge+import complete. sirius_annotations.tsv updated."
