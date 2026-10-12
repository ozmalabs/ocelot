# Effect-only attribute replay order and binding scale (2026-09-25)

## Protocol

The native substrate ran every authored rule-order permutation for one, two, or three writers. Each writer changes the same source node's `watched` attribute to a distinct constant; a reader rule copies that attribute to matched target nodes. The harness varied reader-binding count across 8, 64, and 128, then compared each settled reader value with the final graph value for its source. Every run received a terminal `run_rules(1)` probe. The probe ran 96 deterministic cases and records source/native provenance and full graph snapshots in the [raw report](../../../evaluation/reports/substrate_replay_order_scale_20260925.json).

## Results

All cases settled, and every output was checked against the final graph. Stale reads appeared at every binding count and writer family:

| Writers | Distinct writer orders | Stale schedules per binding count | Mismatch fraction in a stale schedule |
|---|---:|---:|---:|
| 1 (`5`) | 2 | 1/2 | 1/8, 1/64, 1/128 |
| 2 (`3`, `7`) | 6 | 4/6 | 1/8, 1/64, 1/128 |
| 3 (`-2`, `5`, `11`) | 24 | 18/24 | 1/8, 1/64, 1/128 |

In this generator, all writers target only the first source while the reader spans every source. Therefore the schedule-level stale rate stays fixed as the binding count grows, while the fraction of reader outputs stale in a failing schedule drops as `1 / binding_count`. Adding a third writer raises the observed stale-order share from 4/6 to 18/24 (75%); this is deterministic evidence for this generator, not an estimate of natural workload prevalence.

## Interpretation and boundary

More reader bindings dilute the output-level mismatch but do not remove the order-sensitive stale read. A larger number of competing writes to the shared source increases the fraction of rule orders with a mismatch in this probe. The result supports extending the replay audit's generator and confirms the need to compare scheduler suppression with a full recomputation oracle before changing policy. It does not validate a fix, test native effect-to-frame notification, or estimate frequency on CAN, conversation, or other authored tasks.
