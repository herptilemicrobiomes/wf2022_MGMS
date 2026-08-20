# Data Manifest

<!-- Add entries below using the appropriate manifest entry template. -->

### gnps2-f7a16270-bagel — SUPERSEDED, see gnps2-ad67978e-bagel
```yaml
name: gnps2-f7a16270-bagel
type: other  # untargeted LC-MS/MS metabolomics: feature quant + networking + library search
source: GNPS2 Everything Bagel workflow (apps.gnps2.org), task f7a1627054b34a238404d709e9d962f6, input dataset MassIVE MSV000095549
date_acquired: 2026-08-20
format: CSV/TSV/MGF/YAML (multi-file bundle)
rows: aligned_features.csv rows = one per feature (row/cluster id)
columns: N/A (per-file peak areas + m/z + RT columns; see aligned_features.csv header)
size: ~40 MB total bundle
raw_path: data/raw/gnps2_f7a16270_bagel/  # NOTE: no longer present on disk as of 2026-08-20
processed_path: # none
metadata_path: data/metadata/gnps2_f7a16270_bagel/sample_metadata_animal_enriched.csv  # hand-built enrichment; reused as the metadata_file input for the v2 rerun below
status: superseded
known_issues:
  - Raw bundle directory (data/raw/gnps2_f7a16270_bagel/) no longer exists on disk; only the derived metadata files under data/metadata/gnps2_f7a16270_bagel/ remain
  - Superseded by gnps2-ad67978e-bagel (v2 re-run of the same workflow/input with the enriched metadata baked into the GNPS2 job itself); use that entry for new work
access_restrictions: none
tags: [metabolomics, LC-MS-MS, GNPS2, molecular-networking, feature-finding, herptile, superseded]
```

Original Everything Bagel export for the Herptile metabolomics WF_2022 dataset. **Superseded 2026-08-20 by `gnps2-ad67978e-bagel`** (below), a v2 re-run of the same workflow against the same MassIVE input with the hand-built sample-metadata enrichment (`sample_metadata_animal_enriched.csv`, produced from this bundle's template) submitted directly as the GNPS2 job's metadata input. The raw bundle for this entry is no longer present on disk — kept here for provenance of the metadata-enrichment work only.

### gnps2-ad67978e-bagel
```yaml
name: gnps2-ad67978e-bagel
type: other  # untargeted LC-MS/MS metabolomics: feature quant + networking + library search
source: GNPS2 Everything Bagel workflow (apps.gnps2.org), task ad67978e27274245abe5ea428c44ce09, input dataset MassIVE MSV000095549 ("v2 - WoodFrog fecal from feeding experiments")
date_acquired: 2026-08-20
format: CSV/TSV/MGF/GraphML/YAML (multi-file bundle)
rows: aligned_features.csv = 12566 features (row id); merged_metadata.tsv = 57 samples/blanks
columns: aligned_features.csv = 143 (fixed QC/feature columns + one peak-area column per linked sample file)
size: ~96 MB total bundle
raw_path: data/raw/gnps2_ad67978e_bagel/
processed_path: # none yet
metadata_path: data/raw/gnps2_ad67978e_bagel/nf_output/metadata/merged_metadata.tsv  # already fully enriched (species/tissue/tank/dates/treatment) — submitted as this run's metadata_file, no separate join needed
status: raw
known_issues:
  - No MS1 isotope envelope in this export — halogen calls and charge-state disambiguation cannot be closed
  - No fragment-position information — hydroxyl vs oxo ambiguity, regiochemistry needs ModiFinder-style work or standards
  - Representative MS2 spectra are pooled per feature, not per-sample; presence of a diagnostic ion is a property of the node, not the subject — join aligned_features.csv peak-area columns to merged_metadata.tsv on filename for per-sample/per-subject claims
  - merged_feature_library_search_results.tsv (265 hits) library matches carry no confidence beyond MQScore/SharedPeaks — treat as leads, tier by evidence hierarchy (class ion > compound-specific fragment > ppm > network proximity)
  - gps_lat/gps_lon are blank for all rows in this export
access_restrictions: none
tags: [metabolomics, LC-MS-MS, GNPS2, molecular-networking, feature-finding, herptile, wood-frog]
```

v2 re-run of the Everything Bagel workflow on the Herptile metabolomics WF_2022 dataset (MassIVE MSV000095549), bundling feature quantification (`aligned_features.csv`, 12,566 features), gap-filled MS/MS (`aligned_features_filled.mgf`), molecular-networking edges (`filtered_pairs.tsv`/`merged_pairs.tsv`, 2,014 filtered edges), and spectral-library hits (`merged_feature_library_search_results.tsv`). Unlike the superseded `gnps2-f7a16270-bagel` run, this job was submitted with the hand-built sample-metadata enrichment file as its `metadata_file` input, so `nf_output/metadata/merged_metadata.tsv` already carries full biological annotation (species *Lithobates sylvaticus*, tissue, tank, dates, treatment group) for all 50 sample rows — no separate metadata join is required. Full annotation guidance (mass conventions, diagnostic ions, artifact screens, USI-based spectrum linking, formula-search discipline) lives in `data/raw/gnps2_ad67978e_bagel/README_FOR_CLAUDE.md` — read it before doing any annotation work on this bundle. Join key across files is the feature/row id (MGF `SCANS` field, graphml cluster index).
