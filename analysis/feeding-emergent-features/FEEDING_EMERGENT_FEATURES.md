# Feeding Emergent Features

## Purpose

Identify MS features from `gnps2-ad67978e-bagel` that show a specific
biological pattern: **absent/very low in `control` samples, absent/very
low in the early days after Basidiobolus feeding, and clearly higher in
the late stage of feeding** — in either the STP1710.7 or STP1717.1 pilot
cohort. Candidates like this are leads for a metabolite that's actively
produced or accumulated as a consequence of the feeding exposure, rather
than a baseline gut/diet metabolite.

## Status

**Status**: complete (screening pass; annotation/confirmation not attempted)

## Datasets

- `gnps2-ad67978e-bagel` (`data/DATA_MANIFEST.md`) — feature-quant table
  (`aligned_features.csv.gz`), enriched sample metadata
  (`merged_metadata.tsv`), spectral-library hits
  (`merged_feature_library_search_results.tsv`).

## Parent Analysis

- Parent: `pcoa-ms-feature-composition`
- What's different: that analysis established (a) TIC normalization as
  the right cross-sample comparison, (b) the derived `days_post_feeding`
  variable and its three natural collection-round clusters, and (c) that
  age/timeline — not treatment group — was the dominant PCoA axis. This
  analysis reuses (a) and (b) to ask a targeted per-feature question that
  PCoA (an aggregate ordination) can't answer directly: *which individual
  features* drive a feeding-emergent pattern, as opposed to which axis of
  overall composition correlates with time.

## Method

1. **Early/late day bins** are the two outer thirds of the natural
   3-timepoint collection structure identified in the parent analysis
   (`days_post_feeding` clusters at roughly [-1,10], [24,33], [50,63]):
   `EARLY_DAYS_MAX = 10`, `LATE_DAYS_MIN = 45`. The middle round is
   dropped from the early/late comparison (used only in the age/PCoA
   analysis), so "early" and "late" are genuinely separated timepoints,
   not a median split.
2. TIC-normalize the 50-biological-sample x 12,566-feature peak-area
   table (same procedure as the parent PCoA analysis).
3. For each of the two treated groups (STP1710.7, STP1717.1) separately,
   and for every feature, compute in three sample sets — all `control`
   samples (n=17), that group's early samples, that group's late
   samples — the detection rate (fraction of samples with signal >0) and
   median normalized abundance.
4. **Screening criteria** (all required; thresholds are relative to each
   feature's own max normalized abundance across the 50 biological
   samples, since peak areas span orders of magnitude across features):
   - `control_low`: detect rate ≤30% AND median ≤10% of the feature's max
   - `early_low`: same criteria, in that group's early samples
   - `late_high`: detect rate ≥50% AND median ≥50% of the feature's max,
     in that group's late samples
   - `fold_change` (late median / early median, 1%-of-max pseudocount) ≥4x
5. **Significance**: one-sided Mann-Whitney U (late samples > control+early
   pooled baseline), computed for **all** 12,566 features per group (not
   just pre-screened ones, to avoid selection bias in the p-values), then
   Benjamini-Hochberg FDR corrected within each group's 12,566 tests.
   `FDR_THRESHOLD = 0.05`.
6. Reported at two tiers: **FDR-significant candidates** (pass screening
   criteria AND q<0.05) and the broader **pattern-matching leads**
   (pass the four screening criteria but not necessarily FDR-significant
   — small early/late group sizes, n=5-7, limit statistical power after
   correcting across 12,566 tests). Both tiers are exported; only the
   FDR-significant tier should be treated as a confident call.
7. Joined results to `row m/z`/`row retention time`/`adduct` and to any
   GNPS spectral-library hit (`merged_feature_library_search_results.tsv`,
   joined on `query_scan` = feature id) for interpretability.

## Key Findings

- **1 feature is FDR-significant**: feature `4506` (m/z 1419.8656, RT
  17.858 min) in the **STP1717.1 pilot** cohort — undetected in all
  control samples and all STP1717.1 early samples, detected in 80% of
  STP1717.1 late samples, 64.4x fold change, FDR q=0.030. STP1710.7 had
  zero FDR-significant candidates at this sample size.
- **17 pattern-matching leads** (8 in STP1710.7, 10 in STP1717.1, not
  FDR-significant) match the qualitative shape the user asked about —
  see `outputs/feeding_emergent_pattern_leads.csv`, ranked by fold change.
  None have a spectral-library hit (all `library_name` are NaN) — these
  are unannotated leads, not confirmed compound identifications.
- **One feature (`12362`, m/z 771.2756) shows the pattern independently
  in BOTH treated groups** (STP1710.7 fdr_q=0.22, STP1717.1 fdr_q=0.15;
  neither individually significant, but the same feature reaching the
  pattern threshold in two independent cohorts is a stronger lead than
  its p-values alone suggest).
- **Possible co-eluting compound family**: features `4506` (m/z
  1419.8656), `3345` (m/z 1392.8453), and `3520` (m/z 1418.8621) all
  share **the same retention time, 17.858 min**, and are all
  pattern-matching leads in STP1717.1. Identical RT for multiple
  features in a small mass window is a signature of isotopologues,
  in-source fragments, or multiple adducts of one underlying compound
  (per README_FOR_CLAUDE.md's "in-source fragments" and "mass QC"
  guidance) — worth checking `is_isf`/`isf_parent_id` and the
  `network.graphml` component for these three before treating them as
  three independent hits.
- Trajectory plots for the top 9 pattern leads (`outputs/top_candidate_trajectories.png`)
  visually confirm the shape for most: near-zero at day ≤10 across all
  groups, rising by day ≥50, with `control` samples staying low/absent
  across their own full date range (control has no "late" bin by
  construction — see Open Questions).

## Open Questions

- **None of the 18 unique candidate/lead features have a spectral-library
  hit.** Per README_FOR_CLAUDE.md's annotation workflow, next steps would
  be: (1) pull each feature's node from `network.graphml` and check its
  `component` for an annotated neighbor to propagate from; (2) screen
  their MS/MS (`aligned_features_filled.mgf`, `SCANS`=feature id) for
  known Basidiobolus/fungal or amide/lipid class-diagnostic ions; (3) run
  `massql` queries per the bundle's local-tooling guidance. Not attempted
  in this pass — this analysis only screens the quant table.
- **Only 1 of 18 candidates is FDR-significant** — the other 17 are
  reported as leads, not findings. Late-group sample sizes (n=5-7 per
  cohort) limit power after correcting across 12,566 tests; a targeted
  re-test restricted to just these 18 pre-identified features (much
  smaller multiple-testing burden) would be a fair follow-up now that
  they're not "discovered" on that re-test's own p-values.
- The 3 same-RT features (`4506`/`3345`/`3520`) should be checked for
  `is_isf`/`isf_parent_id` relationships and adduct calls before being
  treated as 3 independent feeding-emergent compounds rather than one.
- `control` samples don't have a "late" bin in this design (they're used
  as one pooled baseline group across all their timepoints) — so
  "low in control" here means low across the control group's full date
  range, not specifically at the late collection round. If a reviewer
  wants a stricter comparison (late-treated vs. late-control specifically,
  controlling for calendar time given the parent analysis's finding that
  age/time is a dominant axis even in controls), that's a natural
  follow-up but requires small-n statistics (control late-round n was not
  checked here).
- Screening thresholds (30%/10%/50%/50%/4x) are reasonable but somewhat
  arbitrary named constants (see `scripts/01_screen_features.py`) — a
  sensitivity sweep (per the repo's robust-analysis convention) was not
  run; the candidate list could shrink or grow under nearby threshold
  choices.

## Reproducibility

To reproduce all outputs:

```bash
cd analysis/feeding-emergent-features
bash run.sh
```

Requires `pandas`, `numpy`, `scipy`, `matplotlib` (same environment as
`pcoa-ms-feature-composition`; see `ENVIRONMENTS_INSTALLATIONS.md`).

## Outputs

| File | Description |
|------|-------------|
| `outputs/feature_screen_all_results.csv` | Full screening results for all 12,566 features x 2 treated groups (25,132 rows), including features that failed screening — the complete audit trail. |
| `outputs/feeding_emergent_candidates.csv` | The strict, FDR-significant tier (screening criteria + q<0.05). |
| `outputs/feeding_emergent_pattern_leads.csv` | The broader pattern-matching tier (screening criteria only, not FDR-corrected), ranked by fold change. |
| `outputs/top_candidate_trajectories.pdf` / `.png` | Per-sample abundance vs. `days_post_feeding` for the top 9 pattern leads, colored by `treatment_group` (control shown for reference), one panel per feature. |
| `outputs/numbers.json` | Reportable values (bin definitions, thresholds, candidate/lead counts per group and combined) registered via `register_value`. |
