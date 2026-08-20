"""Split an MGF into N round-robin shards for a SIRIUS SLURM array job.
Ported from the Rhodotorula/Bd_massspec sirius_container_pipeline convention.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path


def parse_blocks(path: Path) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in path.read_text().splitlines():
        if line == "BEGIN IONS":
            current = [line]
            continue
        current.append(line)
        if line == "END IONS":
            blocks.append(current)
    return blocks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mgf", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--spectra-per-shard", type=int, default=20)
    args = parser.parse_args()

    spectra = parse_blocks(args.mgf)
    if not spectra:
        raise ValueError(f"no BEGIN IONS/END IONS blocks found in {args.mgf}")

    n_shards = math.ceil(len(spectra) / args.spectra_per_shard)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for i in range(n_shards):
        shard_spectra = spectra[i::n_shards]  # round-robin, not contiguous chunks
        shard_path = args.out_dir / f"shard_{i:03d}.mgf"
        with shard_path.open("w") as fh:
            for block in shard_spectra:
                fh.write("\n".join(block) + "\n")
        written += len(shard_spectra)

    if written != len(spectra):
        raise ValueError(f"sharding lost spectra: wrote {written}, expected {len(spectra)}")

    print(f"{len(spectra)} spectra -> {n_shards} shards in {args.out_dir}")


if __name__ == "__main__":
    main()
