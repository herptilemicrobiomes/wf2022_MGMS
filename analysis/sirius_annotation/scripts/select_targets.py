"""Select SIRIUS annotation targets for gnps2-ad67978e-bagel, in one of two modes:

  --mode interesting : the feeding-emergent-features candidates + pattern leads
                        (a small, explicit feature-id list)
  --mode full         : every feature with has_ms2==True and charge==1 in
                        aligned_features.csv, minus anything already annotated
                        (modeled on Bd_massspec's select_native_targets.py)

Writes <analysis_root>/sirius_targets_<mode>.csv (feature_id, mz, rt, source_file,
source_scan) for export_targets_mgf.py to consume.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]

sys.path.insert(0, str(REPO_ROOT / "analysis" / "_lib"))
from register_value import register_value  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "raw" / "gnps2_ad67978e_bagel"
FEATURES_PATH = RAW_DIR / "nf_output" / "feature_finding" / "feature_finding_results" / "aligned_features.csv.gz"
FEEDING_EMERGENT_DIR = REPO_ROOT / "analysis" / "feeding-emergent-features" / "outputs"

REQUIRED_CHARGE = 1  # SIRIUS formula/fingerprint/CSI:FingerID assume a known, singly-charged
# precursor in this pipeline (matches the Bd_massspec/Rhodotorula convention) -- multiply charged
# features are excluded rather than guessed at.


def load_feature_table() -> pd.DataFrame:
    df = pd.read_csv(FEATURES_PATH, compression="gzip")
    if df.shape[0] != 12566:
        raise ValueError(f"expected 12566 features, got {df.shape[0]}")
    return df.rename(columns={"row ID": "feature_id", "row m/z": "mz", "row retention time": "rt"})


def already_annotated_ids(annotations_path: Path) -> set[int]:
    if not annotations_path.exists():
        return set()
    prior = pd.read_csv(annotations_path, sep="\t")
    return set(prior["feature_id"].tolist())


def select_interesting(df: pd.DataFrame) -> pd.DataFrame:
    candidates_path = FEEDING_EMERGENT_DIR / "feeding_emergent_candidates.csv"
    leads_path = FEEDING_EMERGENT_DIR / "feeding_emergent_pattern_leads.csv"
    if not candidates_path.exists() or not leads_path.exists():
        raise FileNotFoundError(
            f"expected feeding-emergent-features outputs at {candidates_path} and {leads_path}; "
            "run analysis/feeding-emergent-features/run.sh first"
        )
    candidates = pd.read_csv(candidates_path)
    leads = pd.read_csv(leads_path)
    ids = sorted(set(candidates["feature_id"]) | set(leads["feature_id"]))
    targets = df[df["feature_id"].isin(ids)].copy()
    if targets.shape[0] != len(ids):
        missing = set(ids) - set(targets["feature_id"])
        raise ValueError(f"feature ids from feeding-emergent-features not found in feature table: {missing}")
    return targets


def select_full(df: pd.DataFrame, max_features: int) -> pd.DataFrame:
    targets = df[(df["has_ms2"] == True) & (df["charge"] == REQUIRED_CHARGE)].copy()  # noqa: E712
    if max_features > 0:
        targets = targets.sample(n=min(max_features, targets.shape[0]), random_state=1234)
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["interesting", "full"], required=True)
    parser.add_argument(
        "--max-features",
        type=int,
        default=0,
        help="For --mode full: cap the target count with a reproducible random subsample (0 = no cap, full run).",
    )
    parser.add_argument(
        "--skip-annotated",
        action="store_true",
        help="Exclude feature ids already present in sirius_annotations.tsv.",
    )
    args = parser.parse_args()

    df = load_feature_table()

    if args.mode == "interesting":
        targets = select_interesting(df)
    else:
        targets = select_full(df, args.max_features)

    if args.skip_annotated:
        prior_ids = already_annotated_ids(ANALYSIS_ROOT / "sirius_annotations.tsv")
        n_before = targets.shape[0]
        targets = targets[~targets["feature_id"].isin(prior_ids)]
        print(f"Excluded {n_before - targets.shape[0]} already-annotated features")

    out_cols = ["feature_id", "mz", "rt", "source_file", "source_scan"]
    missing_cols = [c for c in out_cols if c not in targets.columns]
    if missing_cols:
        raise ValueError(f"feature table missing expected columns: {missing_cols}")

    out_path = ANALYSIS_ROOT / f"sirius_targets_{args.mode}.csv"
    targets[out_cols].to_csv(out_path, index=False)

    register_value(f"sirius_n_targets_{args.mode}", int(targets.shape[0]), provenance="scripts/select_targets.py")
    print(f"Selected {targets.shape[0]} targets ({args.mode}) -> {out_path}")


if __name__ == "__main__":
    main()
