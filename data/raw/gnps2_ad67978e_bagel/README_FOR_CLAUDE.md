# GNPS2 Everything Bagel — result bundle

This folder is a packaged export of a GNPS2 Everything Bagel task, assembled by
the GNPS2 Networking Packager (apps.gnps2.org) for analysis with Claude. It
contains the result tables and network files listed below. Read this file
first, then `manifest.json` for the exact byte sizes.

- **Task:** `ad67978e27274245abe5ea428c44ce09`
- **Host:** https://gnps2.org
- **Status page:** https://gnps2.org/status?task=ad67978e27274245abe5ea428c44ce09
- **Workflow:** `everything_bagel_workflow`
- **Packaged:** 2026-08-20T03:23:45.845Z

## What Everything Bagel does

A combined workflow: it runs feature finding (alignment + gap-filling) on the raw files, then molecular networking and (optionally) spectral-library search on the resulting features. It is modular, so a given run may skip networking or library steps — files not produced by this run show as 'not found'.

## The join key

The join key is the **feature / row id**:
- `feature_finding_results/aligned_features.csv` — one row per feature (the row id), x samples.
- `aligned_features_filled.mgf` — each spectrum's `SCANS` = feature/row id.
- `filtered_pairs.tsv` — edges, `CLUSTERID1`/`CLUSTERID2` = feature ids.
- `merged_feature_library_search_results.tsv` — library hits keyed on the feature id (when present).

## Run parameters (from submission_parameters.yaml)

- `pm_tolerance`: 0.05
- `fragment_tolerance`: 0.05
- `library_min_matched_peaks`: 6
- `input_spectra`: DATASETLOCATION/MassIVE/MSV000095549

## Files in this bundle

### `submission_parameters.yaml`  _(820 B)_

Form values exactly as the user submitted them (workflow name, tolerances, dataset selection). The best record of intent.

### `job_parameters.yaml`  _(1.2 KB)_

Fully resolved Nextflow parameters the run actually used.

### `flow_filelinking.yaml`  _(7.0 KB)_

Which concrete input spectrum files were linked into the run.

### `nf_output/file_list/input_spectra_list.tsv`  _(10.3 KB)_

One row per input spectrum file linked into the run.

### `nf_output/feature_finding/feature_finding_results/aligned_features.csv`  _(6.6 MB)_

PRIMARY feature quantification table: aligned features (rows, keyed by feature/row id) x samples, with m/z, RT, and per-file peak areas. Start here for quant.

### `nf_output/feature_finding/aligned_features_filled.mgf`  _(5.4 MB)_

Gap-filled aligned-feature MS/MS, one spectrum per feature; SCANS = feature/row id. Primary spectra for fragment-level work.

### `nf_output/feature_library_search/merged_feature_library_search_results.tsv`  _(152.5 KB)_

Spectral-library matches for features (may be absent if this run skipped library search).

### `nf_output/networking/filtered_pairs.tsv`  _(53.0 KB)_

Filtered molecular-networking edges between features. Columns: CLUSTERID1, CLUSTERID2 (= feature ids), DeltaMZ, Cosine, MatchedPeaks.

### `nf_output/metadata/merged_metadata.tsv`  _(13.8 KB)_

Merged sample metadata / grouping (may be absent if none was supplied).

### `nf_output/networking/network.graphml`  _(5.2 MB)_

The molecular network as GraphML, if this run produced one (Cytoscape-ready).

### `nf_output/networking/network_singletons.graphml`  _(42.3 MB)_

Network including singleton features, if produced.

### `nf_output/feature_finding/feature_finding_results/aligned_features.mgf`  _(4.7 MB)_

Aligned-feature MS/MS before gap-filling.

### `nf_output/feature_finding/feature_finding_results/aligned_features_ms2.csv`  _(2.0 MB)_

Per-feature MS2 summary (precursor, best-scan info).

### `nf_output/feature_finding/feature_finding_results/aligned_feature_ms2_scans.tsv`  _(5.1 MB)_

Maps each feature to the individual MS2 scans that contributed to it.

### `nf_output/feature_finding/feature_finding_results/aligned_rt_bounds.csv`  _(12.1 MB)_

Per-feature RT integration bounds per file (large).

### `nf_output/networking/merged_pairs.tsv`  _(6.2 MB)_

ALL raw pairwise alignments before topology filtering. filtered_pairs.tsv is the filtered network you usually want instead.

## Annotating unannotated nodes — hard-won guidance

_Distilled from real annotation sessions (acylcarnitine, bile-acid, and metformin-conjugate networks); the reasoning generalizes to any conjugate/derivative class._

### Get the mass convention right first

In positive mode, search the **observed cation mass**, not the neutral/zwitterion — the single most expensive silent bug. Every target otherwise lands ~1.007 Da low and real hits vanish with no error.
- Carnitine: zwitterion C7H15NO3 = 161.1052; observed cation C7H16NO3+ = **162.1125**.
- Conjugate target m/z = backbone_cation + acid − H2O.
- **Calibrate against a known-true structure first**: compute its SMILES m/z (RDKit) and confirm it reproduces the observed value to <5 ppm before trusting any search.
- Zero hits for something the user says they have quantified ⇒ suspect the mass constant, not the user.

### Evidence hierarchy — mass accuracy is not evidence

Plenty of pure coincidences sit at 0 ppm. Rank every candidate by what it actually has:
1. **Class-diagnostic ion** — proves the backbone.
2. **Compound-specific fragment** — proves the acyl/substituent; this is what turns a lead into a call.
3. **Tight ppm** — necessary, not sufficient.
4. **Network proximity** — weakest.

(1)+(2)+(3) = a call. (1)+(3) = strong. (3) alone = a coin flip.

### Class-diagnostic ions & the bulky-substituent exception

Fragment-level work uses the consensus MGF (`specs_ms.mgf`; each spectrum's SCANS = cluster index — verify once by joining a couple of PEPMASS values to the node table).
- **Acylcarnitine:** 85.0284 (most universal), 60.0808, 144.1019, TMA neutral loss 59.0735.
- **Bile acids** carry no permanent charge — use conjugate ions instead: glycine 76.0394, taurine 126.0225, plus the sequential water-loss ladder (−18.011 × n, where n = hydroxyl count, distinguishing mono/di/trihydroxy).

**Bulky-substituent exception:** a large acyl group suppresses the class ion (ibuprofen-carnitine shows no 85.0284 at all; it fragments via TMA loss then decarboxylation) yet is a confirmed compound. For large |Δmass| (≳150 Da), accept a secondary diagnostic ion alone — but spot-check, because some large-Δ 'no class ion' nodes belong to an entirely different compound class. It's a tendency, not a rule.

### Show the user the spectrum — link out via the metabolomics-USI resolver

Don't just describe a spectrum in prose — **hand the user a link (or an inline image) they can open**. The lab's USI resolver renders any node's MS/MS on demand, pulling the spectrum live from this task on GNPS2, so it works whether or not `nf_output/feature_finding/aligned_features_filled.mgf` was included in the zip.

**Build the USI** for a node from its join key (the `cluster index` / feature id):

```
mzspec:GNPS2:TASK-ad67978e27274245abe5ea428c44ce09-nf_output/feature_finding/aligned_features_filled.mgf:scan:<NODE>
```

where `<NODE>` is the node's join-key value (its `SCANS` in the MGF). Then:
- **Inline image** (embed directly in your reply so the user sees it):
  `![node <NODE>](https://metabolomics-usi.gnps2.org/png/?usi1=mzspec:GNPS2:TASK-ad67978e27274245abe5ea428c44ce09-nf_output/feature_finding/aligned_features_filled.mgf:scan:<NODE>)`
- **Interactive viewer** (zoom / read off peaks): `https://metabolomics-usi.gnps2.org/spectrum/?usi1=mzspec:GNPS2:TASK-ad67978e27274245abe5ea428c44ce09-nf_output/feature_finding/aligned_features_filled.mgf:scan:<NODE>`
- **Peaks as data** to reason over, or to sanity-check the USI before you link it: `https://metabolomics-usi.gnps2.org/json/?usi1=mzspec:GNPS2:TASK-ad67978e27274245abe5ea428c44ce09-nf_output/feature_finding/aligned_features_filled.mgf:scan:<NODE>` (a 200 with a `peaks` array = valid; validate before handing the user a render link).

**Mirror a node against its library hit** — the canonical 'is this annotation real?' evidence image. Take the `SpectrumID` (a `CCMSLIB...` accession) from `merged_results_with_gnps.tsv` for that node and mirror the two spectra head-to-tail:

```
https://metabolomics-usi.gnps2.org/png/mirror/?usi1=mzspec:GNPS2:TASK-ad67978e27274245abe5ea428c44ce09-nf_output/feature_finding/aligned_features_filled.mgf:scan:<NODE>&usi2=mzspec:GNPS:GNPS-LIBRARY:accession:<SpectrumID>
```

- Interactive mirror: `https://metabolomics-usi.gnps2.org/mirror/?usi1=<node USI>&usi2=<library USI>`.
- **Gotcha:** the mirror *image* lives at `/png/mirror/` (and `/svg/mirror/`). A plain `/png/?usi1=&usi2=` silently ignores `usi2` and renders only the node — it will not mirror.

Reach for this whenever you surface a node the user might want to eyeball: a proposed annotation, a diagnostic-ion call, a suspected artifact, or the two ends of a delta-mass edge. A rendered spectrum (and a mirror against the library) is the fastest way to let them confirm your reasoning.

_(Library-USI forms for non-GNPS references: MassBank `mzspec:MASSBANK::accession:<id>` — note the empty middle field. If this task lives only on `beta.gnps2.org`, the resolver may not find it under the `GNPS2` provider; fall back to the interactive viewer on the matching host.)_

### Run the artifact screens FIRST

Screen the whole dataset for these before annotating — each rides into a family on a coincidental cosine edge:
- **PEG / polymer:** repeating 44.026 Da ladder, base peak 89.0597, secondary 133.0857, and zero class-diagnostic ions. Re-check already-confirmed hits against the removal list so nothing real gets pulled.
- **Chimeric / co-isolated spectra:** two distinct masses sitting on the assigned precursor. The class ion may belong to the co-isolate, so the delta is uninterpretable — label 'real signal, relationship uninterpretable' rather than guessing a structure.
- **Adduct pairs:** two nodes ~21.982 Da apart with near-identical fragments are Na/H adducts of one compound, not a structural relationship.
- **Mass defect as a cheap outlier detector:** ordinary CHNO deltas cluster ~−0.1 to +0.2; outside that is usually artifact. A delta that fits *no* formula even at 10 mDa is itself diagnostic.

### What this export cannot answer

State the limits early rather than dressing a cluster-level result up as sample-level:
- **Per-file abundance IS in this bundle** — the feature/quant table is features (nodes) × files; join it to `merged_metadata.tsv` for grouping. But the representative spectrum is pooled and carries no provenance, so presence of a diagnostic ion is a property of the *node*, never of a subject. Per-subject work still needs sample metadata mapping files → subjects.
- **No MS1 isotope envelope** ⇒ halogen calls (M+2 ≈ 32% for one Cl, ≈ 98% for one Br) and charge-state disambiguation cannot be closed from this export.
- **No fragment-position information** ⇒ hydroxyl vs oxo is +O either way; regiochemistry needs ModiFinder-style work or authentic standards.

If the user asks for one of these, request the specific missing file instead of faking it.

### Propagation vs. absolute-mass search — do both

- **Component −1 is the singleton / unclustered bucket** (often 30–40% of nodes). No edges ⇒ no propagation possible. Exclude it explicitly and say so.
- **Delta-mass propagation:** walk ≤5 hops from an annotated anchor within a component and explain the cumulative Δ. This extends existing annotations only, and only reaches families that already had one.
- **Also run an absolute-mass search across ALL nodes** against a compound library — it finds whole series propagation never touches.
- **Network tiers only weakly predict MS2 support** (~60% diagnostic-ion support in the top tier vs ~38% in the bottom). Re-tier on fragment evidence the moment the MGF is in hand, and downgrade freely.

### Annotate by anchor-and-propagate, and reuse prior lists

The most reliable naming workflow, in order:
1. **Find anchors:** search the graphml / node table for nodes that already carry a library annotation (keyword-match a drug or class name). These named nodes are your anchors.
2. **Propagate within the component:** every node sharing an anchor's connected component is a candidate member — confirm each carries the class-diagnostic ion before accepting it. A single anchored component often turns out to be a near-complete homologous family.
3. **Mass-ladder the members:** name unnamed members by the building-block relationship (e.g. parent + carbonyl − H2O for a condensation series), checked against the observed m/z.
4. **Reuse prior annotation lists across datasets:** cross-match a compound list identified in a *previous* network against this one by accurate mass (≤0.02 Da). Formula-only leads here often resolve to a real name from the other network — new information, essentially free.
Tier the result explicitly: library-verified (1) > network-propagated-from-anchor (2) > diagnostic-ion-positive but unanchored (3).

### Derive the class fingerprint; beware isobaric fragments

- **Don't trust a single diagnostic ion — derive the whole fingerprint.** Rank every shared low-mass peak across the *confirmed* members (anchored + library) by prevalence and mean intensity; the near-ubiquitous ones are the diagnostic set. This routinely surfaces ions a first pass missed (for metformin conjugates the core 113.0822 plus a 71.0604 / 68.0244 / 96.0557 sequential-NH3-loss ladder, and 130.1088 = intact parent regenerated by full retro-condensation).
- **Score candidates by how many diagnostic ions they carry** (e.g. 'k of 8') and sort by it — a candidate resting on the one primary ion alone is the weakest lead.
- **A single-ion filter over-collects.** Screening on one core ion returned 430+ hits, but two large unrelated families shared an *isobaric* ion that was not the true core fragment. Exclude them with the anchor/library sanity check — this isobaric-fragment trap recurs across datasets.

### Homologous series & chromatography as independent checks

- **Edge delta-masses reveal real families.** Within a component, the internal-edge deltamz of a genuine homologous series clusters at chemically meaningful steps: ±14.016 (CH2), ±28.031 (2×CH2), ±2.016 (H2, saturation/desaturation), ±26.016 (C2H2). That pattern is independent evidence the family is real, not a clustering artifact.
- **RT should track hydrophobicity.** On reversed phase, shorter/more-polar members elute earlier and longer/sterol members later; a monotonic RT-vs-chain-length trend reinforces the series, and local inversions between near-isobaric isomers are expected noise.
- **A logP-vs-RT plot** of the named members is a cheap misassignment screen: a predicted-logP outlier that breaks the RT trend flags a wrong call.

### Adducts, in-source fragments, and mass QC

- **Do not assume [M+H]+.** Pull the real adduct / parent_mass from the feature table before computing neutral mass — a large minority of features are Na/K/NH4 adducts or water-loss species, and assuming protonation silently corrupts every downstream formula and 'duplicate' call.
- **Test an [M+NH4]+ hypothesis** for anything that won't resolve as stated; a block of features re-resolving only under ammonium usually means the adduct-caller mislabeled them.
- **In-source fragments masquerade as small molecules.** If the table has an in-source-fragment parent column (e.g. is_isf_parent_id), a node whose parent traces to a much larger compound is an artifact riding the component, not a real small feature.
- **Verify each node's ppm even inside an anchor's own component.** Small non-specific fragments (immonium-type 60–85 ions) make unrelated compounds co-cluster: a 'parent-drug' component was 14 of 15 nodes wrong by tens-to-thousands of ppm, only the library standard correct. Component membership is a lead, never proof of identity.
- **Treat >5 ppm as incorrect, and use a ppm-scaled tolerance** not a fixed-Da one (a 6 mDa window is generous at 130 Da but far too loose at 500 Da). Cascade the formula search simplest-first (CHO → +N → +S/P → halogen); the enlarged heteroatom space over-fits above ~300 Da, so a clean sub-5 ppm CHO fit beats a mathematically-closer heteroatom fit almost every time.

### Cross-sample structure: co-occurrence, confounds, phenotypes

With the feature tables (nodes × files) and enough samples, an orthogonal evidence axis opens up:
- **Presence/absence co-occurrence** (Jaccard + hypergeometric) computed *across different network components* is independent of MS2 similarity — compounds that always appear in the same samples despite sharing no spectral edge point to a shared upstream driver.
- **Control the obvious confound before claiming biology.** In one cohort overall richness tracked drug dose (mass action drives every condensation at once); only after regressing out dose (or within a matched-dose stratum) does a residual subject-level phenotype count as real. In PCA this is one axis correlated with the confound and a second composition axis that is not — the latter is where a real diet/microbiome subgroup lives.
- **Use presence/absence, not raw Pearson, on sparse features, and TIC-normalize** — two features can correlate merely because both track injection intensity.
- **Bucket unknown attachments by plausible origin** — host primary metabolism, gut-microbial, diet, plant/phytochemical, drug/excipient, oxidative-stress/lipid-peroxidation, xenobiotic/environmental — as *hypotheses to test against metadata*, never proof from mass alone. An S/P/halogen-containing 'unknown' is more often a known xenobiotic than novel endogenous chemistry.

### Formula-search discipline

Unconstrained CHNOPS+halogen brute force **over-fits catastrophically above ~300 Da** — it will happily 'explain' any delta with something like C16H3NO2FCl. That is numerology.
- Restrict to chemically realistic single events: H→F/Cl/Br, OH→Cl/Br, −CF3, −CCl3, gem-dihalide. Filter by RDBE plausibility.
- Halogens cannot be confirmed without the MS1 isotope envelope (absent here).
- A compact library (~40 acids — phenolics, indoles, benzoates, bile acids, NSAIDs, TCA/dicarboxylic series — crossed with ~8 modifiers: ±OH, ±H2, +SO3, +GlcA, +OCH3, +Gly) covers a few hundred targets without the combinatorial blow-up.

### Isobaric traps — flag, don't silently pick

Name the ambiguity explicitly; never pick the more interesting isomer silently, especially where the choice has clinical or legal weight:
- caffeate / 4-hydroxyphenylpyruvate · coumarate / phenylpyruvate · ascorbate / glucuronate · succinyl- / methylmalonyl- · isovalerate / valerate · most bile-acid stereoisomer sets (CA/allo-CA/hyo-CA; DCA/CDCA/UDCA/HDCA).
- **GHB vs 3-hydroxybutyrate:** base rates strongly favor the endogenous ketone body — state that, do not assume it silently.

### QC & reporting conventions

- **QC plot:** predicted mass vs observed ppm error, colored by diagnostic-ion support. Supported points cluster tight around 0; unsupported scatter to ±25 ppm — the clearest demonstration that fragments, not mass, do the discriminating. A consistent small offset (mean ~−2 ppm, ~3 ppm spread) is systematic calibration bias, which is reassuring.
- **Tier everything 1–4 and define the tiers in-file.** Tier 4 must be labeled 'unresolved, not disproven' or it reads as rejected.
- Report per candidate: molecular formula, calc [M]+, observed m/z, ppm error, each diagnostic-ion relative intensity, component, RT, and the rationale. Use lipid notation where it applies (CAR n:y;Oz for acylcarnitines, DCA n:y for diacids); call out branched/tricarboxylic species separately.
- Name the near-miss ppm casualties separately from coincidental far-out matches — different categories.

### Start from the graphml — it already joins everything together

`network.graphml` is the **consolidated view of the whole run** — reach for it before hand-joining the separate tables. Every node carries *all* of its node-table attributes (parent mass, RT, `Compound_Name`/library annotation, `component`, and the per-group abundance columns), and every edge carries its `Cosine` and `DeltaMZ`. Loading this one file gives you the node table, the edges, the annotations, the molecular-family grouping, and the per-group quant already joined on the cluster index — no manual merge across files, and no chance of mis-keying the join.

- **Molecular families / groups are built in.** The `component` attribute on each node is its molecular-family id; `networkx.connected_components(G)` recovers the same grouping from the edges, and per-group abundance columns ride on the nodes, so group-vs-group comparisons come straight off the graph.
- **Load it in one line:** `import networkx as nx; G = nx.read_graphml('network.graphml')` — then `G.nodes[n]` is the full attribute dict for node `n` (the cluster index / feature id), and `G.edges(data=True)` gives the cosine/DeltaMZ on every link.
- **Visual work:** it opens directly in Cytoscape, which is the fastest way to eyeball a family before drilling into individual nodes.
- **Singletons:** `network.graphml` excludes unclustered nodes (component -1). Use `network_singletons.graphml` when you need those too.

### Local tooling — pip-installable packages to run on this bundle

You can analyze these files directly with a few small Python packages — install them and run against the bundle rather than eyeballing tables. A **`requirements.txt` ships in this bundle**; install everything up front (Python 3.8+; use a fresh virtualenv if you like):

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Then, per tool:

- **`massql`** (`pip install massql`) — query the consensus/feature MS/MS by fragment, neutral loss, or precursor, the same language as the GNPS2 web form below but on the local MGF:

  ```
  python -m massql.msql_cmd nf_output/feature_finding/aligned_features_filled.mgf \
    "QUERY scaninfo(MS2DATA) WHERE MS2PROD=85.0284:TOLERANCEMZ=0.01" \
    --output_file hits.tsv
  ```

  Each hit's `scan` **is the node's join key** (SCANS = cluster index / feature id), so results join straight back to the node table — screen every node for a diagnostic ion in one pass. Without `--output_file` it only prints a count and writes nothing.
- **`pyteomics`** (`pip install pyteomics`) — plain MGF/mzML parsing when you just want peaks and precursors as arrays.
- **`rdkit`** (`pip install rdkit`) — SMILES → molecular formula and exact monoisotopic mass; use it to do the mass-convention calibration this README keeps insisting on before trusting any m/z search.
- **`networkx`** (`pip install networkx`) — `read_graphml('network.graphml')` to traverse components, find an annotated anchor's neighbors, and walk delta-mass propagation programmatically.

### MassQL fallback (precursor-level only)

When only precursor-level files are available, hand the user a query to run in GNPS2 rather than stopping:

```
QUERY scaninfo(MS2DATA)
WHERE MS2PROD=85.0284:TOLERANCEMZ=0.01
AND MS2PROD=144.1019:TOLERANCEMZ=0.01
AND MS2NL=59.0735:TOLERANCEMZ=0.01
```

Drop to a single required ion (the most universal class ion) for a looser first pass.

### Posture

This work is a **hypothesis generator**; calibrated honesty is the whole value.
- Report clean negatives as negatives (statins, food dyes, amphetamines all coming back empty was useful).
- When the user corrects a result, look for the bug rather than defending the output — the arithmetic is usually wrong before the user is.
- Flag ambiguity; do not launder a guess into a call.

## Suggested things to ask Claude

- Summarize the largest molecular families (components) and their annotations.
- List confidently library-annotated nodes (high `MQScore`, many `SharedPeaks`)
  and the compound classes present.
- For a given `component`, tabulate its nodes, parent masses, and the
  `DeltaMZ` values on its edges to propose modifications/analogs.
- Cross the feature/quant table with the metadata to find nodes that separate groups.
- Show me the MS/MS spectrum for node `<cluster index>` (and mirror it against its
  library hit) using the metabolomics-USI resolver.

## Provenance

Files were pulled from the GNPS2 `/resultfile` endpoint on https://gnps2.org for
task `ad67978e27274245abe5ea428c44ce09` (`everything_bagel_workflow`). Only the files present in
this run and selected at package time are included — see `manifest.json`. This tool
supports Classical Molecular Networking, FBMN, and Everything Bagel; a run that skipped
an optional step simply omits those files.
