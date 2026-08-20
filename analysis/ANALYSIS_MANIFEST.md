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

PCoA (Bray-Curtis, TIC-normalized) ordination of the 57-sample MS1 feature-quant table from `gnps2-ad67978e-bagel`, colored by `sample_type` and `treatment_group`, with PERMANOVA significance tests for both groupings. QC blanks separate strongly and significantly from biological samples (pseudo-F=16.39, p=0.001); the three feeding-experiment treatment groups do not separate among biological samples (pseudo-F=0.93, p=0.543). See `PCOA_MS_FEATURE_COMPOSITION.md` for full findings and open questions.
