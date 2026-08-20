#!/bin/bash
#SBATCH --job-name=sirius-herptile-full
#SBATCH --partition=short
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/sirius_array_%A_%a.log
#SBATCH --array=0-0%1
#
# One shard per array task, %1 = strictly serial (only one task runs at a
# time). This is NOT for parallel speedup -- SIRIUS itself can only run one
# process project-wide at a time (shared login token; see
# scripts/run_sirius_shard.sh and the 2026-08-20 decisions.md entry). The
# array's only purpose here is per-shard checkpointing/resumability: a failed
# or killed job can be resubmitted and will skip already-completed shards
# (run_sirius_shard.sh's ".sirius exists" check).
#
# Set --array=0-$((N_SHARDS-1))%1 to match the actual shard count from
# shard_mgf.py before submitting (this file's default array=0-0 is a
# placeholder that must be edited or overridden with sbatch --array=...).
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"  # the directory `sbatch` was invoked from -- must be analysis/sirius_annotation/

SHARD_DIR="${1:?usage: sbatch --array=0-N%1 run_sirius_array.sbatch <shard_dir> <results_dir>}"
RESULTS_DIR="${2:?usage: sbatch --array=0-N%1 run_sirius_array.sbatch <shard_dir> <results_dir>}"

mkdir -p "$RESULTS_DIR" logs

shard=$(printf "%s/shard_%03d.mgf" "$SHARD_DIR" "$SLURM_ARRAY_TASK_ID")
name="shard_$(printf "%03d" "$SLURM_ARRAY_TASK_ID")"

bash scripts/run_sirius_shard.sh "$shard" "$RESULTS_DIR/$name"
