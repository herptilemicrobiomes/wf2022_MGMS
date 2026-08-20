# Learnings

Append-only log of gotchas, surprises, and insights.

### [2026-08-19] Mycelium plugin scripts require Python 3.11+ on this HPCC login node

**Category**: gotcha

**What happened**: `init_repo.py` (and by extension the other `skills/core/scripts/*.py` mycelium scripts) import `datetime.UTC`, added in Python 3.11. The default `python3` on this UCR HPCC node resolves to the miniconda 3.9 install and fails with `ImportError: cannot import name 'UTC' from 'datetime'`. `/usr/bin/python3.12` is available on the system and works.

**Why it matters**: Any future mycelium script invocation (`recall_lessons.py`, `generate_index.py`, `validate_structure.py`, `crystallize_findings.py`, `upsert_table_row.py`, etc.) on this host will fail the same way if invoked with the default `python3`.

**Resolution**: Invoke mycelium scripts explicitly with `/usr/bin/python3.12` on this host rather than bare `python3`.

**Tags**: mycelium, hpcc, python, environment

**mitigation_type**: ambient-awareness

**structural_mitigation_candidate**: Not fixable locally (it's the plugin's code); the plugin itself could guard the `UTC` import with a `try/except` fallback to `datetime.timezone.utc` for Python <3.11 compatibility.

---

**Entry template:** copy from `skills/core/templates/learning-entry.md` (includes Category, What happened, Why it matters, Resolution, Tags fields). The `**Tags**:` line is consumed by `generate_index.py --summary-heuristic` to build the cluster summary in INDEX.md — use them.
