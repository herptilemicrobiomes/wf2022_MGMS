"""Export the spectra for a sirius_targets_<mode>.csv target list from the
gap-filled feature MGF (gnps2-ad67978e-bagel), keyed on SCANS == feature_id.

Validates and drops (reporting each): missing block for a requested feature_id,
CHARGE tag not "1+", PEPMASS<=0, or no peak with intensity>0 -- mirrors the
Bd_massspec/Rhodotorula export_*_mgf.py drop criteria.
"""

from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path

import pandas as pd

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]

sys.path.insert(0, str(REPO_ROOT / "analysis" / "_lib"))
from register_value import register_value  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "raw" / "gnps2_ad67978e_bagel"
SOURCE_MGF_GZ = RAW_DIR / "nf_output" / "feature_finding" / "aligned_features_filled.mgf.gz"
EXPECTED_CHARGE_TAG = "1+"


def parse_mgf_blocks(path: Path) -> dict[int, list[str]]:
    blocks: dict[int, list[str]] = {}
    current: list[str] = []
    scan_id: int | None = None
    with gzip.open(path, "rt") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            if stripped == "BEGIN IONS":
                current = [stripped]
                scan_id = None
                continue
            current.append(stripped)
            if stripped.startswith("SCANS="):
                scan_id = int(stripped.split("=", 1)[1])
            if stripped == "END IONS":
                if scan_id is None:
                    raise ValueError("MGF block ended without a SCANS= tag")
                if scan_id in blocks:
                    raise ValueError(f"duplicate SCANS={scan_id} block in source MGF")
                blocks[scan_id] = current
    return blocks


def block_is_valid(block: list[str]) -> tuple[bool, str]:
    charge_tag = next((l.split("=", 1)[1] for l in block if l.startswith("CHARGE=")), None)
    if charge_tag != EXPECTED_CHARGE_TAG:
        return False, f"CHARGE={charge_tag!r} != {EXPECTED_CHARGE_TAG!r}"
    pepmass_tag = next((l.split("=", 1)[1] for l in block if l.startswith("PEPMASS=")), None)
    if pepmass_tag is None or float(pepmass_tag) <= 0:
        return False, f"PEPMASS={pepmass_tag!r} <= 0 or missing"
    has_peak = any(
        (not l.startswith(("BEGIN", "END", "TITLE", "FEATURE_ID", "SOURCE_", "PEPMASS", "CHARGE", "MSLEVEL", "SEQ", "RTINSECONDS", "COLLISION_ENERGY", "SCANS")))
        and l.strip()
        and float(l.split()[1]) > 0
        for l in block
        if len(l.split()) == 2
    )
    if not has_peak:
        return False, "no peak with intensity > 0"
    return True, ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["interesting", "full"], required=True)
    args = parser.parse_args()

    targets_path = ANALYSIS_ROOT / f"sirius_targets_{args.mode}.csv"
    if not targets_path.exists():
        raise FileNotFoundError(f"{targets_path} not found -- run select_targets.py --mode {args.mode} first")
    targets = pd.read_csv(targets_path)
    target_ids = targets["feature_id"].tolist()

    all_blocks = parse_mgf_blocks(SOURCE_MGF_GZ)

    kept: list[str] = []
    dropped: list[tuple[int, str]] = []
    for fid in target_ids:
        block = all_blocks.get(fid)
        if block is None:
            dropped.append((fid, "no MGF block for this feature_id"))
            continue
        ok, reason = block_is_valid(block)
        if not ok:
            dropped.append((fid, reason))
            continue
        kept.extend(block)

    out_mgf = ANALYSIS_ROOT / f"sirius_targets_{args.mode}.mgf"
    out_mgf.write_text("\n".join(kept) + ("\n" if kept else ""))

    for fid, reason in dropped:
        print(f"DROPPED feature_id={fid}: {reason}")

    register_value(f"sirius_n_exported_{args.mode}", len(target_ids) - len(dropped), provenance="scripts/export_targets_mgf.py")
    register_value(f"sirius_n_dropped_{args.mode}", len(dropped), provenance="scripts/export_targets_mgf.py")
    print(f"Exported {len(target_ids) - len(dropped)}/{len(target_ids)} spectra -> {out_mgf} ({len(dropped)} dropped)")


if __name__ == "__main__":
    main()
