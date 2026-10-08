# Thoughtexperiment recurrence compose-and-select v1.1 — results

## Result

The corrected, source/native-locked integration panel passes all 12 independent analysis checks. Four workers each compared nine unique hypotheses: eight from the unchanged host correction generator and the generic `add_match_guard` proposal produced by the general graph-Term composer. The selector saw opaque digests with the same neutral label and two training outcomes per candidate. In all workers it selected `dedup_identity_fix` as the unique training maximum (2/2); the generic composer proposal scored 0/2. The frozen selection then passed both disjoint held-out episodes in all four workers (8/8). All-wrong and tie controls abstained. Proposal and evidence nodes stayed in the snapshot branch, primary rules remained unchanged, and held-out keys were disjoint from training keys.

Median training scoring across nine candidates and two episodes was 8.02 s per worker; native-Term selection took 0.568 ms median. The result composes the previously separate findings: the generic composer cannot express the needed recurrence repair, while the graph-resident evidence selector can select a supplied specialized repair from outcomes. Host code still generates the candidate set, task cue, task episodes, and labels; therefore this is not open-ended structure induction. The cost also shows that most work lies in generating and scoring alternatives, not choosing among them.

V1 training capture is retained but its held-out stage stopped before scoring because the scorer did not replay the recorded candidate permutation. V1.1 fixes that stage and uses a separate lock and capture. No v1 training outcomes are carried into v1.1.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_COMPOSE_AND_SELECT_V1_PREREG_20261002.md)
- [V1.1 amendment](THOUGHTEXPERIMENT_RECURRENCE_COMPOSE_AND_SELECT_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_compose_and_select_v1.py)
- [V1.1 source lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_compose_and_select_v1_1_lock_20261002.json)
- [Training orders and evidence](../../../evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_scores_20261002.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_recurrence_compose_and_select_v1_1_analysis_20261002.json)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_compose_and_select_v1.py)
