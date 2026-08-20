# Environments & Installations

## Primary Environment

- **Manager**: 
- **Python version**: 
- **Created**: 

### Setup from scratch

```bash
# Add setup commands here
```

## Dependencies

- The default `python3` (miniconda 3.9, see below) already has `pandas`, `numpy`, `scipy`, `scikit-learn`, and `matplotlib` installed and was used as-is for `analysis/pcoa-ms-feature-composition/` (no project-level pixi/venv environment exists yet — consider adding one if more analyses accumulate).
- `scilintr` (analysis linter) installed via `/usr/bin/python3.12 -m pip install --user scilintr` — it requires Python >=3.11, so it will not install under the default miniconda 3.9 `python3`/`pip`. Run it as `~/.local/bin/scilintr` (on `PATH` after a fresh login shell) or `/usr/bin/python3.12 -m scilintr`.

## System Dependencies

<!-- Add system-level dependencies here. -->

## HPCC (UCR SLURM) notes

- Host default `python3` resolves to miniconda 3.9 (`/opt/linux/rocky/8.x/x86_64/pkgs/miniconda3/py39_4.12.0/bin/python3`). Use `/usr/bin/python3.12` for anything needing Python ≥3.11 (including Mycelium's own `skills/core/scripts/*.py`, which import `datetime.UTC`).
- The GNPS2 bagel README (`data/raw/gnps2_f7a16270_bagel/README_FOR_CLAUDE.md`) recommends `pip install -r data/raw/gnps2_f7a16270_bagel/requirements.txt` (massql, pyteomics, rdkit) in a fresh virtualenv for local annotation work on this bundle — not yet set up.
