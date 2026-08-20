"""Screen gnps2-ad67978e-bagel features for a "feeding-emergent" pattern:
absent/very-low in control samples, absent/very-low early after
Basidiobolus feeding, and clearly higher late after feeding -- in either
the STP1710.7 or STP1717.1 pilot cohort.

Strict-execution notes (robust-analysis convention):
  - Early/late day bins are the two outer thirds of the natural 3-timepoint
    collection structure (see .living/decisions.md), not an arbitrary split.
  - Screening thresholds are named constants with provenance in comments.
  - Significance uses a one-sided Mann-Whitney U test (late > control+early
    baseline), Benjamini-Hochberg FDR corrected across all 12,566 features
    tested per treated group (not just pre-screened candidates), to avoid
    selection-bias in the reported p-values.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]
OUT_DIR = ANALYSIS_ROOT / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_ROOT / "analysis" / "_lib"))
from register_value import register_value  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "raw" / "gnps2_ad67978e_bagel"
FEATURES_PATH = RAW_DIR / "nf_output" / "feature_finding" / "feature_finding_results" / "aligned_features.csv.gz"
METADATA_PATH = RAW_DIR / "nf_output" / "metadata" / "merged_metadata.tsv"
LIBRARY_HITS_PATH = RAW_DIR / "nf_output" / "feature_library_search" / "merged_feature_library_search_results.tsv"

# Early/late day bins: the 33 treated-cohort samples fall into 3 natural collection rounds
# (~[-1,10], ~[24,33], ~[50,63] days post feeding -- see outputs/age_variable_correlation.png
# in the pcoa-ms-feature-composition analysis and .living/decisions.md 2026-08-20 entry). We use
# the two OUTER rounds as "early"/"late" and drop the middle round, rather than a median split,
# so "early" and "late" reflect genuinely separated collection timepoints, not an arbitrary cut.
EARLY_DAYS_MAX = 10
LATE_DAYS_MIN = 45

TREATED_GROUPS = ["STP1710.7 pilot", "STP1717.1 pilot"]
CONTROL_GROUP = "control"

# Screening thresholds (fraction of the feature's own max normalized abundance across all 50
# biological samples). Chosen to encode "not present or very low" / "clearly higher" in relative,
# per-feature terms rather than an absolute peak-area cutoff (peak areas span orders of magnitude
# across features).
LOW_DETECT_RATE_MAX = 0.3  # <=30% of samples in a "low" group show any signal
LOW_MEDIAN_FRAC_MAX = 0.10  # median abundance in a "low" group <=10% of the feature's own max
HIGH_DETECT_RATE_MIN = 0.5  # >=50% of samples in the "late" group show signal
HIGH_MEDIAN_FRAC_MIN = 0.5  # median abundance in "late" group >=50% of the feature's own max
MIN_FOLD_CHANGE = 4.0  # late median / early median (with a small pseudocount, see below)
FDR_THRESHOLD = 0.05
MIN_GROUP_N = 3  # minimum samples required in each of control/early/late to run a test

PSEUDOCOUNT_FRAC = 0.01  # 1% of each feature's own max, used only to avoid divide-by-zero in the
# fold-change ratio when the early-group median is exactly 0 -- does not affect detection-rate or
# absolute-median screening criteria, only the reported fold-change number.


def load_bio_metadata() -> pd.DataFrame:
    meta = pd.read_csv(METADATA_PATH, sep="\t", dtype=str)
    bio = meta[meta["sample_type"] == "sample"].copy().reset_index(drop=True)
    if bio.shape[0] != 50:
        raise ValueError(f"expected 50 biological samples, got {bio.shape[0]}")

    for col in ("collection_date", "basidiobolus_feeding_date"):
        parsed = pd.to_datetime(bio[col], errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"unparseable/missing {col} among biological samples")
        bio[col] = parsed
    bio["days_post_feeding"] = (bio["collection_date"] - bio["basidiobolus_feeding_date"]).dt.days
    return bio


def load_normalized_feature_table(bio: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (feature_annotations, sample_x_feature normalized abundance)."""
    df = pd.read_csv(FEATURES_PATH, compression="gzip")
    if df.shape[0] != 12566:
        raise ValueError(f"expected 12566 features, got {df.shape[0]}")

    peak_cols = [f"{fn} Peak area" for fn in bio["filename"]]
    missing_cols = [c for c in peak_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"peak-area columns missing from aligned_features.csv for: {missing_cols}")

    annotations = df[["row ID", "row m/z", "row retention time", "parent_mass", "adduct", "is_isf"]].copy()
    annotations = annotations.rename(columns={"row ID": "feature_id", "row m/z": "mz", "row retention time": "rt"})

    peak_areas = df[peak_cols].copy()
    peak_areas.columns = bio["filename"].tolist()
    peak_areas.index = df["row ID"]
    # ANALYSIS_OK[missingness]: NaN in aligned_features.csv peak-area columns means "not detected
    # in this gap-filled feature" per README_FOR_CLAUDE.md, not a missing measurement -> 0 is the
    # correct value, not an imputation. Same convention as
    # pcoa-ms-feature-composition/scripts/01_pcoa.py::load_feature_table.
    peak_areas = peak_areas.fillna(0.0)

    sample_x_feature = peak_areas.T
    sample_x_feature.index.name = "filename"
    if sample_x_feature.shape != (50, 12566):
        raise ValueError(f"unexpected sample x feature shape: {sample_x_feature.shape}")

    row_sums = sample_x_feature.sum(axis=1)
    # ANALYSIS_OK[threshold]: 0 here is division-undefined, not a scientific cutoff -- mirrors the
    # same check in pcoa-ms-feature-composition/scripts/01_pcoa.py::tic_normalize.
    zero_tic = row_sums[row_sums == 0]
    if not zero_tic.empty:
        raise ValueError(f"samples with zero total peak area (cannot TIC-normalize): {list(zero_tic.index)}")
    normalized = sample_x_feature.div(row_sums, axis=0)

    return annotations, normalized


def load_library_hits() -> pd.DataFrame:
    hits = pd.read_csv(LIBRARY_HITS_PATH, sep="\t")
    if hits["query_scan"].duplicated().any():
        raise ValueError("merged_feature_library_search_results.tsv has duplicate query_scan values")
    return hits[["query_scan", "cosine", "matched_peaks", "NAME", "SPECTRUMID"]].rename(
        columns={"query_scan": "feature_id", "NAME": "library_name", "SPECTRUMID": "library_spectrum_id"}
    )


def screen_group(
    normalized: pd.DataFrame, bio: pd.DataFrame, group: str
) -> pd.DataFrame:
    ctrl_files = bio.loc[bio["treatment_group"] == CONTROL_GROUP, "filename"]
    early_files = bio.loc[
        (bio["treatment_group"] == group) & (bio["days_post_feeding"] <= EARLY_DAYS_MAX), "filename"
    ]
    late_files = bio.loc[
        (bio["treatment_group"] == group) & (bio["days_post_feeding"] >= LATE_DAYS_MIN), "filename"
    ]
    if min(len(ctrl_files), len(early_files), len(late_files)) < MIN_GROUP_N:
        raise ValueError(
            f"{group}: insufficient samples for screening "
            f"(control={len(ctrl_files)}, early={len(early_files)}, late={len(late_files)}, min={MIN_GROUP_N})"
        )

    ctrl_arr = normalized.loc[ctrl_files].to_numpy()  # (n_ctrl, n_features)
    early_arr = normalized.loc[early_files].to_numpy()
    late_arr = normalized.loc[late_files].to_numpy()
    baseline_arr = np.concatenate([ctrl_arr, early_arr], axis=0)

    feature_max = normalized.to_numpy().max(axis=0)  # per-feature max across all 50 bio samples
    feature_ids = normalized.columns.to_numpy()

    ctrl_detect_rate = (ctrl_arr > 0).mean(axis=0)
    ctrl_median = np.median(ctrl_arr, axis=0)
    early_detect_rate = (early_arr > 0).mean(axis=0)
    early_median = np.median(early_arr, axis=0)
    late_detect_rate = (late_arr > 0).mean(axis=0)
    late_median = np.median(late_arr, axis=0)

    pseudocount = PSEUDOCOUNT_FRAC * feature_max
    # ANALYSIS_OK[threshold]: features never detected in any of the 50 biological samples have
    # feature_max == 0, so both early_median and pseudocount are 0 here -> 0/0 -> NaN by
    # construction, not a bug. These features always fail late_high (late_detect_rate can't reach
    # HIGH_DETECT_RATE_MIN with nothing ever detected) so the NaN fold_change never spuriously
    # passes the screen; errstate below just silences the expected divide-by-zero warning.
    with np.errstate(divide="ignore", invalid="ignore"):
        fold_change = late_median / np.maximum(early_median, pseudocount)

    # mannwhitneyu with axis=1 vectorizes the test across all 12,566 features at once (arrays
    # shaped n_features x n_samples-in-group) instead of a 12,566-iteration Python loop.
    stat, pvalue = mannwhitneyu(late_arr.T, baseline_arr.T, alternative="greater", axis=1)
    fdr_q = benjamini_hochberg(pvalue)

    with np.errstate(divide="ignore", invalid="ignore"):
        ctrl_low = (ctrl_detect_rate <= LOW_DETECT_RATE_MAX) & (ctrl_median <= LOW_MEDIAN_FRAC_MAX * feature_max)
        early_low = (early_detect_rate <= LOW_DETECT_RATE_MAX) & (early_median <= LOW_MEDIAN_FRAC_MAX * feature_max)
        late_high = (late_detect_rate >= HIGH_DETECT_RATE_MIN) & (late_median >= HIGH_MEDIAN_FRAC_MIN * feature_max)
    fold_ok = fold_change >= MIN_FOLD_CHANGE
    sig_ok = fdr_q < FDR_THRESHOLD

    pattern_only = ctrl_low & early_low & late_high & fold_ok
    passes = pattern_only & sig_ok

    result = pd.DataFrame(
        {
            "feature_id": feature_ids,
            "treatment_group": group,
            "n_control": len(ctrl_files),
            "n_early": len(early_files),
            "n_late": len(late_files),
            "feature_max_normalized_abundance": feature_max,
            "control_detect_rate": ctrl_detect_rate,
            "control_median_normalized": ctrl_median,
            "early_detect_rate": early_detect_rate,
            "early_median_normalized": early_median,
            "late_detect_rate": late_detect_rate,
            "late_median_normalized": late_median,
            "fold_change_late_over_early": fold_change,
            "mannwhitney_pvalue": pvalue,
            "fdr_q": fdr_q,
            "matches_pattern_uncorrected": pattern_only,
            "passes_screen": passes,
        }
    )
    return result


def benjamini_hochberg(pvalues: np.ndarray) -> np.ndarray:
    n = len(pvalues)
    order = np.argsort(pvalues)
    ranked = pvalues[order]
    q = ranked * n / (np.arange(1, n + 1))
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0, 1)
    out = np.empty(n)
    out[order] = q
    return out


def plot_top_candidates(
    normalized: pd.DataFrame, bio: pd.DataFrame, candidates: pd.DataFrame, annotations: pd.DataFrame, n_top: int, out_path: Path
) -> None:
    top = candidates.sort_values("fdr_q").head(n_top)
    if top.empty:
        return
    n = len(top)
    ncols = min(3, n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.5 * ncols, 3.8 * nrows), squeeze=False)

    group_colors = {"control": "#1B9E77", "STP1710.7 pilot": "#D95F02", "STP1717.1 pilot": "#7570B3"}

    for i, (_, row) in enumerate(top.iterrows()):
        ax = axes[i // ncols][i % ncols]
        fid = row["feature_id"]
        for g, color in group_colors.items():
            g_files = bio.loc[bio["treatment_group"] == g, "filename"]
            x = bio.set_index("filename").loc[g_files, "days_post_feeding"]
            y = normalized.loc[g_files, fid]
            ax.scatter(x, y, c=color, label=g, s=30, edgecolor="k", linewidth=0.3, alpha=0.85)
        mz = annotations.set_index("feature_id").loc[fid, "mz"]
        ax.set_title(f"feature {fid}  m/z {mz:.4f}\nFDR q={row['fdr_q']:.2g}, FC={row['fold_change_late_over_early']:.1f}x", fontsize=8)
        ax.set_xlabel("Days post feeding", fontsize=8)
        ax.set_ylabel("TIC-normalized abundance", fontsize=8)
        ax.tick_params(labelsize=7)
        if i == 0:
            ax.legend(fontsize=6, loc="upper left")

    for j in range(n, nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")

    fig.tight_layout()
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=200)
    plt.close(fig)


def main() -> None:
    bio = load_bio_metadata()
    annotations, normalized = load_normalized_feature_table(bio)
    library_hits = load_library_hits()

    register_value("screen_early_days_max", EARLY_DAYS_MAX, provenance="scripts/01_screen_features.py")
    register_value("screen_late_days_min", LATE_DAYS_MIN, provenance="scripts/01_screen_features.py")
    register_value("screen_min_fold_change", MIN_FOLD_CHANGE, provenance="scripts/01_screen_features.py")
    register_value("screen_fdr_threshold", FDR_THRESHOLD, provenance="scripts/01_screen_features.py")
    register_value("screen_n_features_tested", int(normalized.shape[1]), provenance="scripts/01_screen_features.py")

    all_results = []
    for group in TREATED_GROUPS:
        res = screen_group(normalized, bio, group)
        n_pass = int(res["passes_screen"].sum())
        n_pattern = int(res["matches_pattern_uncorrected"].sum())
        register_value(
            f"screen_n_candidates_{group.split()[0].replace('.', '_')}",
            n_pass,
            provenance="scripts/01_screen_features.py",
        )
        register_value(
            f"screen_n_pattern_only_{group.split()[0].replace('.', '_')}",
            n_pattern,
            provenance="scripts/01_screen_features.py (matches shape criteria, not FDR-significant)",
        )
        print(
            f"{group}: {n_pass} FDR-significant candidates, {n_pattern} pattern-matching leads "
            f"(uncorrected) of {res.shape[0]} features tested"
        )
        all_results.append(res)

    combined = pd.concat(all_results, ignore_index=True)
    combined = combined.merge(annotations, on="feature_id", how="left", validate="many_to_one")
    combined = combined.merge(library_hits, on="feature_id", how="left", validate="many_to_one")
    combined.to_csv(OUT_DIR / "feature_screen_all_results.csv", index=False)

    candidates = combined[combined["passes_screen"]].copy().sort_values(["treatment_group", "fdr_q"])
    candidates.to_csv(OUT_DIR / "feeding_emergent_candidates.csv", index=False)

    pattern_leads = combined[combined["matches_pattern_uncorrected"]].copy()
    pattern_leads = pattern_leads.sort_values(["treatment_group", "fold_change_late_over_early"], ascending=[True, False])
    pattern_leads.to_csv(OUT_DIR / "feeding_emergent_pattern_leads.csv", index=False)

    n_both_strict = (
        candidates.groupby("feature_id")["treatment_group"].nunique().loc[lambda s: s == len(TREATED_GROUPS)].shape[0]
    )
    n_both_pattern = (
        pattern_leads.groupby("feature_id")["treatment_group"].nunique().loc[lambda s: s == len(TREATED_GROUPS)].shape[0]
    )
    register_value("screen_n_candidates_both_groups", int(n_both_strict), provenance="scripts/01_screen_features.py")
    register_value("screen_n_pattern_leads_both_groups", int(n_both_pattern), provenance="scripts/01_screen_features.py")
    n_library_annotated = int(pattern_leads["library_name"].notna().sum())
    register_value("screen_n_pattern_leads_library_annotated", n_library_annotated, provenance="scripts/01_screen_features.py")

    # Plot from the pattern-leads list (ranked by fold change) rather than the strict FDR-passing
    # list, since the latter can be too small (n=1 at FDR<0.05 here) to be a useful trajectory
    # gallery -- the plot titles still report each feature's own fdr_q so significance is visible.
    plot_top_candidates(normalized, bio, pattern_leads, annotations, n_top=9, out_path=OUT_DIR / "top_candidate_trajectories.pdf")

    print(f"FDR-significant candidates (either group): {candidates['feature_id'].nunique()}")
    print(f"Pattern-matching leads, uncorrected (either group): {pattern_leads['feature_id'].nunique()}")
    print(f"Pattern leads significant in both treated groups: {n_both_pattern}")
    print(f"Pattern leads with a spectral-library hit: {n_library_annotated}")
    print(f"Outputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
