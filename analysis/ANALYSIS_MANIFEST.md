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
