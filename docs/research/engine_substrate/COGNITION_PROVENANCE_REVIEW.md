# Native provenance review

Review date: 2026-10-22. Scope: process-mastery runner artifact fingerprints through P15 and the P16.02 loaded-extension attestation requirements.

## Finding

The P6–P15 linear runners that declare `engine_binary_sha256` hash `Path(substrate_rs.__file__)`. That path is the Python package wrapper (`__init__.py`), not the loaded `substrate_rs._native` extension. The P15 review independently verified the frozen wrapper digest and compared it with the tracked native artifact available at the P15 freeze; those bytes differ. Therefore, the historical tables establish wrapper/source metadata identity where recorded, but do not establish which native extension executed. Their historical outcomes remain intact; native runtime identity is `NOT_ESTABLISHED`.

The repository also has `domains.engine_provenance` checks for deterministic native-module resolution and build/source freshness. Those checks support current-tree reproducibility, but do not retroactively bind earlier scorecards to the module object loaded during those runs. A later rebuild or commit cannot supply the missing execution-time identity.

## New freeze requirements

`evaluation.process_mastery.runtime_attestation.attest` separately records wrapper bytes, the exact loaded extension module path and bytes, symbol identity, build-receipt bytes, and source fingerprint. A freeze must fail closed unless those fields are present and match; the receipt's extension digest must match the loaded extension, and a new held-out freeze must reject dirty artifact/source paths. Missing receipt or module evidence is `UNKNOWN`, while a mismatch is not eligible for a freeze. Development can inspect an unclean tree, clearly labeled development-only.

The native module object is obtained from the already imported `substrate_rs` package; attestation does not search for a convenient library or copy one into place. P15 and earlier scorecards are not silently rehashed or upgraded.
