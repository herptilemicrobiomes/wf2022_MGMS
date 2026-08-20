"""Check whether the two derived age/timeline variables used in 01_pcoa.py
(days_post_metamorphosis, days_post_feeding) are themselves correlated,
and plot the relationship with both axes labeled.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]
OUT_DIR = ANALYSIS_ROOT / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_ROOT / "analysis" / "_lib"))
from register_value import register_value  # noqa: E402

RAW_DIR = REPO_ROOT / "data" / "raw" / "gnps2_ad67978e_bagel"
METADATA_PATH = RAW_DIR / "nf_output" / "metadata" / "merged_metadata.tsv"

TREATMENT_COLORS = {
    "control": "#1B9E77",
    "STP1710.7 pilot": "#D95F02",
    "STP1717.1 pilot": "#7570B3",
}


def main() -> None:
    meta = pd.read_csv(METADATA_PATH, sep="\t", dtype=str)
    bio = meta[meta["sample_type"] == "sample"].copy()
    if bio.shape[0] != 50:
        raise ValueError(f"expected 50 biological samples, got {bio.shape[0]}")

    for col in ("collection_date", "metamorphosis_date", "basidiobolus_feeding_date"):
        parsed = pd.to_datetime(bio[col], errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"unparseable/missing {col} among biological samples")
        bio[col] = parsed

    bio["days_post_metamorphosis"] = (bio["collection_date"] - bio["metamorphosis_date"]).dt.days
    bio["days_post_feeding"] = (bio["collection_date"] - bio["basidiobolus_feeding_date"]).dt.days

    r, p_pearson = pearsonr(bio["days_post_metamorphosis"], bio["days_post_feeding"])
    rho, p_spearman = spearmanr(bio["days_post_metamorphosis"], bio["days_post_feeding"])

    register_value("age_vars_n_samples", int(bio.shape[0]), provenance="scripts/02_age_variable_correlation.py")
    register_value("age_vars_pearson_r", round(float(r), 4), provenance="scripts/02_age_variable_correlation.py")
    register_value("age_vars_pearson_pvalue", float(p_pearson), provenance="scripts/02_age_variable_correlation.py")
    register_value("age_vars_spearman_rho", round(float(rho), 4), provenance="scripts/02_age_variable_correlation.py")
    register_value("age_vars_spearman_pvalue", float(p_spearman), provenance="scripts/02_age_variable_correlation.py")

    fig, ax = plt.subplots(figsize=(6.5, 6))
    for tg, color in TREATMENT_COLORS.items():
        mask = (bio["treatment_group"] == tg).to_numpy()
        if not mask.any():
            continue
        ax.scatter(
            bio.loc[mask, "days_post_metamorphosis"],
            bio.loc[mask, "days_post_feeding"],
            c=color,
            label=tg,
            s=55,
            edgecolor="k",
            linewidth=0.4,
        )
    lims = [
        min(bio["days_post_metamorphosis"].min(), bio["days_post_feeding"].min()) - 3,
        max(bio["days_post_metamorphosis"].max(), bio["days_post_feeding"].max()) + 3,
    ]
    ax.plot(lims, lims, color="grey", lw=0.8, linestyle="--", label="y = x")
    ax.set_xlabel("Days post metamorphosis (developmental age)")
    ax.set_ylabel("Days post Basidiobolus feeding")
    ax.set_title(
        f"days_post_metamorphosis vs. days_post_feeding (n={bio.shape[0]})\n"
        f"Pearson r={r:.3f} (p={p_pearson:.2e}), Spearman rho={rho:.3f} (p={p_spearman:.2e})",
        fontsize=10,
    )
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "age_variable_correlation.pdf")
    fig.savefig(OUT_DIR / "age_variable_correlation.png", dpi=200)
    plt.close(fig)

    bio[["sample_id", "subject_id", "treatment_group", "days_post_metamorphosis", "days_post_feeding"]].to_csv(
        OUT_DIR / "age_variable_correlation.csv", index=False
    )

    print(f"n={bio.shape[0]}  Pearson r={r:.4f} p={p_pearson:.2e}  Spearman rho={rho:.4f} p={p_spearman:.2e}")
    print(f"Outputs written to {OUT_DIR}")


if __name__ == "__main__":
    main()
