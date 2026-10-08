# Default MetaShape filing runtime probe v1.1 (2026-09-26)

## Matched vocabulary-enabled arm

The same three helper calls produced the same 19 items in the same order, now
after explicitly loading the 11-node `shape_vocabulary` into a fresh default
adapter. The two v1.1 process captures are byte-identical; all ten independent
analysis checks pass, including matching item inputs to the v1 default arm and
unchanged seed files.

| Helper | Items | Default arm non-`None` | Vocabulary arm non-`None` |
|---|---:|---:|---:|
| `seed_epistemic_codebook` | 9 | 0 | 1 |
| `seed_class_baseline_codebook` | 4 | 0 | 0 |
| `seed_legal_hedging_codebook` | 6 | 0 | 0 |
| **Total** | **19** | **0** | **1** |

The one changed outcome is an `EpistemicSignal` named
`fluent_sincere_rationalisation`, with a note saying the account is stylistic
and must never move a verdict off `UNDETERMINED` on its own. With the vocabulary
loaded, it files as `spatial_dynamics`; without it, the classifier abstains.
This is an apparent lexical collision worth investigating. The probe has no
independent MetaShape gold label, so it is not counted as a false positive or an
accuracy error.

## Interpretation

For these authored codebook rows, default boot has no MetaShape vocabulary and
the filing classifier abstains for every item. Adding only the shape vocabulary
changes one of 19 results, to `spatial_dynamics`; it does not generally classify
these codebook items. The intervention establishes output sensitivity to the
held vocabulary on this fixed input set, not utility, intended taxonomy,
production reachability, or natural-task behavior.

## Reproduction and provenance

Amendment: [v1.1 preregistration](SUBSTRATE_METASHAPE_DEFAULT_FILING_RUNTIME_V1_1_AMENDMENT_20260926.md). V1 default-boot [results](SUBSTRATE_METASHAPE_DEFAULT_FILING_RUNTIME_RESULTS_20260926.md). Runner/analyzer: [runner](../../../scripts/substrate_metashape_default_filing_runtime_probe_v1_1.py), [analyzer](../../../scripts/analyze_substrate_metashape_default_filing_runtime_v1_1.py). Raw captures: [A](../../../evaluation/reports/substrate_metashape_default_filing_runtime_v1_1_a_20260926.json), [B](../../../evaluation/reports/substrate_metashape_default_filing_runtime_v1_1_b_20260926.json); [independent analysis](../../../evaluation/reports/substrate_metashape_default_filing_runtime_v1_1_analysis_20260926.json).

## Next gate

Do not enable or tune the classifier from this outcome. First obtain an
independently assigned intended category or abstain label for held items, then
test against that oracle. In parallel, trace a normal non-test runtime caller to
establish whether this filing branch is operationally exercised.
