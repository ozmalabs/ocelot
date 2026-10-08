# Independently authored anaphora transfer panel v1 results

## Result

Ten source-locked fresh workers ran all eleven frozen assistant-authored cases
through default `WorldAdapter()`, `receive_utterance`, and `comprehend`: 90
positive case-runs and 20 negative-control case-runs. The independent analyzer
passes **12/12 gates**. All 110 case oracles pass; all ten PIDs are distinct,
pre/post fingerprints match the lock, and complete graph digests repeat within
each case across workers.

The nine positive conditions cover new utterance combinations around
`question` and `answer`, recency selection after competing antecedents, a
three-turn pronoun chain, and `this`/`that` transfer. The two negatives correctly
leave an unknown antecedent and a first-turn pronoun unresolved. Median
receive-plus-comprehend wall times are 8.50–9.28 ms for eight cases, with the
first case's lazy seed-load interval at 32.26 ms. Adapter initialization
medians range from 26.86–32.17 ms. Median worker wall/CPU are 554.63/534.88 ms
for the eleven cases, and median peak RSS is 59,152 KiB. The largest final
graph contains 1,240 nodes and 1,202 edges.

## Interpretation and limits

This is a clean small transfer probe beyond the exact example combinations in
the earlier integration-test panel. It supports the specific claim that the
current held-structure route transfers between two already represented
concepts, selects the latest of those two antecedents, propagates across the
tested intermediate turn, and respects the two negative controls. It does not
test acquisition of new concepts or dimensions, broad lexical/syntactic
coverage, independently human-authored tasks, natural frequency, or general
language understanding. The suite was authored after inspecting the documented
rule contract; it is independent of the implementation's case outputs, not
blind to the target capability.

PersonaChat data was not used as held-out evidence: repository inspection found
that the standard learning route consumes the first 300 corpus rows, and a
persisted learned graph is present, so exposure of a convenient corpus split
cannot be ruled out from current provenance.

## Reproducibility

- Protocol: [`SUBSTRATE_INDEPENDENT_AUTHORED_ANAPHORA_PANEL_V1_PREREG_20260929.md`](SUBSTRATE_INDEPENDENT_AUTHORED_ANAPHORA_PANEL_V1_PREREG_20260929.md)
- Frozen task suite: [`anaphora_independent_task_suite_v1.json`](../../../evaluation/substrate_capability/anaphora_independent_task_suite_v1.json)
- Runner and analyzer: [`runner`](../../../scripts/substrate_independent_authored_anaphora_panel_v1.py), [`analyzer`](../../../scripts/analyze_substrate_independent_authored_anaphora_panel_v1.py)
- Source/native lock: [`lock`](../../../evaluation/substrate_capability/independent_authored_anaphora_panel_v1_lock_20260929.json)
- Raw capture and analysis: [`raw`](../../../evaluation/reports/independent_authored_anaphora_panel_v1_raw_20260929.json), [`analysis`](../../../evaluation/reports/independent_authored_anaphora_panel_v1_analysis_20260929.json)
