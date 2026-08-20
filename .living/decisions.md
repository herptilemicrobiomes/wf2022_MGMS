# Decision Log

Append-only log of non-obvious decisions and their rationale.

**Entry template:** copy from `skills/core/templates/decision-log-entry.md` (includes Context, Decision, Alternatives considered, Rationale, Consequences, Tags fields).

### [2026-08-19] Repo was not under git; initialized fresh before mycelium scaffold

**Context**: Mycelium `init` was requested on an existing project directory (`data/raw`, `data/preprocessed`, `data/metadata` already populated with a GNPS2 metabolomics bundle) that had never been git-initialized.

**Decision**: Ran `git init` (confirmed with the user first) before scaffolding, then ran the plain mycelium init (not `--restructure`, which is only a non-destructive audit stub in this plugin version) since `data/` is already a Mycelium-managed top-level prefix and the script only creates missing dirs/files without overwriting existing ones.

**Alternatives considered**:
- `init_repo.py --restructure` — rejected for the actual move step; the installed plugin version's restructure mode only prints an audit report and exits (`TODO: Implement interactive restructure workflow`), so it could not have performed a migration anyway.

**Rationale**: `create_directory_structure`/`create_manifests` use `mkdir(parents=True, exist_ok=True)` and only write files that don't already exist, so running plain init against a directory with pre-existing `data/` content is safe.

**Consequences**: Existing `data/preprocessed/` (non-canonical name; canonical is `data/processed/`) was left as-is rather than renamed — no data was moved. Future ingests should use `data/processed/` going forward; consider consolidating `data/preprocessed/` into it later if it accumulates content.

**Tags**: mycelium, setup, git, restructure

---

### [2026-08-20] Marked gnps2-f7a16270-bagel superseded rather than deleting it

**Context**: A v2 GNPS2 Everything Bagel re-run (task `ad67978e...`) arrived at `data/raw/gnps2_ad67978e_bagel/`, same workflow and MassIVE input (MSV000095549) as the existing `gnps2-f7a16270-bagel` manifest entry, but this time submitted with the hand-built sample-metadata enrichment file baked in as the job's `metadata_file`. The original bundle's raw directory (`data/raw/gnps2_f7a16270_bagel/`) was found to no longer exist on disk.

**Decision**: Added a new `gnps2-ad67978e-bagel` manifest entry as the dataset to use going forward, and changed the old entry's `status` to `superseded` (with a note that its raw path is gone) instead of deleting the old entry outright.

**Alternatives considered**:
- Delete the old manifest entry — rejected; it still documents real provenance (the hand-built `sample_metadata_animal_enriched.csv` under `data/metadata/gnps2_f7a16270_bagel/` was reused as this run's metadata input, and that lineage is worth keeping traceable).
- Overwrite the old entry in place with the new task id — rejected; the two are genuinely different GNPS2 tasks with different result bundles, and collapsing them would lose the "why did the join key data disappear" trail if `gnps2_f7a16270_bagel` is ever referenced from an old analysis.

**Rationale**: Manifest entries should be an append-only provenance record per raw-data ingestion convention; superseding (not deleting) preserves traceability for any existing references to the old task/bundle.

**Consequences**: Future work on this dataset should use `gnps2-ad67978e-bagel`/`data/raw/gnps2_ad67978e_bagel/`. Any existing analysis scripts or notes referencing `gnps2_f7a16270_bagel` raw paths will need updating (its raw files are gone; only derived metadata under `data/metadata/gnps2_f7a16270_bagel/` remains).

**Tags**: mycelium, data-ingest, gnps2, metabolomics, manifest

---

### [2026-08-20] PCoA on MS feature table uses Bray-Curtis + TIC normalization, not raw Euclidean PCA

**Context**: User asked for a PCoA of the `gnps2-ad67978e-bagel` MS1 feature-quant table (12,566 features x 57 samples) colored by `sample_type` and `treatment_group`. The peak-area columns are raw, unnormalized intensities in arbitrary units, and the feature table is sparse (many features are zero/not-detected in a given sample).

**Decision**: TIC-normalize each sample (divide by its total peak area across all features) then compute Bray-Curtis distance and run classical (Gower) PCoA, per the bundle's own `README_FOR_CLAUDE.md` guidance ("Use presence/absence, not raw Pearson, on sparse features, and TIC-normalize"). Backed the ordination with a permutation PERMANOVA (999 permutations, seed 42) rather than relying on eyeballing cluster separation.

**Alternatives considered**:
- Raw Euclidean PCA on unnormalized peak areas — rejected; would let total-intensity/injection-volume differences between samples dominate the ordination rather than compositional differences, and Euclidean distance is a poor fit for sparse, non-negative, compositional feature-abundance data.
- Log-transform + Euclidean PCA — a reasonable alternative not used here; Bray-Curtis was chosen instead as the more standard choice for compositional ecology-style feature tables (this is effectively a "metabolite community composition" ordination) and because it handles the many true zeros (not-detected features) without a log-of-zero problem.

**Rationale**: Matches the domain guidance already documented in the ingested bundle's README, and keeps QC blanks (used here as the sample_type-separation sanity check) and biological samples on a comparable footing despite very different total ion content.

**Consequences**: `treatment_group` PERMANOVA was restricted to the 50 biological samples only (QC blanks have no treatment_group and were excluded from that specific test, not from the ordination itself or the sample_type test). Result: sample_type separates strongly (pseudo-F=16.39, p=0.001); treatment_group does not (pseudo-F=0.93, p=0.543) on the full 12,566-feature table — see `analysis/pcoa-ms-feature-composition/PCOA_MS_FEATURE_COMPOSITION.md` Open Questions for caveats (unfiltered feature set may mask a real effect; tank/date confounds not checked).

**Tags**: mycelium, analysis, metabolomics, pcoa, statistics

---

### [2026-08-20] Derived sample age from metadata timeline dates; dropped controls (not blanks) for the age-gradient plot

**Context**: User asked whether a specific sample "age" could be inferred from `gnps2-ad67978e-bagel`'s metadata and, if so, to visualize the PCoA colored/shaped by it. `merged_metadata.tsv` has no direct age column, but does have `subject_id` (grouping repeat samples per animal; 19 subjects, mostly 3 timepoints each), `collection_date`, `metamorphosis_date`, and `basidiobolus_feeding_date`.

**Decision**: Derived two candidate ages — `days_post_metamorphosis` (developmental age) and `days_post_feeding` (experimental time since Basidiobolus exposure) — and used `days_post_feeding` for the requested color-gradient plot. Built that plot on a *third* ordination (QC blanks AND `control`-treatment samples dropped, n=33), not the existing no-blanks ordination, because `days_post_feeding` is only a meaningful clock for animals actually exposed to the fungus; `control` animals have a `basidiobolus_feeding_date` value in the metadata (same tank/cohort schedule) but it doesn't correspond to a real exposure event for them, so plotting them on that color scale would be misleading.

**Alternatives considered**:
- Color the existing 50-sample no-blanks ordination by `days_post_feeding` and just gray out controls — rejected; the PCoA centering itself would still be influenced by control samples whose "age" value is not biologically meaningful, muddying the ordination as well as the color scale.
- Use `days_post_metamorphosis` instead of `days_post_feeding` — not rejected, but not tried in this pass; noted as an open question since the two are correlated by construction and it's unclear which (or both) drives the pattern.

**Rationale**: Matches the same "recompute the ordination on the exact sample set you're interpreting" principle already used for the no-blanks version, and avoids showing a derived covariate for samples where it isn't defined.

**Consequences**: Found a significant correlation between `days_post_feeding` and both PC1 (Spearman rho=0.54, p=0.0012) and PC2 (rho=-0.45, p=0.0093) among the 33 treated samples — a stronger and cleaner signal than the treatment-group PERMANOVA found. Flagged as an open question that the earlier non-significant treatment-group PERMANOVA should be revisited with `days_post_feeding`/`subject_id` as a covariate, since a treatment effect could be masked by this larger time trend. Also flagged that the 33 points are repeated-measures (not independent), so the Spearman test is a first-pass signal, not a rigorous test.

**Tags**: mycelium, analysis, metabolomics, pcoa, age, derived-variable

