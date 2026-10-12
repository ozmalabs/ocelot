# Default MetaShape filing runtime probe (2026-09-26)

## Result

The three actor-goal codebook helpers completed on a fresh default
`WorldAdapter`; their four source-level `teach()` call expressions produced 19
runtime items. The wrapped default classifier ran for all 19, and returned
`None` for all 19. The adapter held zero `MetaShape` nodes. Seed persistence was
disabled, and the SHA-256 digest of all `seeds/*.json` files was identical
before and after each capture.

| Helper | Runtime classifier calls | Non-`None` filing results |
|---|---:|---:|
| `seed_epistemic_codebook` | 9 | 0 |
| `seed_class_baseline_codebook` | 4 | 0 |
| `seed_legal_hedging_codebook` | 6 | 0 |
| **Total** | **19** | **0** |

The two fresh-process raw captures are byte-identical. All ten independent
analyzer checks pass, including helper order/counts, no persistence, unchanged
seed-tree digest, recorded-call completeness, result values, and source/native
artifact identity.

## Interpretation and boundary

This closes the uncertainty about these three helper paths on a default boot:
their omitted filing arguments do reach `categorise_by_shape`, but the empty
MetaShape codebook makes the result uniformly `None`, after which `teach()` uses
the item's `category`/`domain`/`topic` or its `taught` fallback. The result does
not measure semantic accuracy.

The helper functions were found only at test call sites in the repository. This
probe called them directly; it does not show their production frequency or
external use. It also does not characterize a boot profile that loads
`shape_vocabulary`, nor other wrappers whose dynamic category arguments can be
`None`. Those are separate activation questions. No conclusion about overall
MetaShape usefulness or natural filing quality follows from this sample.

## Reproduction

From the repository root, run twice in separate processes:

```sh
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_metashape_default_filing_runtime_probe_v1.py > evaluation/reports/substrate_metashape_default_filing_runtime_v1_a_20260926.json
PYTHONPATH=.:runners/dsl/python .venv/bin/python scripts/substrate_metashape_default_filing_runtime_probe_v1.py > evaluation/reports/substrate_metashape_default_filing_runtime_v1_b_20260926.json
.venv/bin/python scripts/analyze_substrate_metashape_default_filing_runtime_v1.py evaluation/reports/substrate_metashape_default_filing_runtime_v1_a_20260926.json evaluation/reports/substrate_metashape_default_filing_runtime_v1_b_20260926.json
```

Protocol: [preregistration](SUBSTRATE_METASHAPE_DEFAULT_FILING_RUNTIME_PREREG_20260926.md). Runner and independent analyzer: [runner](../../../scripts/substrate_metashape_default_filing_runtime_probe_v1.py), [analyzer](../../../scripts/analyze_substrate_metashape_default_filing_runtime_v1.py). Raw captures: [A](../../../evaluation/reports/substrate_metashape_default_filing_runtime_v1_a_20260926.json), [B](../../../evaluation/reports/substrate_metashape_default_filing_runtime_v1_b_20260926.json); [analysis](../../../evaluation/reports/substrate_metashape_default_filing_runtime_v1_analysis_20260926.json).

## Next gate

Measure the same held items under an explicitly loaded MetaShape vocabulary, then
trace an actual non-test production caller or instrument a representative normal
boot to establish whether any default filing branch is reached. Keep the default
boot and vocabulary-enabled arm distinct; report classification changes without
calling them correct absent independent labels.
