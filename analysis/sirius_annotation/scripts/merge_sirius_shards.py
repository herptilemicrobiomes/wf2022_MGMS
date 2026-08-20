"""Concatenate per-shard SIRIUS write-summaries TSVs into one file per table.
Straight concatenation is correct here -- rank columns (formulaRank,
structurePerIdRank, ...) are per-compound, not global across shards.
Ported from the Rhodotorula/Bd_massspec sirius_container_pipeline convention.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SUMMARY_TABLES = [
    "formula_identifications.tsv",
    "structure_identifications.tsv",
    "denovo_structure_identifications.tsv",
    "canopus_formula_summary.tsv",
    "canopus_structure_summary.tsv",
    "spectral_matches.tsv",
    "spectral_matches_analog.tsv",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-root", type=Path, required=True, help="Directory containing shard_NNN/ SIRIUS project dirs")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    # ANALYSIS_OK[file-selection]: not a "pick the latest/best" glob -- shard_NNN/ dirs are
    # exhaustively enumerated (every match is used, none discarded) and shard_mgf.py guarantees
    # deterministic zero-padded names, so sorting just fixes iteration/output order.
    shard_dirs = sorted(p for p in args.shard_root.glob("shard_*") if p.is_dir())
    if not shard_dirs:
        raise FileNotFoundError(f"no shard_* directories found under {args.shard_root}")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for table_name in SUMMARY_TABLES:
        frames = []
        header = None
        for shard_dir in shard_dirs:
            table_path = shard_dir / table_name
            if not table_path.exists():
                continue
            df = pd.read_csv(table_path, sep="\t")
            if header is None:
                header = list(df.columns)
            elif list(df.columns) != header:
                raise ValueError(f"{table_path} has a different header than earlier shards for {table_name}")
            frames.append(df)
        if not frames:
            print(f"SKIP {table_name}: not produced by any shard")
            continue
        merged = pd.concat(frames, ignore_index=True)
        out_path = args.out_dir / table_name
        merged.to_csv(out_path, sep="\t", index=False)
        print(f"{table_name}: {merged.shape[0]} rows from {len(frames)} shards -> {out_path}")


if __name__ == "__main__":
    main()
