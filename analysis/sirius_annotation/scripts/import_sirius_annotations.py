"""Distill a merged SIRIUS run (merge_sirius_shards.py output) into one row
per feature_id in sirius_annotations.tsv, accumulating across repeated/
separate runs rather than overwriting.

Join key: SIRIUS's own feature-id column (its exact header name is detected
at runtime -- SIRIUS 6.x versions have used "mappingFeatureId" and
"featureId" across releases) is treated as identical to this project's
feature/row id (both derive from the source MGF's SCANS= tag).

On conflict between runs for the same feature_id: a row with a structure hit
beats a row with formula-only, then higher structure confidence wins.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FEATURE_ID_COLUMN_CANDIDATES = ["mappingFeatureId", "featureId", "id"]
TOP_RANK = 1  # SIRIUS ranks candidates per compound starting at 1; "rank==1" means "best hit".

OUTPUT_COLUMNS = [
    "feature_id",
    "sirius_formula",
    "sirius_adduct",
    "sirius_structure_name",
    "sirius_structure_smiles",
    "sirius_structure_confidence",
    "sirius_npc_pathway",
    "sirius_npc_class",
    "sirius_classyfire_class",
    "source_run",
]


def find_feature_id_column(df: pd.DataFrame, table_name: str) -> str:
    for candidate in FEATURE_ID_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate
    raise ValueError(
        f"{table_name}: none of the expected feature-id columns {FEATURE_ID_COLUMN_CANDIDATES} "
        f"found; actual columns are {list(df.columns)} -- update FEATURE_ID_COLUMN_CANDIDATES"
    )


def find_column_containing(df: pd.DataFrame, substrings: list[str], table_name: str) -> str | None:
    for col in df.columns:
        lowered = col.lower()
        if any(s in lowered for s in substrings):
            return col
    print(f"NOTE: {table_name} has no column matching {substrings}; actual columns: {list(df.columns)}")
    return None


def load_table(merged_dir: Path, name: str) -> pd.DataFrame | None:
    path = merged_dir / name
    if not path.exists():
        # ANALYSIS_OK[optional-input]: this table is genuinely optional per SIRIUS run (e.g.
        # structure_identifications.tsv is absent if CSI:FingerID found zero hits); every caller
        # checks `is not None` (see build_run_table) instead of assuming presence.
        return None
    df = pd.read_csv(path, sep="\t")
    if df.empty:
        # ANALYSIS_OK[optional-input]: an empty summary table (SIRIUS wrote the header, zero
        # rows) is treated the same as "table absent" by every caller via the `is not None` check.
        return None
    return df


def build_run_table(merged_dir: Path, label: str) -> pd.DataFrame:
    rows: dict[int, dict] = {}

    formulas = load_table(merged_dir, "formula_identifications.tsv")
    if formulas is not None:
        fid_col = find_feature_id_column(formulas, "formula_identifications.tsv")
        rank_col = find_column_containing(formulas, ["rank"], "formula_identifications.tsv")
        # "molecularformula" only (not a bare "formula") -- the bare substring would match
        # "formulaRank" itself, which is iterated first in the real SIRIUS 6.3.12 header.
        formula_col = find_column_containing(formulas, ["molecularformula"], "formula_identifications.tsv")
        adduct_col = find_column_containing(formulas, ["adduct"], "formula_identifications.tsv")
        top = formulas[formulas[rank_col] == TOP_RANK] if rank_col else formulas
        for _, row in top.iterrows():
            fid = int(row[fid_col])
            rows.setdefault(fid, {})["sirius_formula"] = row.get(formula_col) if formula_col else None
            rows[fid]["sirius_adduct"] = row.get(adduct_col) if adduct_col else None

    structures = load_table(merged_dir, "structure_identifications.tsv")
    if structures is not None:
        fid_col = find_feature_id_column(structures, "structure_identifications.tsv")
        rank_col = find_column_containing(structures, ["rank"], "structure_identifications.tsv")
        name_col = find_column_containing(structures, ["name"], "structure_identifications.tsv")
        smiles_col = find_column_containing(structures, ["smiles"], "structure_identifications.tsv")
        conf_col = find_column_containing(structures, ["confidencescore", "confidence"], "structure_identifications.tsv")
        top = structures[structures[rank_col] == TOP_RANK] if rank_col else structures
        for _, row in top.iterrows():
            fid = int(row[fid_col])
            rows.setdefault(fid, {})["sirius_structure_name"] = row.get(name_col) if name_col else None
            rows[fid]["sirius_structure_smiles"] = row.get(smiles_col) if smiles_col else None
            conf = row.get(conf_col) if conf_col else None
            if conf is not None and (conf == float("inf") or conf == float("-inf")):
                conf = None
            rows[fid]["sirius_structure_confidence"] = conf

    canopus = load_table(merged_dir, "canopus_structure_summary.tsv")
    if canopus is None:
        canopus = load_table(merged_dir, "canopus_formula_summary.tsv")
    if canopus is not None:
        fid_col = find_feature_id_column(canopus, "canopus_*_summary.tsv")
        pathway_col = find_column_containing(canopus, ["npc#pathway", "npc pathway"], "canopus summary")
        class_col = find_column_containing(canopus, ["npc#class", "npc class"], "canopus summary")
        # "classyfire#class" (not just "classyfire") -- the bare substring would match
        # "ClassyFire#superclass", which sorts earlier in the real SIRIUS 6.3.12 header.
        classyfire_col = find_column_containing(canopus, ["classyfire#class"], "canopus summary")
        for _, row in canopus.iterrows():
            fid = int(row[fid_col])
            rows.setdefault(fid, {})["sirius_npc_pathway"] = row.get(pathway_col) if pathway_col else None
            rows[fid]["sirius_npc_class"] = row.get(class_col) if class_col else None
            rows[fid]["sirius_classyfire_class"] = row.get(classyfire_col) if classyfire_col else None

    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "feature_id"
    out = out.reset_index()
    out["source_run"] = label
    for col in OUTPUT_COLUMNS:
        if col not in out.columns:
            out[col] = None
    return out[OUTPUT_COLUMNS]


def merge_accumulate(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([existing, new], ignore_index=True)

    def pick_best(group: pd.DataFrame) -> pd.Series:
        has_structure = group["sirius_structure_name"].notna()
        if has_structure.any():
            group = group[has_structure]
        group = group.sort_values("sirius_structure_confidence", ascending=False, na_position="last")
        best = group.iloc[0].copy()
        best["source_run"] = ";".join(sorted(set(combined.loc[combined["feature_id"] == best["feature_id"], "source_run"])))
        return best

    return combined.groupby("feature_id", group_keys=False).apply(pick_best).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merged-dir", type=Path, required=True, help="Output of merge_sirius_shards.py")
    parser.add_argument("--label", required=True, help="Short label for this run, e.g. 'interesting_2026-08-20'")
    parser.add_argument("--annotations-path", type=Path, default=None)
    parser.add_argument("--fresh", action="store_true", help="Rebuild from scratch instead of accumulating")
    args = parser.parse_args()

    analysis_root = Path(__file__).resolve().parents[1]
    annotations_path = args.annotations_path or (analysis_root / "sirius_annotations.tsv")

    new_run = build_run_table(args.merged_dir, args.label)

    if annotations_path.exists() and not args.fresh:
        existing = pd.read_csv(annotations_path, sep="\t")
        combined = merge_accumulate(existing, new_run)
    else:
        combined = new_run

    combined = combined.sort_values("feature_id")
    combined.to_csv(annotations_path, sep="\t", index=False)

    n_structure = int(combined["sirius_structure_name"].notna().sum())
    n_formula_only = int(combined.shape[0] - n_structure)
    print(f"{combined.shape[0]} total annotated features ({n_structure} with structure hit, {n_formula_only} formula-only)")
    print(f"Written to {annotations_path}")


if __name__ == "__main__":
    main()
