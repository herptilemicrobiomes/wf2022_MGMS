#!/bin/bash
# Run the SIRIUS 6.3.12 container on one shard MGF.
# Usage: run_sirius_shard.sh <shard.mgf> <output_project_dir>
#
# Command chain order (formula -> fingerprint -> canopus -> structures ->
# write-summaries) is load-bearing for SIRIUS 6.x. ZODIAC is deliberately
# excluded (it's a dataset-wide tool; sharding would change its results).
# -XX:AOTMode=off works around a SIGILL on some AMD EPYC nodes with SIRIUS's
# prebuilt AOT cache.
set -euo pipefail

SHARD="$1"
OUT_DIR="$2"
SIF="${SIRIUS_SIF:-/bigdata/stajichlab/shared/singularity/sirius-6.3.12-linux-x64.sif}"
SIRIUS_HEAP_GB="${SIRIUS_HEAP_GB:-12}"

if [ -d "${OUT_DIR}.sirius" ]; then
    echo "SKIP: ${OUT_DIR}.sirius already exists (resume checkpoint) -- delete it to force a rerun"
    exit 0
fi

mkdir -p "$(dirname "$OUT_DIR")"

module load singularity

echo "sirius login check:"
singularity exec --bind /bigdata,/scratch "$SIF" sirius login --show

JAVA_OPTS="-Xmx${SIRIUS_HEAP_GB}G -XX:AOTMode=off" singularity exec --bind /bigdata,/scratch "$SIF" \
    sirius --cores "${SLURM_CPUS_PER_TASK:-4}" \
    --input "$SHARD" --output "$OUT_DIR" \
    formula --ppm-max 15 --ppm-max-ms2 15 --candidates 10 \
    fingerprint \
    canopus \
    structures \
    write-summaries

echo "DONE: $SHARD -> $OUT_DIR"
