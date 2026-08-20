# PCoA MS Feature Composition

## Purpose

How do the 57 MS1 feature-quant samples (50 biological wood-frog fecal
samples + 7 QC blanks) from the `gnps2-ad67978e-bagel` bundle lay out in
ordination space, and does that layout separate by `sample_type` (QC vs.
biological) or by feeding-experiment `treatment_group`?

## Status

**Status**: complete

## Datasets

- `gnps2-ad67978e-bagel` (`data/DATA_MANIFEST.md`) — primary feature-quant
  table (`aligned_features.csv.gz`, 12,566 features x 57 samples' peak-area
  columns) and enriched sample metadata (`merged_metadata.tsv`).

## Algorithms

No entry yet in `algorithms/ALGORITHM_MANIFEST.md` — this analysis uses a
short, self-contained classical (Gower) PCoA implementation and a
permutation-based PERMANOVA (Anderson 2001 pseudo-F), both in
`scripts/01_pcoa.py`, rather than a registered reusable algorithm module.

## Method

1. Load the MS1 (non-MS1-suffixed, i.e. MS2-file-associated) peak-area
   columns from `aligned_features.csv.gz`, matched to
   `merged_metadata.tsv` by `filename`.
2. Fill NaN peak areas with 0 (README_FOR_CLAUDE.md: NaN in this gap-filled
   export means "not detected," not "missing measurement").
3. TIC-normalize each sample (divide by that sample's total peak area
   across all 12,566 features), per the bundle README's cross-sample
   guidance.
4. Compute a Bray-Curtis distance matrix across the 57 samples and run
   classical (Gower-centered eigendecomposition) PCoA.
5. Test group separation with a permutation PERMANOVA (999 permutations,
   seed 42): once for `sample_type` (all 57 samples) and once for
   `treatment_group` restricted to the 50 biological samples (QC blanks
   excluded — they have no treatment_group).

## Key Findings

- **PC1 explains 38.1% of variance, PC2 13.0%** (15 of 57 eigenvalues were
  negative, expected for a non-Euclidean Bray-Curtis distance; % variance
  is computed over positive eigenvalues only).
- **`sample_type` separates strongly and significantly**: QC blanks (solvent
  blank, blank-with-internal-standard) sit far out along PC1/PC2 from the
  biological-sample cluster; PERMANOVA pseudo-F = 16.39, p = 0.001
  (999 permutations). This is the expected/sanity-check result — it shows
  the ordination and normalization are behaving reasonably (blanks should
  look chemically distinct from fecal extracts).
- **`treatment_group` (control / STP1710.7 pilot / STP1717.1 pilot) does
  NOT separate** among the 50 biological samples: PERMANOVA pseudo-F =
  0.93, p = 0.543. Visually the three treatment groups are fully
  intermixed within the biological-sample cluster in both panels of
  `outputs/pcoa_bray_curtis.pdf`.
- One biological sample is a clear outlier (PCo1 ≈ 0.38, far from the main
  sample cluster) and one `QC_blank_extract` sits closer to the biological
  cluster than the other blanks — worth a closer look (see Open Questions)
  before treating either as routine.

## Open Questions

- Identify the outlier biological sample (PCo1 ≈ 0.38) by `sample_id` in
  `outputs/pcoa_scores.csv` and check whether it's a QC/handling issue or a
  genuine biological outlier.
- The one `QC_blank_extract` that lands near the biological-sample cluster
  (rather than with the other blanks) may indicate carryover/contamination
  in that extraction blank — worth flagging to the wet-lab side.
- `treatment_group` and `treatment` columns in `merged_metadata.tsv` are
  identical in this bundle; only `treatment_group` was used here.
- Non-significant treatment-group PERMANOVA here is a global test across
  all 12,566 features — a more targeted test (e.g. restricted to
  library-annotated / diagnostic-ion-confirmed features, per the bundle
  README's annotation guidance) might still reveal a treatment effect
  masked by noise features in the full table. Not attempted in this pass.
- No correction for `tank`/`egg_mass`/collection-date structure — treatment
  groups may be confounded with these design variables; not checked here.

## Reproducibility

To reproduce all outputs:

```bash
cd analysis/pcoa-ms-feature-composition
bash run.sh
```

Requires `pandas`, `numpy`, `scipy`, `matplotlib` (available via the
system `python3` / miniconda env on this host — no project-level pixi
environment exists yet; see `ENVIRONMENTS_INSTALLATIONS.md`).

## Outputs

| File | Description |
|------|-------------|
| `outputs/pcoa_bray_curtis.pdf` / `.png` | Two-panel PCoA ordination (PC1 vs PC2), colored by `sample_type` and by `treatment_group`. |
| `outputs/pcoa_scores.csv` | Per-sample PCo1-5 coordinates joined to `sample_id`, `sample_type`, `treatment_group`, `subject_id`. |
| `outputs/pcoa_variance_explained.csv` | % variance explained per PCoA axis. |
| `outputs/numbers.json` | Reportable values (sample/feature counts, % variance, PERMANOVA pseudo-F/p) registered via `register_value`. |
