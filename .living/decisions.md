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

