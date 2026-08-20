# SIRIUS Annotation

## Purpose

Link more structural/compound-class information to `gnps2-ad67978e-bagel`
features than the GNPS spectral-library search alone provides, using SIRIUS
6.3.12 (formula prediction, CSI:FingerID structure search, CANOPUS compound
class prediction) — for (a) the small set of "interesting" features flagged
by the `feeding-emergent-features` screen, and (b) the full set of features
with real MS/MS spectra, as a general-purpose annotation resource for future
work on this bundle.

## Status

**Status**: active — interesting-features run complete; full run
**submitted and running unattended** as of 2026-08-20:
- Array job `27671478` (`--array=0-176%1`, strictly serial): runs
  `scripts/run_sirius_array.sbatch shards_full sirius_results_full` over
  all 177 shards.
- Merge/import job `27671479`, chained with
  `--dependency=afterok:27671478` (waits for **all** array tasks to
  succeed): runs `scripts/run_merge_import_full.sbatch`, which calls
  `merge_sirius_shards.py` + `import_sirius_annotations.py` and writes
  `FULL_RUN_COMPLETE.marker` on success — no manual/interactive step
  needed after the array finishes.
- Job ids are also recorded in `.full_run_array_jobid` /
  `.full_run_merge_jobid` in this directory.
- **To check status in a future session**: `squeue -j 27671478,27671479`
  (or `sacct -j 27671478,27671479 --format=JobID,State,ExitCode,Elapsed`
  if no longer in the queue). If `FULL_RUN_COMPLETE.marker` exists,
  `sirius_annotations.tsv` already has the full-run results merged in
  (accumulated alongside the interesting-run results, per
  `import_sirius_annotations.py`'s merge-not-overwrite behavior) — the
  remaining work is updating this doc's Key Findings with the real
  numbers/hit-rate and reviewing `sirius_annotations.tsv` for anything
  interesting, not re-running the pipeline.

## Datasets

- `gnps2-ad67978e-bagel` (`data/DATA_MANIFEST.md`) — `aligned_features.csv.gz`
  (feature table, for target selection) and `aligned_features_filled.mgf.gz`
  (per-feature MS/MS, SIRIUS input).

## Parent Analyses

- Parent: `feeding-emergent-features` — the "interesting" target set is
  exactly that analysis's `feeding_emergent_candidates.csv` +
  `feeding_emergent_pattern_leads.csv` feature ids (17 unique features).
- Framework adapted from two sibling projects' SIRIUS pipelines:
  `/bigdata/stajichlab/shared/projects/Chytrid/Bd_massspec/Batrachochytrium_MS/analysis/sirius_annotation/`
  and
  `/bigdata/stajichlab/shared/projects/Rhodotorula/Rhodotorula_Metabolites/Rhodotorula_pheno_MS/analysis/sirius_annotation/`
  (target selection / MGF export / shard / merge / import script pattern,
  the shared Singularity container, and the SIRIUS command chain).

## Method

1. **SIRIUS itself**: shared Singularity container
   `/bigdata/stajichlab/shared/singularity/sirius-6.3.12-linux-x64.sif`
   (same image used by both sibling projects). Command chain per shard
   (`scripts/run_sirius_shard.sh`):
   `formula --ppm-max 15 --ppm-max-ms2 15 --candidates 10 → fingerprint →
   canopus → structures → write-summaries`. `ZODIAC` deliberately excluded
   (dataset-wide tool; sharding would change its results).
   `-XX:AOTMode=off` works around a SIGILL on some cluster nodes.
2. **Critical constraint carried over from both sibling projects: only one
   `sirius` process may run project-wide (across ALL of this user's
   projects) at a time** — the login/refresh-token file at
   `~/.sirius-6.3/` is shared and not concurrency-safe. Every shard run
   checks `sirius login --show` first and fails loudly if login is dead.
   Before submitting any SIRIUS job here, check `squeue -u jstajich` for
   jobs from the sibling projects (or any other job that might be running
   `run_sirius_shard.sh`) and never run concurrently with them.
3. **Target selection** (`scripts/select_targets.py`):
   - `--mode interesting`: the union of `feeding-emergent-features`'s
     candidates + pattern leads (17 feature ids).
   - `--mode full`: every feature with `has_ms2==True` and `charge==1` in
     `aligned_features.csv` (3,530 of 12,566 features — the rest either
     have no real MS2 spectrum in this export, or a multiply-charged
     precursor SIRIUS isn't set up to handle here).
4. **MGF export** (`scripts/export_targets_mgf.py`): pulls each target's
   block from `aligned_features_filled.mgf.gz` keyed on `SCANS==feature_id`,
   drops (reporting each) blocks with `CHARGE` ≠ `1+`, `PEPMASS`≤0, or no
   peak with intensity>0.
   - **Key finding from this step**: 14 of the 17 "interesting" features
     have `has_ms2==False` — i.e. they were quantified (real peak areas
     across samples) but the feature-finding step assigned them the
     dataset's gap-filled placeholder spectrum (`CHARGE=0`, no real
     fragmentation data), not a genuine MS/MS scan. **SIRIUS cannot
     formula/structure-annotate a feature with no real MS2** — this is a
     hard data limitation, not a pipeline bug. Only 3 of the 17
     "interesting" features (`3345`, `7757`, `11360`) have real MS/MS and
     were actually submitted to SIRIUS.
5. **Sharding** (`scripts/shard_mgf.py`): round-robin split into
   `spectra-per-shard`-sized shards (20/shard used here) for
   checkpointing/resumability — sharding does not speed up SIRIUS itself,
   since only one process may run at a time (see constraint above).
6. **Execution**: `scripts/run_sirius_serial.sbatch <shard_dir> <results_dir>`
   loops all shards in one job (used for the small interesting-set run);
   `scripts/run_sirius_array.sbatch <shard_dir> <results_dir>` runs one
   shard per array task with `%1` (strictly serial — the array only exists
   for per-shard resumability, not parallelism) for the full run.
7. **Merge + import**: `scripts/merge_sirius_shards.py` concatenates each
   shard's `write-summaries` TSVs; `scripts/import_sirius_annotations.py`
   distills the merged tables into one row per `feature_id` in
   `sirius_annotations.tsv` at this analysis's root, accumulating across
   runs (structure hit beats formula-only; higher confidence wins ties).

## Key Findings

- Only 3 of the 17 "interesting" (feeding-emergent) candidate/lead features
  have real MS/MS spectra available (`3345`, `7757`, `11360`); the other 14
  cannot be SIRIUS-annotated from this export at all — see Method step 4.
  This should be flagged wherever the feeding-emergent candidate list is
  used downstream: most of those leads are, and will likely remain,
  structurally uncharacterized from this dataset alone.
- **Interesting-features SIRIUS run (job 27661542, 5m21s for 3 spectra)
  results** — treat all three as unconfirmed leads, not calls, per the
  README's evidence hierarchy (mass/formula alone is not evidence; no
  diagnostic-ion or spectral-library cross-check was done here):
  - **Feature `3345`**: SIRIUS could not call a molecular formula at all
    (no row in `formula_identifications.tsv`) — likely too few/weak
    fragment peaks in this feature's representative spectrum. No further
    annotation possible from this run.
  - **Feature `7757`**: formula `C27H47N5O6`, adduct `[M+H]+`; one
    structure hit — a large cyclic-peptide-like/protease-inhibitor-style
    molecule (SMILES in `sirius_annotations.tsv`) — but at
    **ConfidenceScoreExact = 0.09**, effectively no confidence (SIRIUS's
    own exact-confidence scale runs roughly 0-1 with values well below
    ~0.5 not meant to be trusted as a call). CANOPUS class: "Amino acids
    and Peptides" / "Cyclic peptides" (NPClassifier), "Carboxylic acids
    and derivatives" (ClassyFire) — the class-level call is more useful
    here than the specific structure guess.
  - **Feature `11360`**: formula only, `C62H101N11O15`, `[M+H]+` — no
    structure hit. This is an unusually large formula (62 carbons, 11
    nitrogens) for a single small-molecule metabolite; worth sanity
    checking against the feature's actual `parent_mass`/`adduct` call in
    `aligned_features.csv` before trusting it (large multi-nitrogen
    formulas are also consistent with SIRIUS mis-resolving a
    low-fragment-count spectrum — see the formula-search-discipline
    caution in `README_FOR_CLAUDE.md`).
  - **Bottom line: none of the 3 annotatable "interesting" features got a
    trustworthy structure ID from this pass.** The feeding-emergent
    candidate list remains chemically uncharacterized; SIRIUS on the
    existing MS/MS didn't change that for this particular set (small
    sample, weak spectra). A full run may still surface better-supported
    hits among other, non-"interesting" features, or future re-acquisition
    with deeper MS/MS would be needed for these specific 3.
- Full run (3,530 features, 177 shards of 20): prepared, **not submitted**
  — see Open Questions for the runtime estimate and the ask for
  confirmation before committing cluster time.

## Open Questions

- **Full run submitted 2026-08-20** (array `27671478` + dependent merge
  `27671479`, see Status) after user confirmation. Runtime estimate from
  the observed rate on the interesting-set run (5m21s for 3 spectra in
  one shard, ~1.8 min/spectrum including per-shard JVM startup): roughly
  15-20 min/shard once startup overhead amortizes over 20 spectra/shard,
  so **~2-3 days of wall clock for 177 shards run strictly serially**
  (one `sirius` process project-wide at a time). `squeue -u jstajich`
  showed no other sirius jobs running immediately before submission. If
  a sibling project's SIRIUS job gets submitted while this one is
  running, both will fail at their next `sirius login` call (shared
  token) — check `squeue -u jstajich` and job logs for login errors if
  either job fails partway through.
  - Given the interesting-set pilot found no usable hit (0/3), the full
    run's actual value depends on whether the broader feature set
    (spanning many more compound classes/spectral qualities) fares
    better — worth a skeptical read of the hit-rate once it completes,
    not an assumption that "more features run = more real answers."
- The 14 "interesting" features with no real MS2 need an alternative
  annotation path if they're to be identified at all: accurate-mass search
  against a compound library (per README_FOR_CLAUDE.md's "absolute-mass
  search" and "compact library" guidance), or `network.graphml` component
  propagation from an annotated neighbor — not attempted here.
- `import_sirius_annotations.py`'s column-name detection
  (`FEATURE_ID_COLUMN_CANDIDATES`, `find_column_containing`) was written
  defensively against uncertainty about exact SIRIUS 6.3.12
  `write-summaries` header names; verify/correct against the real output
  the first time it's run (see script docstring).

## Reproducibility

```bash
cd analysis/sirius_annotation

# targeted run (small; already executed for this analysis)
python3 scripts/select_targets.py --mode interesting
python3 scripts/export_targets_mgf.py --mode interesting
python3 scripts/shard_mgf.py sirius_targets_interesting.mgf --out-dir shards_interesting --spectra-per-shard 20
sbatch scripts/run_sirius_serial.sbatch shards_interesting sirius_results_interesting
# after the job completes:
python3 scripts/merge_sirius_shards.py --shard-root sirius_results_interesting --out-dir sirius_results_interesting/merged
python3 scripts/import_sirius_annotations.py --merged-dir sirius_results_interesting/merged --label interesting_2026-08-20

# full run (large; prepared but not submitted -- see Open Questions)
python3 scripts/select_targets.py --mode full
python3 scripts/export_targets_mgf.py --mode full
python3 scripts/shard_mgf.py sirius_targets_full.mgf --out-dir shards_full --spectra-per-shard 20
sbatch --array=0-176%1 scripts/run_sirius_array.sbatch shards_full sirius_results_full
# after all array tasks complete:
python3 scripts/merge_sirius_shards.py --shard-root sirius_results_full --out-dir sirius_results_full/merged
python3 scripts/import_sirius_annotations.py --merged-dir sirius_results_full/merged --label full_2026-08-20
```

Requires `module load singularity` and the shared `.sif` at
`/bigdata/stajichlab/shared/singularity/sirius-6.3.12-linux-x64.sif`
(group-readable, `stajichlab`). No project-specific SIRIUS license setup
needed — uses the already-authenticated shared login
(`~/.sirius-6.3/`, academic subscription).

## Outputs

| File | Description |
|------|-------------|
| `sirius_targets_<mode>.csv` | Selected target feature ids + mz/rt/source columns. |
| `sirius_targets_<mode>.mgf` | Exported spectra for those targets (post drop-filtering). |
| `shards_<mode>/shard_NNN.mgf` | Round-robin shards (gitignored, transient). |
| `sirius_results_<mode>/shard_NNN.sirius/` | Per-shard SIRIUS project space (gitignored, large binary). |
| `sirius_results_<mode>/merged/*.tsv` | Concatenated write-summaries tables across all shards. |
| `sirius_annotations.tsv` | Final one-row-per-feature accumulated annotation table (formula, adduct, structure name/SMILES/confidence, CANOPUS NPC pathway/class, ClassyFire class, source_run). |
