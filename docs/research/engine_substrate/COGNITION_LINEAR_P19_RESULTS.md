# Linear P19 v1 results

**Protocol:** `linear-p19-v1`. **Status:** held-out allocation complete; structural audit passes; primary efficacy `NOT_ESTABLISHED`. The raw scorecard and analysis remain outside git at `/tmp/linear_p19_heldout.json` and `/tmp/linear_p19_analysis.json`.

## Frozen artifacts and integrity

The preregistration was committed alone as `cfc4efd2` before the sole held-out launch. The runner confirmed the standalone freeze and exact provenance bundle. Analyzer status is `PASS`; runtime provenance is `ATTESTED`. There are 2,400/2,400 expected arm rows, 100/100 passing controls, and zero receipt, resource, pairing, exposure, or other structural audit failures.

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| Raw held-out scorecard | `9416ec3f6100164a80be67bc7868371877cd25826ced6cfa8461174ddbc2fda5` | 5,732,128 |
| Analyzer output | `36c0863fb6ab67bd1ed2e04345e2c888e118c41824da2b834b1570dc249c33db` | 70,740 |

The loaded extension hash is `16b94f563be757ad9293e4921864466052d02e3fa07102ecff9e014b0b76a12b`; build receipt hash `c350006f11edc703ae3668c302aedb9ae04aa61659e4752b6fb2bcdb7e4916a1`; source fingerprint `73c04733538d88f983beb5139e2dfae4633e686738f9161f56a8b2678e8e2c54`. Full component hashes and allocation identities are frozen in [`COGNITION_LINEAR_P19_PREREG.md`](COGNITION_LINEAR_P19_PREREG.md).

## Outcomes

| Cell | Invention discovery | Measured greedy | Native primitive search |
|---|---:|---:|---:|
| Permutation / process effect | 0/200 actionable solves; 193 awaiting approval, 7 ambiguous | 120/200 (60%) | 200/200 (100%) |
| Permutation / multi-step constraint | 0/200 actionable solves; 189 awaiting approval, 9 ambiguous, 2 no candidate | 112/200 (56%) | 200/200 (100%) |
| Irreversible objects / process effect | 0/200 actionable solves; 200 awaiting approval | 200/200 (100%) | 200/200 (100%) |
| Irreversible objects / multi-step constraint | 0/200 actionable solves; 200 no candidate | 200/200 (100%) | 200/200 (100%) |

Overall comparator rates were 632/800 (79%) for greedy and 800/800 (100%) for native primitive search. The invention arm has 582 `AWAITING_CANDIDATE_APPROVAL`, 202 `NO_CANDIDATE`, and 16 `AMBIGUOUS_CANDIDATE` rows. Missing candidate-specific human approval is an authorization boundary, so these proposals were non-actionable and are not scored as zero-skill failures. Because approvals are pending, the registered primary comparison is `NOT_ESTABLISHED` rather than an efficacy `FAIL`.

The two mechanism criteria both `FAIL` on the observed held-out panel: there were zero independently receipted non-template inventions and zero receipt-learned strategies solving a changed state and goal binding. No candidate approval manifest was supplied. These counts show the mechanisms were not demonstrated in this run; they do not establish that approved candidates would fail.

All 100 controls passed (34 impossible-goal, 33 illegal-action, 33 precondition-failure). The native search solved every cell; greedy reached its ceiling on irreversible-object tasks and solved 112/200 and 120/200 permutation multi-step and effect tasks. Mean model queries / primitives by cell were: irreversible multi-step, greedy 7 / 4 and native 17 / 4; irreversible effect, 4 / 2 and 13 / 2; permutation multi-step, 19.16 / 4.79 and 132.695 / 2.12; permutation effect, 17.38 / 4.345 and 126.55 / 2.045. These are adapter-specific declared units, not equivalent wall-clock costs. Held-out raw rows contain 91,634 invention search attempts total (mean 114.54, max 120); the frozen analyzer's model-query field is zero for pending rows because those rows have no executed-world query record. This supplementary attempt count does not replace the frozen accounting.

## Interpretation and next entry

P19 establishes that the frozen task allocation, native search comparator, control checks and provenance audit execute as specified. It does not establish an efficacy benefit for generic invention or unseen-binding strategy learning. The held-out mechanism criteria remain unmet, and no capability-level claim follows.

Phase 20 entry is supported narrowly by P19's bounded graph search, candidate-digest/approval boundary, receipt-backed strategy interfaces, P18 observed-model interface, and P16/P17 native evidence paths. P20 must preserve P19's unresolved efficacy and approval-limited mechanisms; it must implement and validate a fresh target learner before freezing any transfer comparison. It may not assume generic invention or strategy transfer succeeded.
