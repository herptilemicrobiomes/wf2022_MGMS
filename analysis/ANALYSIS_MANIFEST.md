# Analysis Manifest

<!-- Add entries below using the appropriate manifest entry template. -->

### pcoa-ms-feature-composition

```yaml
name: pcoa-ms-feature-composition
status: complete
datasets: [gnps2-ad67978e-bagel]
algorithms: []  # self-contained Bray-Curtis PCoA + permutation PERMANOVA in scripts/01_pcoa.py
parent_analysis: none
path: analysis/pcoa-ms-feature-composition/
```

PCoA (Bray-Curtis, TIC-normalized) ordination of the 57-sample MS1 feature-quant table from `gnps2-ad67978e-bagel`, colored by `sample_type` and `treatment_group`, with PERMANOVA significance tests for both groupings, plus a second ordination re-run on the 50 biological samples with QC blanks removed (controls included) that's also plotted colored by a derived `days_post_feeding` age variable (shape = `treatment_group`). QC blanks separate strongly and significantly from biological samples (pseudo-F=16.39, p=0.001); `treatment_group` does not separate biological samples (pseudo-F=0.93, p=0.543); but the derived `days_post_feeding` timeline correlates strongly with PC1 (rho=0.65, p<0.0001) — and does so identically in `control` animals, meaning this axis is confounded with (or simply is) calendar time/batch, not a treatment-specific biological effect. `days_post_feeding` and `days_post_metamorphosis` (developmental age) are themselves near-collinear (Pearson r=0.998), so this dataset cannot statistically distinguish a time-since-exposure effect from a developmental-age effect. See `PCOA_MS_FEATURE_COMPOSITION.md` for full findings, embedded plots, and open questions.

### feeding-emergent-features

```yaml
name: feeding-emergent-features
status: complete
datasets: [gnps2-ad67978e-bagel]
algorithms: []  # per-feature screening (detect-rate/median thresholds) + vectorized Mann-Whitney U + BH-FDR in scripts/01_screen_features.py
parent_analysis: pcoa-ms-feature-composition
path: analysis/feeding-emergent-features/
```

Per-feature screen of the 12,566-feature quant table for a "feeding-emergent" pattern: absent/very-low in `control`, absent/very-low early after Basidiobolus feeding, clearly higher late after feeding — tested separately for the STP1710.7 and STP1717.1 pilot cohorts (early/late bins = the two outer thirds of the natural 3-timepoint collection structure found in the parent PCoA analysis). 1 feature is FDR-significant (feature 4506, STP1717.1, q=0.03, 64x fold change); 17 more match the pattern without reaching FDR significance at this sample size (reported as leads, not findings) — including one feature (12362) matching independently in both cohorts, and three same-retention-time features that may be one compound's isotopologues/adducts rather than three independent hits. None of the candidates have a spectral-library annotation. See `FEEDING_EMERGENT_FEATURES.md` for full method, findings, and open questions.

### sirius_annotation

```yaml
name: sirius_annotation
status: active
datasets: [gnps2-ad67978e-bagel]
algorithms: []  # SIRIUS 6.3.12 (formula/fingerprint/CANOPUS/CSI:FingerID structures) via shared Singularity container; pipeline scripts adapted from the Bd_massspec and Rhodotorula_pheno_MS sirius_annotation frameworks
parent_analysis: feeding-emergent-features
path: analysis/sirius_annotation/
```

SIRIUS structural/compound-class annotation, adapted from the sibling projects' `sirius_annotation` pipelines (shared `.sif` container, target-select -> MGF-export -> shard -> run -> merge -> import script pattern). Two target sets: `interesting` (the 17 unique `feeding-emergent-features` candidate/lead feature ids) and `full` (3,530 of 12,566 features with real MS2 and singly-charged precursor). Only 3 of the 17 "interesting" features have real MS/MS spectra at all (the other 14 are gap-filled placeholders with no fragmentation data); the interesting-features run completed (job 27661542) and found no trustworthy hit among those 3 (one uncallable formula, one formula-only with an implausibly large C62H101N11O15 composition, one structure hit at ConfidenceScoreExact=0.09 — effectively unconfident). The full run (177 shards, ~2-3 days serial wall-clock) was submitted 2026-08-20 as array job `27671478` with a dependent merge/import job `27671479` (`--dependency=afterok`) chained to run automatically on completion, so it finishes unattended without needing an interactive session. See `SIRIUS_ANNOTATION.md` for the full pipeline, job ids, and status-check instructions for a future session.
