# Provenance: gnps2_ad67978e_bagel

## Source

**Type**: url (facility/service export)

**Origin**:
- URL: https://gnps2.org (status page: https://gnps2.org/status?task=ad67978e27274245abe5ea428c44ce09)
- Derived from: MassIVE MSV000095549 (input LC-MS/MS spectra), processed through the GNPS2 `everything_bagel_workflow` (feature finding + molecular networking + spectral library search).

**Citation / accession**: MassIVE MSV000095549; GNPS2 task `ad67978e27274245abe5ea428c44ce09`.

## Acquisition details

**Date acquired**: 2026-08-20

**Obtained by**: jasonst@ucr.edu (jstajich), via the GNPS2 Networking Packager result-bundle export ("packaged for analysis with Claude").

**Method**: Downloaded as a packaged multi-file bundle (README_FOR_CLAUDE.md + manifest.json + result tables) from the GNPS2 `/resultfile` endpoint for this task. Workflow run submitted 2026-08-19 19:36:37 PDT with `workflow_version: SERVER:2026.05.21;WORKFLOW:2026.08.13`.

**Checksum**: not recorded (see `manifest.json` in `data/raw/gnps2_ad67978e_bagel/` for per-file byte sizes as a lighter integrity check).

## Access restrictions

**Restriction level**: none

**Details**: None.

- Files over ~1 MB in `data/raw/gnps2_ad67978e_bagel/` are stored gzip-compressed (`.gz`) for git; the uncompressed originals are gitignored locally. See `GNPS2_AD67978E_BAGEL.md` in that directory for the file list and decompression notes.

## Known issues

- No MS1 isotope envelope in this export — halogen calls (M+2 pattern) and charge-state disambiguation cannot be closed from these files alone.
- No fragment-position information — hydroxyl vs. oxo (+O either way) and other regiochemistry questions need ModiFinder-style work or authentic standards, not this export.
- Representative MS2 spectra are pooled per feature (not per sample) — presence of a diagnostic ion is a property of the node, not of an individual subject. Per-subject/per-sample claims require joining `nf_output/feature_finding/feature_finding_results/aligned_features.csv` peak-area columns to `nf_output/metadata/merged_metadata.tsv` on filename; the enriched biological fields are already filled in this run (unlike the prior `gnps2-f7a16270-bagel` bundle, which needed a separate hand-built enrichment file).
- `merged_feature_library_search_results.tsv` library matches carry no confidence beyond MQScore/SharedPeaks — treat as leads and tier by the evidence hierarchy in README_FOR_CLAUDE.md (class-diagnostic ion > compound-specific fragment > tight ppm > network proximity; ppm/cosine alone is not a call).
- Peak-area columns are arbitrary intensity units (not molar concentration); cross-sample comparisons should be TIC-normalized per the README's "Cross-sample structure" guidance, and raw Pearson correlation on sparse features is discouraged in favor of presence/absence + Jaccard/hypergeometric tests.
- `gps_lat`/`gps_lon` are blank for all rows in this export.

## Contact

**Primary contact**: Jason Stajich (jasonst@ucr.edu), Stajich Lab, UC Riverside.

**Backup contact**: None.

## Version history

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-20 | Initial ingestion of task `ad67978e...` bundle — v2 re-run of the everything_bagel_workflow on MSV000095549 with enriched sample metadata submitted as the run's `metadata_file`, superseding the prior `gnps2-f7a16270-bagel` bundle (raw path no longer present on disk; that bundle's hand-built enrichment file was reused as this run's metadata input). |
