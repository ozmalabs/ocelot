# Thoughtexperiment recurrence offer idempotence v1 — results

**Result:** 7/7 preregistered gates pass.

Across three fresh workers, the single injected defect—removing the existing negative-existence guard from `mrl_offer_due_once`—causes the task graph to mint [75, 75, 75] offers for one recurrence candidate over five bounded closure sweeps. On each worker, a full-copy branch restores the known authored rule, emits exactly one offer, reaches a zero-progress fixed point, and leaves the faulty primary graph and rules unchanged.

The independent oracle is the count of `has_mint_offer` edges from the target candidate, rather than the collapse model's generic Observation-frontier estimate. This establishes a second task-shaped thoughtexperiment with clear utility and isolation checks. The repair was supplied from the known authored rule: this does not show autonomous diagnosis, correction discovery, outcome transfer, or COW performance.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_OFFER_IDEMPOTENCE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_offer_idempotence_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_offer_idempotence_v1_raw_20261001.json)
