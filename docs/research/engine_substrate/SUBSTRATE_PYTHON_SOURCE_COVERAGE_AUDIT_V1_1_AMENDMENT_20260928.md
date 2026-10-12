# Python source coverage audit v1.1 amendment

Date: 2026-09-28  
Status: extends v1 with explicit profile preload and seed-manifest crosswalks.

## Changes from v1

- Added `substrate/boot_profiles.py` as a runtime entrypoint and extracted literal module names from `CONVERSATION_RUNTIME_MODULES` and constant `import_module(...)` calls.
- Scanned the exact top-level `seeds/*.json` and `seeds/generated/*.json` path sets used by `boot_all`; excluded valid manifests marked `self_load_only` from the eligible-manifest module-reference check.
- Matched only exact dotted Python module names in eligible manifest string values. Package names such as `domains` are not treated as imports.
- Recorded a SHA-256 for each of the 833 Python files and 838 discovered seed JSON manifests, and rechecked both file sets after analysis. Any source or seed drift aborts output.

## Results

The literal conversation profile contains 65 unique Python module preload targets. Static imports from the six entrypoints already reach 247 files; declared profile loads increase this to 248, adding only `domains/reference_slab.py` to the reachable set. Across 742 loader-eligible seed manifests, no exact dotted Python module references were found. The census has zero Python parse errors and zero malformed seed manifests.

This does not prove that the 65 modules execute on every conversation, nor that seed-defined graph rules have no external dispatch path. Computed imports, `importlib` inputs assembled at runtime, Python host callbacks stored outside seed JSON, and non-Python loading remain outside the extracted cases. V1 remains intact as the initial static-only record; use v1.1 for profile and manifest claims.
