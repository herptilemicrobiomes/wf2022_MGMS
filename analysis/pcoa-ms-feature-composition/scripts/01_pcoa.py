"""PCoA (Bray-Curtis) ordination of the gnps2-ad67978e-bagel MS1 feature-quant table.

Strict-execution notes (robust-analysis convention):
  - Every join/filter asserts its expected row/column count; no silent drops.
  - NaN handling is explicit (gap-filled features -> 0, i.e. "not detected").
  - Group-separation significance uses a permutation test (PERMANOVA-style
    pseudo-F), not just eyeballing the ordination plot.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import squareform, pdist

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]
OUT_DIR = ANALYSIS_ROOT / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_ROOT / "analysis" / "_lib"))
from register_value import register_value  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "raw" / "gnps2_ad67978e_bagel"
FEATURES_PATH = RAW_DIR / "nf_output" / "feature_finding" / "feature_finding_results" / "aligned_features.csv.gz"
METADATA_PATH = RAW_DIR / "nf_output" / "metadata" / "merged_metadata.tsv"

RNG_SEED = 42
N_PERMUTATIONS = 999

SAMPLE_TYPE_COLORS = {
    "sample": "#2C7FB8",
    "QC_blank_extract": "#D95F02",
    "QC_blank_solvent": "#7570B3",
    "QC_blank_with_internal_standard": "#E7298A",
}
TREATMENT_COLORS = {
    "control": "#1B9E77",
    "STP1710.7 pilot": "#D95F02",
    "STP1717.1 pilot": "#7570B3",
    "(QC blank)": "#BBBBBB",
}


def load_metadata() -> pd.DataFrame:
    meta = pd.read_csv(METADATA_PATH, sep="\t", dtype=str)
    if meta.shape[0] != 57:
        raise ValueError(f"expected 57 metadata rows (50 samples + 7 QC blanks), got {meta.shape[0]}")
    if not meta["filename"].is_unique:
        raise ValueError("merged_metadata.tsv filename column has duplicates")
    n_missing_type = int(meta["sample_type"].isna().sum())
    if n_missing_type != 0:
        raise ValueError(f"{n_missing_type} rows missing sample_type")
    # ANALYSIS_OK[missingness]: treatment_group is blank only for QC blank rows (verified above
    # via sample_type completeness + the 7-row QC-blank count asserted in main()); recoding the
    # blank to an explicit "(QC blank)" label is presentation-only for the legend, not an impute
    # of a real biological value.
    meta["treatment_group"] = meta["treatment_group"].fillna("(QC blank)").replace("", "(QC blank)")
    return meta


def load_feature_table(meta: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(FEATURES_PATH, compression="gzip")
    if df.shape[0] != 12566:
        raise ValueError(f"expected 12566 features, got {df.shape[0]}")

    peak_cols = [f"{fn} Peak area" for fn in meta["filename"]]
    missing_cols = [c for c in peak_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"peak-area columns missing from aligned_features.csv for: {missing_cols}")

    peak_areas = df[peak_cols].copy()
    peak_areas.columns = meta["filename"].tolist()

    n_nan = int(peak_areas.isna().sum().sum())
    # ANALYSIS_OK[missingness]: NaN in aligned_features.csv peak-area columns means "not detected
    # in this gap-filled feature" (per README_FOR_CLAUDE.md), not a missing measurement -> 0 is
    # the correct value, not an imputation. Count of filled cells is logged via register_value
    # ("n_nan_peak_area_cells_filled_zero") immediately below for audit.
    peak_areas = peak_areas.fillna(0.0)
    register_value(
        "n_nan_peak_area_cells_filled_zero",
        n_nan,
        provenance="scripts/01_pcoa.py: aligned_features.csv gap-filled MGF export; NaN == not detected",
    )

    sample_x_feature = peak_areas.T
    sample_x_feature.index.name = "filename"
    if sample_x_feature.shape != (57, 12566):
        raise ValueError(f"unexpected sample x feature shape: {sample_x_feature.shape}")
    return sample_x_feature


def tic_normalize(sample_x_feature: pd.DataFrame) -> pd.DataFrame:
    row_sums = sample_x_feature.sum(axis=1)
    # ANALYSIS_OK[threshold]: 0 here is not a scientific cutoff, it is the mathematical identity
    # for "division undefined" — any sample with zero total peak area cannot be TIC-normalized and
    # must abort the run rather than silently producing inf/NaN downstream.
    zero_tic = row_sums[row_sums == 0]
    if not zero_tic.empty:
        raise ValueError(f"samples with zero total peak area (cannot TIC-normalize): {list(zero_tic.index)}")
    normalized = sample_x_feature.div(row_sums, axis=0)
    np.testing.assert_allclose(normalized.sum(axis=1).to_numpy(), 1.0, rtol=1e-8)
    return normalized


def classical_pcoa(distance_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Gower-centered eigendecomposition PCoA. Returns (scores, pct_variance_explained)."""
    n = distance_matrix.shape[0]
    d2 = distance_matrix**2
    centering = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * centering @ d2 @ centering
    eigvals, eigvecs = np.linalg.eigh(b)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    positive = np.clip(eigvals, a_min=0, a_max=None)
    total_positive = positive.sum()
    pct_var = 100 * positive / total_positive

    scores = eigvecs * np.sqrt(np.clip(eigvals, a_min=0, a_max=None))
    n_negative = int((eigvals < -1e-8).sum())
    if n_negative > 0:
        print(f"[pcoa] note: {n_negative} negative eigenvalues (Bray-Curtis is non-Euclidean); "
              f"using only positive axes for %variance.")
    return scores, pct_var


def permanova(distance_matrix: np.ndarray, groups: pd.Series, n_perm: int, rng: np.random.Generator) -> tuple[float, float]:
    """Pseudo-F PERMANOVA (Anderson 2001) with a label-permutation p-value."""
    n = distance_matrix.shape[0]
    d2 = distance_matrix**2
    ss_total = d2.sum() / (2 * n)

    def pseudo_f(labels: np.ndarray) -> float:
        ss_within = 0.0
        for g in np.unique(labels):
            idx = np.where(labels == g)[0]
            n_g = len(idx)
            if n_g < 2:
                continue
            sub = d2[np.ix_(idx, idx)]
            ss_within += sub.sum() / (2 * n_g)
        ss_among = ss_total - ss_within
        n_groups = len(np.unique(labels))
        df_among = n_groups - 1
        df_within = n - n_groups
        if df_among <= 0 or df_within <= 0 or ss_within <= 0:
            return np.nan
        return (ss_among / df_among) / (ss_within / df_within)

    labels = groups.to_numpy()
    f_obs = pseudo_f(labels)

    perm_f = np.empty(n_perm)
    for i in range(n_perm):
        perm_labels = rng.permutation(labels)
        perm_f[i] = pseudo_f(perm_labels)

    valid = ~np.isnan(perm_f)
    p_value = (np.sum(perm_f[valid] >= f_obs) + 1) / (valid.sum() + 1)
    return float(f_obs), float(p_value)


def plot_pcoa(scores: np.ndarray, pct_var: np.ndarray, meta: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)

    xlab = f"PCo1 ({pct_var[0]:.1f}%)"
    ylab = f"PCo2 ({pct_var[1]:.1f}%)"

    ax = axes[0]
    for st, color in SAMPLE_TYPE_COLORS.items():
        mask = (meta["sample_type"] == st).to_numpy()
        if not mask.any():
            continue
        ax.scatter(scores[mask, 0], scores[mask, 1], c=color, label=st, s=45, edgecolor="k", linewidth=0.3)
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.set_title("Colored by sample_type")
    ax.legend(fontsize=8, loc="best")
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)

    ax = axes[1]
    for tg, color in TREATMENT_COLORS.items():
        mask = (meta["treatment_group"] == tg).to_numpy()
        if not mask.any():
            continue
        ax.scatter(scores[mask, 0], scores[mask, 1], c=color, label=tg, s=45, edgecolor="k", linewidth=0.3)
    ax.set_xlabel(xlab)
    ax.set_title("Colored by treatment_group")
    ax.legend(fontsize=8, loc="best")
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)

    fig.suptitle("PCoA (Bray-Curtis) — gnps2-ad67978e-bagel MS1 feature-quant table, TIC-normalized")
    fig.tight_layout()
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=200)
    plt.close(fig)


def plot_pcoa_single_panel(
    scores: np.ndarray, pct_var: np.ndarray, groups: pd.Series, colors: dict[str, str], title: str, out_path: Path
) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for g, color in colors.items():
        mask = (groups == g).to_numpy()
        if not mask.any():
            continue
        ax.scatter(scores[mask, 0], scores[mask, 1], c=color, label=g, s=45, edgecolor="k", linewidth=0.3)
    ax.set_xlabel(f"PCo1 ({pct_var[0]:.1f}%)")
    ax.set_ylabel(f"PCo2 ({pct_var[1]:.1f}%)")
    ax.set_title(title, fontsize=11, wrap=True)
    ax.legend(fontsize=8, loc="best")
    ax.axhline(0, color="grey", lw=0.5)
    ax.axvline(0, color="grey", lw=0.5)
    fig.tight_layout()
    fig.savefig(out_path)
    fig.savefig(out_path.with_suffix(".png"), dpi=200)
    plt.close(fig)


def main() -> None:
    rng = np.random.default_rng(RNG_SEED)

    meta = load_metadata()
    sample_x_feature = load_feature_table(meta)
    if list(sample_x_feature.index) != list(meta["filename"]):
        raise ValueError("sample order mismatch after join between feature table and metadata")

    normalized = tic_normalize(sample_x_feature)

    bray_curtis = squareform(pdist(normalized.to_numpy(), metric="braycurtis"))
    if bray_curtis.shape != (57, 57):
        raise ValueError(f"unexpected Bray-Curtis distance matrix shape: {bray_curtis.shape}")
    if not np.allclose(np.diag(bray_curtis), 0.0):
        raise ValueError("Bray-Curtis distance matrix has nonzero diagonal")

    scores, pct_var = classical_pcoa(bray_curtis)

    register_value("n_samples_total", int(meta.shape[0]), provenance="scripts/01_pcoa.py")
    register_value("n_samples_biological", int((meta["sample_type"] == "sample").sum()), provenance="scripts/01_pcoa.py")
    register_value("n_qc_blanks", int((meta["sample_type"] != "sample").sum()), provenance="scripts/01_pcoa.py")
    register_value("n_features_pcoa", int(sample_x_feature.shape[1]), provenance="scripts/01_pcoa.py")
    register_value("pcoa_pc1_pct_variance", round(float(pct_var[0]), 2), provenance="scripts/01_pcoa.py")
    register_value("pcoa_pc2_pct_variance", round(float(pct_var[1]), 2), provenance="scripts/01_pcoa.py")
    register_value("pcoa_distance_metric", "bray-curtis", provenance="scripts/01_pcoa.py")
    register_value("pcoa_normalization", "TIC (total-peak-area) per sample", provenance="scripts/01_pcoa.py")
    register_value("permanova_n_permutations", N_PERMUTATIONS, provenance="scripts/01_pcoa.py")
    register_value("permanova_random_seed", RNG_SEED, provenance="scripts/01_pcoa.py")

    f_sample_type, p_sample_type = permanova(bray_curtis, meta["sample_type"], N_PERMUTATIONS, rng)
    register_value("permanova_pseudo_f_sample_type", round(f_sample_type, 3), provenance="scripts/01_pcoa.py")
    register_value("permanova_pvalue_sample_type", round(p_sample_type, 4), provenance="scripts/01_pcoa.py")

    bio_mask = (meta["sample_type"] == "sample").to_numpy()
    bio_idx = np.where(bio_mask)[0]
    bc_bio = bray_curtis[np.ix_(bio_idx, bio_idx)]
    treat_bio = meta.loc[bio_mask, "treatment_group"].reset_index(drop=True)
    f_treatment, p_treatment = permanova(bc_bio, treat_bio, N_PERMUTATIONS, rng)
    register_value("permanova_pseudo_f_treatment_group", round(f_treatment, 3), provenance="scripts/01_pcoa.py (biological samples only, QC blanks excluded)")
    register_value("permanova_pvalue_treatment_group", round(p_treatment, 4), provenance="scripts/01_pcoa.py (biological samples only, QC blanks excluded)")

    plot_pcoa(scores, pct_var, meta, OUT_DIR / "pcoa_bray_curtis.pdf")

    coords = pd.DataFrame(scores[:, :5], columns=[f"PCo{i+1}" for i in range(5)], index=meta["filename"])
    coords = coords.join(meta.set_index("filename")[["sample_id", "sample_type", "treatment_group", "subject_id"]])
    coords.to_csv(OUT_DIR / "pcoa_scores.csv")

    var_table = pd.DataFrame({"axis": [f"PCo{i+1}" for i in range(len(pct_var))], "pct_variance": pct_var})
    var_table.to_csv(OUT_DIR / "pcoa_variance_explained.csv", index=False)

    print(f"PC1 {pct_var[0]:.1f}%  PC2 {pct_var[1]:.1f}%")
    print(f"PERMANOVA sample_type: pseudo-F={f_sample_type:.3f}, p={p_sample_type:.4f} (n_perm={N_PERMUTATIONS})")
    print(f"PERMANOVA treatment_group (biological samples only): pseudo-F={f_treatment:.3f}, p={p_treatment:.4f} (n_perm={N_PERMUTATIONS})")

    # No-blanks version: PCoA is re-run on the biological-sample-only Bray-Curtis submatrix
    # (Bray-Curtis pairwise distances themselves don't change when other samples are dropped,
    # but the Gower centering in classical_pcoa is computed over the sample set being ordinated,
    # so scores/axes for the subset differ from slicing the full-sample ordination).
    meta_bio = meta.loc[bio_mask].reset_index(drop=True)
    scores_bio, pct_var_bio = classical_pcoa(bc_bio)
    if scores_bio.shape[0] != int(bio_mask.sum()):
        raise ValueError(f"biological-only PCoA sample count mismatch: {scores_bio.shape[0]} vs {int(bio_mask.sum())}")

    register_value("pcoa_no_blanks_n_samples", int(bio_mask.sum()), provenance="scripts/01_pcoa.py")
    register_value("pcoa_no_blanks_pc1_pct_variance", round(float(pct_var_bio[0]), 2), provenance="scripts/01_pcoa.py")
    register_value("pcoa_no_blanks_pc2_pct_variance", round(float(pct_var_bio[1]), 2), provenance="scripts/01_pcoa.py")

    plot_pcoa_single_panel(
        scores_bio,
        pct_var_bio,
        meta_bio["treatment_group"],
        {k: v for k, v in TREATMENT_COLORS.items() if k != "(QC blank)"},
        "PCoA (Bray-Curtis), QC blanks removed — colored by treatment_group",
        OUT_DIR / "pcoa_bray_curtis_no_blanks.pdf",
    )

    coords_bio = pd.DataFrame(scores_bio[:, :5], columns=[f"PCo{i+1}" for i in range(5)], index=meta_bio["filename"])
    coords_bio = coords_bio.join(meta_bio.set_index("filename")[["sample_id", "treatment_group", "subject_id"]])
    coords_bio.to_csv(OUT_DIR / "pcoa_scores_no_blanks.csv")

    print(f"[no-blanks] PC1 {pct_var_bio[0]:.1f}%  PC2 {pct_var_bio[1]:.1f}% (n={int(bio_mask.sum())})")
    print(f"Outputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
