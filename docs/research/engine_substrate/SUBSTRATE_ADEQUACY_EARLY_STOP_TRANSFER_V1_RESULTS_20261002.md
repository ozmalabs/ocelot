# Early-stop and hypothesis-family transfer for adequacy probes v1 — results

The source/native-locked panel contains 1,440 cells and passes all 10 independent analysis checks. It crosses two Term families, four controls per family, two probe policies, budgets 1/2/4, and 30 repetitions. The audit stops immediately when a label contradicts the candidate.

| Family, wrong broad-domain cases | Hash false accepts k=1 / 2 / 4 | Entropy false accepts k=1 / 2 / 4 | Mean labels used, hash k=4 / entropy k=4 |
|---|---:|---:|---:|
| Sparse polynomial | 54/60, 51/60, 39/60 | 0/60, 0/60, 0/60 | 3.53 / 1.00 |
| Two-variable arithmetic | 56/60, 54/60, 46/60 | 0/60, 0/60, 0/60 | 3.65 / 1.00 |

Maximum-entropy probing selects the one distinguishing witness first in every broad-domain repetition in both families. It accepts the correct candidate and passes all held-outs in 30/30 repetitions for each family and budget. On both alias-only domains, both policies falsely accept in 30/30 repetitions: no selection rule can expose a distinction absent from its domain.

With early stopping, the one-label entropy policy reduces label use as well as false acceptance. For the k=4 setting, median native selection-plus-update time is approximately 0.50 ms versus 0.25 ms for hash sampling in the polynomial cases, and 0.43 ms versus 0.14 ms in the two-variable cases. Hash order setup is included here; oracle label latency is excluded. Hash reaches the witness on some repetitions and then stops, while entropy pays to score each available domain point before its first query. This is a measurable compute-for-label tradeoff; whether it is favorable depends on the cost and availability of labels.

This result transfers the pattern across two authored Term families, not across natural tasks. The challenger set and domains are supplied, oracle labels are harness generated, and the alternatives expose the witness. It does not measure authenticated evidence, production receipt/adoption integration, naturally occurring alias rates, or autonomous proposal generation.

Artifacts: [preregistration](SUBSTRATE_ADEQUACY_EARLY_STOP_TRANSFER_V1_PREREG_20261002.md), [runner](../../../evaluation/substrate_capability/substrate_adequacy_early_stop_transfer_v1.py), [lock](../../../evaluation/substrate_capability/substrate_adequacy_early_stop_transfer_v1_lock_20261002.json), [independent analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_early_stop_transfer_v1.py), [raw capture](../../../evaluation/reports/substrate_adequacy_early_stop_transfer_v1_raw_20261002.json), and [analysis](../../../evaluation/reports/substrate_adequacy_early_stop_transfer_v1_analysis_20261002.json).
