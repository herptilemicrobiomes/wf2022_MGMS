# Summary Statistics: gnps2_ad67978e_bagel

<!-- Generated: 2026-08-20 -->
<!-- Script: manual (wc -l / head / cut on the bundle files) -->

## Overview (primary feature-quant table)

| Property | Value |
|----------|-------|
| File | `nf_output/feature_finding/feature_finding_results/aligned_features.csv` |
| Rows (features) | 12,566 |
| Columns | 143 (fixed feature-finding/QC columns + one peak-area column per linked sample mzML file) |
| File size | 6.6 MB |
| Format | CSV |

## Other key files

| File | Rows | Notes |
|------|------|-------|
| `nf_output/metadata/merged_metadata.tsv` | 58 (57 samples/blanks + header) | 50 `sample`, 3 `QC_blank_extract`, 1 `QC_blank_solvent`, 3 `QC_blank_with_internal_standard`. All `sample` rows are *Lithobates sylvaticus*, tissue `fecal`. |
| `nf_output/networking/filtered_pairs.tsv` | 2,014 edges | Filtered molecular-networking edges (CLUSTERID1/CLUSTERID2/DeltaMZ/Cosine/MatchedPeaks). |
| `nf_output/feature_library_search/merged_feature_library_search_results.tsv` | 265 hits | Spectral-library matches keyed on feature id — leads, not calls (see provenance.md known issues). |
| `nf_output/networking/network.graphml` | — | 5.2 MB; consolidated node+edge+annotation+quant view, excludes singletons. |
| `nf_output/networking/network_singletons.graphml` | — | 42.3 MB; includes component -1 (unclustered) nodes. |

Bundle total on disk: ~96 MB.

## Sample-metadata column summaries (`merged_metadata.tsv`, 57 data rows)

| Column | Type | Non-null | Unique | Notes |
|--------|------|----------|--------|-------|
| sample_type | categorical | 57 | 4 | sample (50), QC_blank_extract (3), QC_blank_with_internal_standard (3), QC_blank_solvent (1) |
| host_species | categorical | 50 | 1 | sylvaticus (all animal samples) |
| tissue | categorical | 50 | 1 | fecal |
| treatment_group / treatment | str | 50 | multiple | pilot/study labels, e.g. "STP1710.7 pilot", "STP1717.1 pilot" |
| gps_lat / gps_lon | float | 0 | — | blank for all rows in this export |

## Missing data summary

| Column | Missing count | Missing % | Pattern / notes |
|--------|---------------|-----------|-----------------|
| subject_id, host_genus/species, tissue, collection_date, treatment*, tank, geo_loc_name, dates, chem_sample_type, n_pooled_biosamples | 8 (QC blank rows only) | 14% | Expected — QC blanks have no biological metadata. |
| gps_lat, gps_lon | 57 | 100% | Not populated in this export for any row. |
| animal_notes_lab | most sample rows | majority | Free-text; only populated for a subset of samples with lab notes. |

## Quality flags

- Component `-1` (unclustered/singleton features) is included in `network_singletons.graphml` but excluded from `network.graphml` — reported networking-edge counts and family sizes should always state whether singletons are included.
- Peak-area columns are raw intensities, not normalized; do not compare across samples without TIC normalization (see README_FOR_CLAUDE.md).
- No isotope-envelope data — do not attempt halogen/charge-state calls from this bundle alone.

## Notes

Row/column counts above were obtained directly from the raw files (`wc -l`, header column count) rather than a generated profiling script; re-run and update this file if the bundle is regenerated.
