# Linear P21 results — bounded retention and self-curriculum

**Protocol:** [`COGNITION_LINEAR_P21_PREREG.md`](COGNITION_LINEAR_P21_PREREG.md), frozen in standalone commit `31ce0440` against implementation commit `f9212d28`.  
**Run:** one fixed held-out allocation, 2026-10-23.  
**Classification:** structural audit `PASS`; native runtime `ATTESTED`; both registered primary effects `FAIL`.

## Registered outcomes

The sleep primary was full-sleep minus replay-only normalized delayed learning-curve AUC. The paired effect was **0.000** against the required `+0.10`; paired new-task accuracy loss was `0.000`, within the `0.02` limit. Each arm reached delayed accuracy 1.00 and new-task accuracy 0.00. At every capacity, full sleep, replay-only, awake rehearsal and no-offline had mean AUC `0.25`. The valid result is `FAIL`: native sleep produced no measured retention gain in this task distribution.

The curriculum primary was residual-selected minus the paired mean of random and fixed selection. Its effect was **0.000** against the required `+0.10`. All three selectors reached delayed accuracy 1.00, used exactly two target actions and seven native rule steps per row, and consumed mean budget debit 4.00. The valid result is `FAIL`: selection did not improve learning under the registered ceiling-level task distribution.

The panels completed 2,400 sleep rows (600 per arm), 1,800 curriculum rows (600 per selector), and 100 structural controls. All capacities (2,048, 4,096 and 8,192 bytes) had 200 rows per arm or selector. Structural analysis reported zero failures; every control exercised over-capacity rejection, unavailable reads and answer-field isolation and passed. Native sleep stages completed in all full-sleep rows. Awake rehearsal used a mean 53 native rule steps against 51 for full sleep, within the frozen five-percent compute match.

## Resource outcomes

Sleep mean resource values across capacities:

| Arm | Native rule steps | Shared-budget debit | Elapsed seconds | Graph bytes | Charged memory bytes | Retrieval bytes |
|---|---:|---:|---:|---:|---:|---:|
| Full sleep | 51 | 9 | 0.0791 | 225,125 | 3,238 | 228 |
| Replay-only | 45 | 5 | 0.0776 | 223,517 | 3,546 | 546 |
| Awake rehearsal | 53 | 2 | 0.0879 | 228,153 | 3,238 | 228 |
| No offline | 0 | 2 | 0.0205 | 221,119 | 3,546 | 546 |

Every sleep arm admitted the same two world receipts and performed eight real interference actions. The larger capacities retained more interference rows, while 2,048-byte strata evicted six of eight. Full sleep's compressed chunk was retrieved on the delayed task and lowered measured retrieval bytes, but did not improve the score. The full-sleep debit exceeded replay-only by four units without a measured benefit.

## Provenance and artifacts

The analyzer verified the exact preregistration, complete allocation, all paired work checks, zero-tolerance controls and current source/profile/world/dependency hashes. Runtime attestation was `ATTESTED`, with no issues. The frozen allocation digest is `f6470481acafe05c287de7ef1014a70c18f2aa4d52f87e0884a86ae0fe991487`.

- Raw held-out payload: `/tmp/cognition_p21_heldout.json`, SHA-256 `d906b3c1eca6e4dafac64a9c1f1bf3d807c77d2571f1202657fc0454516aadd1`.
- Analyzer output: `/tmp/cognition_p21_heldout_analysis.json`, SHA-256 `3a1d8da1920e30ff0266ef142eb15f93ad3718fc7b37332f5b96fcfbaede5fb3`.
- Development payload: `/tmp/cognition_p21_development.json`; structural `PASS`, 24 sleep rows, 18 curriculum rows and two controls.
- Development analyzer: `/tmp/cognition_p21_development_analysis.json`; structural `PASS`, both efficacy primaries `NOT_ESTIMATED`.
- Held-out preregistration SHA-256: `69ff78f1fecceecbdde7c40b926e95bf0840528f0882ed99c9224a806d6ddcf3`.

The focused mechanism/profile/curriculum regression suite passed 93 tests. Development and held-out analyzer checks passed. No rerun or threshold change is authorized by these results.

## Phase decision

P21's storage, retrieval, sleep lifecycle, native curriculum delivery and controls are established for the registered simulator panels. Neither retention benefit nor curriculum-selection benefit is established; both remain failed hypotheses. Further work must fix the ceiling-limited independent task distribution before testing efficacy again. P22 may continue as a specification and mechanism program for independent-goal, multi-generation learning, but may not claim P21 efficacy or treat generated tasks alone as improvement evidence.
