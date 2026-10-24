# P24 additive transfer results

**Disposition:** P24 v2 completed with all structural criteria satisfied and the registered transfer-benefit hypothesis failed in both families. P20's frozen result remains unchanged. The v1 draw is preserved but invalid for efficacy because its frozen analyzer crashed before scoring; it was not reanalyzed.

## Version history and provenance

P24 v1 was frozen in standalone commit `13582b9a` after implementation commits `3b9ddb7f`, `b2079b38`, and `22411522`. Its runner completed the one-shot allocation, but `analyze_linear_p24_v1` raised `UnboundLocalError` before returning any metrics. The consumed raw artifact is [`p24_linear_v1_heldout_20261024.json`](../../../evaluation/process_mastery/results/p24_linear_v1_heldout_20261024.json), SHA-256 `16c9d612e9a0826b0e722efe4ec20bba0fcdf496897a8981eec397ba1efdf657`. The v1 preregistration hash is `4bc21048ecfd1adf45551208de1baa74254eec106876e9d73463c55101c6d9be`. No v1 statistics were produced or used to select v2 criteria.

The corrected version was committed as runner/analyzer/test commit `4e26c05d`, then frozen alone in commit `e625c8b1`. Its preregistration is [`COGNITION_LINEAR_P24_V2_PREREG.md`](COGNITION_LINEAR_P24_V2_PREREG.md), SHA-256 `28145ad5324b48ade0ff048e9ab450f7d91e176918b382be060ceb66f29bc970`. The frozen runtime attested the loaded extension, wrapper, build receipt and profile closure. The v2 development self-check is [`p24_v2_e2_development_selfcheck_20261024_4e26c05d.json`](../../../evaluation/process_mastery/results/p24_v2_e2_development_selfcheck_20261024_4e26c05d.json), SHA-256 `0e9f86211a1f822c8a043a6be737d6875074a8c62b634960335bdc1e6be6f3ee`.

The v2 raw held-out artifact is [`p24_linear_v2_heldout_20261024.json`](../../../evaluation/process_mastery/results/p24_linear_v2_heldout_20261024.json), SHA-256 `0ce665df6fb14f837128c4f86c744028dc30bc23b441b3cec4ba8d92d84db18e`. The analyzer output is [`p24_linear_v2_heldout_analysis_20261024.json`](../../../evaluation/process_mastery/results/p24_linear_v2_heldout_analysis_20261024.json), SHA-256 `8731aefb3c7f0e2ed1a3a3fcf7a322808f2d2ffbc84d85d3c8affeccc9168641`. The runner commit was `e625c8b11f6c65d34e2badcc602ce2b84f077720`; runtime status was `ATTESTED`.

## Panel integrity and structural outcomes

- 400 paired streams completed: 200 each for `heat_to_thermal` and `lever_to_latch`; 1,600 arm rows were retained.
- 300/300 structural controls passed: 100 duplicate-receipt, 100 stale-map, and 100 wrong-source-map controls.
- Every stream gave all four arms the same two ordered target receipt IDs and identical ordinary-evidence signatures. There were zero missing target receipts, duplicate ordinary supports, or target action-count mismatches.
- Compatible-source maps and target-effect receipts verified in all 400 compatible rows. Wrong-source maps were rejected in all 400 wrong-source rows. The 400 fresh and 400 same-target-map-work rows carried no external source information or imported prior.
- Target actions were exactly 2 in every arm. Source actions were 2 in compatible/wrong-source and 0 in fresh/same-target-map-work. Map pairs were 2 in each map-work arm and 0 in fresh. Map verification queries were 5 in compatible/wrong-source and 0 otherwise.
- Shared-budget debits were exactly 2 for fresh and 4 for each map-work arm. The native budget record was enabled with capacity 16 and ceiling 64. External model queries were 0. All target/source native-work and graph-byte ceilings passed.
- The paired stream runner recorded 117.058 seconds total shared-stream elapsed time across 400 streams; median per-stream time was 0.2805 seconds for heat→thermal and 0.2851 seconds for lever→latch. This is host-level stream runtime, not isolated arm latency.
- Context epochs were balanced 100/100 at 5/6 in each family. Allocation checks found no overlap with prior protocols, including P24 v1.

## Registered efficacy outcomes

Every arm had normalized AUC 0.25 in every stream in both families; final accuracy was 1.0 in every arm. The stronger source-free comparator was fresh in both families (same-target-map-work also scored 0.25).

| Family | Compatible AUC | Stronger source-free AUC | Gain | Paired 99% CI | Holm-adjusted p | Final accuracy loss | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Heat→thermal | 0.25 | 0.25 | 0.00 | [0.00, 0.00] | 1.00 | 0.00 | FAIL |
| Lever→latch | 0.25 | 0.25 | 0.00 | [0.00, 0.00] | 1.00 | 0.00 | FAIL |

The registered minimum AUC gain was 0.10, with no final-accuracy loss greater than 0.02. There was no transfer advantage. The negative-transfer contrast, same-target-map-work contrast, and compatible-source-versus-fresh contrast were each exactly 0.00 in both families. Flat curves therefore remain a zero-gain outcome rather than a substitute success criterion.

Resource counts were deterministic within arm and family:

| Arm | Target native rule work | Source native rule work | Graph bytes, heat / lever | Budget debits |
|---|---:|---:|---:|---:|
| Fresh | 12 | 0 | 57,750 / 57,569 | 2 |
| Compatible source | 20 | 5 | 64,863 / 64,577 | 4 |
| Wrong source | 18 | 3 | 61,286 / 61,067 | 4 |
| Same-target map work | 15 | 0 | 61,283 / 61,034 | 4 |

These costs are reported separately; the protocol does not claim resource efficiency or equal realized native work.

## Verification and next entry

The P24 v1 frozen E2 bundle plus allocation/control/analyzer tests passed 23 tests; the P24.E1 integration gate passed 81 tests; related Track I foundation and P20 learner/curve/transfer regressions passed 97 tests. P24 v2 runner/analyzer development self-checks passed, and its focused v2/common-target/additive-transfer suite passed 26 tests. The repository regression sweep reported 16 GREEN, two inherited RED, one `NOT_ESTABLISHED` 420-second timeout (`test_capability_control_fabric_migrated.py`), and one `ALL_SKIPPED` file (`test_staleness_decay_migrated.py`); the baseline verifier found four existing RED entries and no new GREEN/RED classifications. Orphan-signal lint reported 2,243 repository-wide signals, including three source-prior/map relation edges; boot-status reporting found no broken dependencies for either P24 seed.

P24 establishes the common receipt-learning and optional verified-map paths, but it does **not** establish faster transfer, L4 capability, or any human comparison. P25 may proceed on the common learner and persistent-state interfaces; it must not assume P24 source transfer improved learning. P20's historical −0.3333 result remains frozen and unchanged.
