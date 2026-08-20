# _lib

Shared helper code vendored for use by multiple `analysis/*/scripts/`.

- `register_value.py` — copied verbatim from the Mycelium plugin
  (`skills/core/scripts/register_value.py`) per the report-values-guide's
  suggested vendoring pattern, so analysis scripts can
  `sys.path.insert(...); from register_value import register_value`
  without depending on the plugin cache path at runtime.
