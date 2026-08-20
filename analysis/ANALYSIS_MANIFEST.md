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

PCoA (Bray-Curtis, TIC-normalized) ordination of the 57-sample MS1 feature-quant table from `gnps2-ad67978e-bagel`, colored by `sample_type` and `treatment_group`, with PERMANOVA significance tests for both groupings, a second ordination re-run on the 50 biological samples with QC blanks removed, and a third re-run on the 33 Basidiobolus-fed samples (blanks + controls removed) colored by a derived `days_post_feeding` age variable. QC blanks separate strongly and significantly from biological samples (pseudo-F=16.39, p=0.001); `treatment_group` does not separate biological samples (pseudo-F=0.93, p=0.543); but the derived `days_post_feeding` timeline correlates significantly with both PC1 (rho=0.54, p=0.0012) and PC2 (rho=-0.45, p=0.0093) in the treated-only ordination — sample age since feeding looks like the dominant biological axis of variation, not treatment arm. See `PCOA_MS_FEATURE_COMPOSITION.md` for full findings, embedded plots, and open questions.
