#!/bin/bash
#SBATCH --job-name=sirius-herptile
#SBATCH --partition=stajichlab
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/sirius_serial_%j.log
#
# Runs all shards in $SHARD_DIR sequentially in one job -- for a small target
# set (e.g. the "interesting" feeding-emergent features) where an array job's
# per-task scheduling overhead isn't worth it. Modeled on Rhodotorula's
# run_sirius_container_serial_full.sbatch. Only ONE sirius process may run
# project-wide at a time (shared login token) -- do not run this concurrently
# with any other sbatch/array job that also calls run_sirius_shard.sh, in
# this project or a sibling project.
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"  # the directory `sbatch` was invoked from -- must be analysis/sirius_annotation/

SHARD_DIR="${1:?usage: sbatch run_sirius_serial.sbatch <shard_dir> <results_dir>}"
RESULTS_DIR="${2:?usage: sbatch run_sirius_serial.sbatch <shard_dir> <results_dir>}"

mkdir -p "$RESULTS_DIR" logs

for shard in "$SHARD_DIR"/shard_*.mgf; do
    name="$(basename "$shard" .mgf)"
    bash scripts/run_sirius_shard.sh "$shard" "$RESULTS_DIR/$name"
done

echo "All shards in $SHARD_DIR complete."
