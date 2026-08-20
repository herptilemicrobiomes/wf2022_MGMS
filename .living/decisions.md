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

---

### [2026-08-20] Reverted the age-gradient PCoA to include controls, dropping only QC blanks

**Context**: The initial age-gradient plot (`pcoa_bray_curtis_treated_only_by_age.png`) dropped both QC blanks and `control`-treatment samples, reasoning that `days_post_feeding` wasn't a meaningful clock for unfed controls. The user asked to see control samples in that plot too, dropping only QC blanks.

**Decision**: Reused the existing 50-biological-sample (QC-blanks-removed) ordination — already computed for `pcoa_bray_curtis_no_blanks.png` — for the age-gradient plot instead of computing a separate 33-sample PCoA. Controls do have a `basidiobolus_feeding_date` recorded (same tank/cohort schedule) even though they weren't exposed, so `days_post_feeding` is technically defined for them; kept the output filename unchanged per the user's request (referenced by that exact name) even though "treated_only" is no longer literally accurate for its contents.

**Alternatives considered**:
- Keep both the treated-only and controls-included versions as separate plots — rejected as unrequested scope creep; the user asked to update the existing plot, not add a fourth one.
- Rename the file to something like `pcoa_bray_curtis_no_blanks_by_age.png` — rejected; the user referenced the file by its exact current name, so keeping the path stable avoids breaking that reference, at the cost of a slightly stale-sounding filename (noted in the report doc).

**Rationale**: Reusing the no-blanks ordination avoids a redundant PCoA computation and keeps the two "no-blanks" plots (by treatment_group, by age) directly comparable point-for-point.

**Consequences**: With controls included, the `days_post_feeding` vs. PC1 correlation got *stronger* (Spearman rho=0.65, p<0.0001, up from rho=0.54 on the fed-only subset) and now visibly holds across all three treatment groups equally — which changes the scientific interpretation flagged in the report: this axis is more likely a calendar-time/batch effect than a Basidiobolus-specific biological response, since it affects never-exposed controls the same way. Added this caveat to Key Findings and Open Questions in `PCOA_MS_FEATURE_COMPOSITION.md`.

**Tags**: mycelium, analysis, metabolomics, pcoa, age, confound

---

### [2026-08-20] Added a direct age-variable collinearity check rather than assuming it

**Context**: The user presumed `days_post_feeding` and `days_post_metamorphosis` (the two derived age variables from the previous PCoA work) would be correlated with each other, and asked to verify this in the labeled data rather than take it on faith.

**Decision**: Added `scripts/02_age_variable_correlation.py`, a small standalone check that plots the two variables against each other (axes labeled, colored by `treatment_group`, Pearson/Spearman in the title) and registers the correlation stats. Result: Pearson r=0.998 (p=1.6e-60) — the two are practically collinear, with one animal (`UHM102`) as a mild, explainable exception (longer-than-usual metamorphosis-to-feeding gap).

**Alternatives considered**:
- Fold this check into `01_pcoa.py` — rejected; it's a metadata-only diagnostic independent of the feature/quant table and Bray-Curtis machinery, so a separate numbered script keeps `01_pcoa.py` focused and this check independently rerunnable.
- Skip the plot and just report the correlation coefficient in prose — rejected; the user specifically asked to "see" it in a labeled plot, and the scatter also surfaces the UHM102 outlier that a bare correlation number would hide.

**Rationale**: Confirming rather than assuming this collinearity has direct interpretive consequences (see below), so it's worth a checked-in analysis artifact rather than a one-off answer in conversation.

**Consequences**: Since `days_post_feeding` and `days_post_metamorphosis` are collinear in this dataset, the PC1 correlation reported for `days_post_feeding` (rho=0.65 in the controls-included ordination) cannot be attributed to feeding exposure specifically versus developmental age versus calendar time — all three move together for these 50 samples. Updated `PCOA_MS_FEATURE_COMPOSITION.md`'s Open Questions to reflect that this ambiguity is a property of the dataset's design, not something resolvable by further analysis of this bundle alone.

**Tags**: mycelium, analysis, metabolomics, pcoa, age, collinearity

---

### [2026-08-20] Feeding-emergent feature screen: two-tier reporting (FDR-significant vs. pattern-only) instead of a single threshold

**Context**: User asked to identify features absent/low in control, absent/low early in feeding, and higher late in feeding, in either treated cohort. A per-feature Mann-Whitney U test (late vs. control+early baseline) with Benjamini-Hochberg FDR correction across all 12,566 features per group left only 1 FDR-significant feature (of 8+10=18 features matching the qualitative shape criteria) — the early/late group sizes are small (n=5-7 per cohort) and the multiple-testing burden across 12,566 features is heavy.

**Decision**: Report results at two explicit tiers rather than picking one cutoff: (1) `feeding_emergent_candidates.csv` — screening criteria AND FDR q<0.05 (currently 1 feature); (2) `feeding_emergent_pattern_leads.csv` — screening criteria only, ranked by fold change, explicitly labeled as uncorrected (currently 18 features, 1 overlapping both treated groups). The full per-feature results for all 12,566 features (pass or fail) are also saved (`feature_screen_all_results.csv`) as the audit trail.

**Alternatives considered**:
- Report only the FDR-significant list — rejected; a single significant feature is a thin result to hand back for what's clearly a real, visually confirmable pattern in several more features (see trajectory plots), and burying the leads would look like the analysis "found nothing" when it found a shape, just not enough samples to clear correction at 12,566-test scale.
- Relax the FDR threshold instead of adding a second tier — rejected; changing FDR_THRESHOLD to manufacture more "significant" hits blurs the honesty distinction the robust-analysis convention asks for. Keeping q<0.05 and being explicit about the second, uncorrected tier is more honest than moving the goalpost.
- Test only the 8+10=18 pre-screened candidates for significance (much smaller multiple-testing burden) instead of all 12,566 — rejected for the *primary* result, since testing only features that already look promising by eye is circular/selection-biased; noted in Open Questions as a legitimate, separate follow-up test now that the 18 aren't being "discovered" by that second test.

**Rationale**: Matches the repo's posture ("hypothesis generator; calibrated honesty is the whole value" — README_FOR_CLAUDE.md) and the robust-analysis convention's emphasis on reporting clean negatives/uncertain results as such rather than overclaiming.

**Consequences**: Anyone using this list must treat the pattern-leads tier as leads, not confirmed hits — flagged explicitly in the report doc and CSV column name (`matches_pattern_uncorrected`). None of the 18 have a spectral-library annotation, so even the FDR-significant one (feature 4506) is an unannotated lead pending the follow-up annotation work listed in Open Questions.

**Tags**: mycelium, analysis, metabolomics, feature-screening, multiple-testing, statistics

