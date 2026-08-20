# gnps2_ad67978e_bagel

GNPS2 Everything Bagel export, task `ad67978e27274245abe5ea428c44ce09`, packaged
2026-08-20 from https://gnps2.org (status page:
https://gnps2.org/status?task=ad67978e27274245abe5ea428c44ce09).

Full file-by-file description, join-key convention, and extensive annotation
guidance (mass conventions, diagnostic ions, artifact screens, USI spectrum
linking, formula-search discipline) live in `README_FOR_CLAUDE.md` in this
directory — read it before doing any annotation work on this bundle.

## Relationship to prior bundle

This is a **v2 re-run that supersedes `gnps2-f7a16270-bagel`** (see
`data/DATA_MANIFEST.md`; that entry's raw path no longer exists on disk).
Same workflow (`everything_bagel_workflow`) and input dataset (MassIVE
`MSV000095549`), but:

- Run description: "MSV000095549 v2 - WoodFrog fecal from feeding experiments".
- The sample metadata submitted with this run
  (`USERUPLOAD/jstajich/WF2022/WF2022_metadata_animal_enriched.csv`) is the
  same enriched metadata hand-built for the prior bundle
  (`data/metadata/gnps2_f7a16270_bagel/sample_metadata_animal_enriched.csv`),
  so `nf_output/metadata/merged_metadata.tsv` in this bundle already carries
  all enrichment columns filled — no separate join is needed for grouping.

## Storage note: gzip-compressed for git

Files over ~1 MB are stored in git as gzip-compressed `.gz` siblings (e.g.
`aligned_features.csv.gz`) rather than the raw file — compression ratios
were 4-30x for these text/XML formats (`network_singletons.graphml` 43 MB →
1.3 MB gz). The uncompressed originals are `.gitignore`d in this directory
(see `.gitignore` here) to keep repo size manageable; decompress with
`gunzip -k <file>.gz` before use, or read directly with tools that support
transparent gzip input (e.g. `pandas.read_csv(..., compression="infer")`,
`pyteomics` MGF readers that accept file-like objects via `gzip.open`).
Small files (YAML/manifest/short TSVs) are committed uncompressed as-is.

## Contents (see manifest.json for exact byte sizes)

- `submission_parameters.yaml`, `job_parameters.yaml`, `flow_filelinking.yaml` — run intent, resolved parameters, and linked input files.
- `nf_output/feature_finding/feature_finding_results/aligned_features.csv` — PRIMARY feature quant table: 12,566 features (rows) x 143 columns (m/z, RT, per-file peak areas, adduct/isotope/ISF calls, etc.). Start here for quant.
- `nf_output/feature_finding/aligned_features_filled.mgf` — gap-filled per-feature MS/MS; `SCANS` = feature/row id (join key).
- `nf_output/feature_library_search/merged_feature_library_search_results.tsv` — 265 spectral-library hits keyed on feature id.
- `nf_output/networking/filtered_pairs.tsv` — 2,014 filtered molecular-networking edges (`CLUSTERID1`/`CLUSTERID2` = feature ids).
- `nf_output/networking/network.graphml` / `network_singletons.graphml` — consolidated node+edge+annotation+quant view; read this first per the README.
- `nf_output/metadata/merged_metadata.tsv` — 58 rows (50 samples + 8 QC blanks), fully enriched (species, tissue, tank, dates, treatment, etc.) for *Lithobates sylvaticus* fecal samples from feeding-experiment tanks (STP1710.7 / STP1717.1 pilot, etc.).
- `requirements.txt` — pip packages (`massql`, `pyteomics`, `rdkit`, `networkx`, `pandas`) for local analysis of this bundle.

## Provenance

- Source: GNPS2 Everything Bagel workflow (apps.gnps2.org), task `ad67978e27274245abe5ea428c44ce09`.
- Input dataset: MassIVE `MSV000095549`.
- Run params: `pm_tolerance` 0.05, `fragment_tolerance` 0.05, `library_min_matched_peaks` 6, `mode: fbmn`.
- Packaged: 2026-08-20T03:23:45.845Z.
- Retrieved by: jasonst@ucr.edu, 2026-08-20.
