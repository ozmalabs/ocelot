# P26.02 diagnosed search repair results

**Date:** 2026-10-25. **Scope:** one training-only Loopover invention g1 continuation. **Held-out access:** none. **Candidate approval/adoption:** none. **P22 disposition:** remains draft; this development result does not open its held-out gate.

## Frozen allocation and lineage

The run restored the immutable Loopover g1 checkpoint `p22-loopover-g1-2638da0f23ae` (checkpoint digest `c91670f7a91ba3d9f958f865dc85c4d4596d852a8a97c0e99e1f8d3d7b925057`) from `p22_training_panel_registered_root_loopover_g1_0980_0983_ticks120_depth3.json` (artifact SHA-256 `918577599c88c5dc533eed0af99ba1e434522b01690e10c1674244ec74a6fbe6`). The checkpoint carried 20,000 prior search attempts and the existing 120,000 global ceiling.

Training draws 0050–0053 generated four distinct goal states and did not overlap the checkpoint's training trial keys. Validation draws were empty. The run enabled exact finite effect deduplication and allocated each new request at most 10,000 discovery attempts plus a non-reallocatable 5,000 transfer reserve. The maximum incremental allocation was 60,000; the corresponding maximum cumulative graph count was 80,000, still below 120,000.

## Observed work and outcomes

The completed graph contains 61,722 unique attempt IDs: 20,000 inherited and 41,722 new. Every new request used exactly 10,000 discovery attempts. Three targets used 574 transfer attempts each (1,722 total); the fourth used none. The remaining 18,278 reserved transfer attempts stayed unused and were not moved to discovery. Cumulative graph work remained below both the planned 80,000 branch maximum and the 120,000 global ceiling.

The exported finite-effect funnel contains 61,716 residual and 6 verified attempts. Across the whole graph, 5,232 exact effect digests occurred; 56,490 attempts repeated an effect already represented in that graph/domain/probe context. In the new four-request tranche, 41,722 attempts represented 2,909 distinct effect digests, with 38,813 repeated-effect attempts across the shared search space. The two newly verified expressions in task 0051 had different syntax keys but the same exact effect digest. Only attempt `#32376` derived the new candidate `#41575`; equivalent verified attempt `#35270` did not mint another candidate. This is direct evidence of the enabled exact-effect mint guard, not evidence of a useful process.

The branch produced one new unapproved candidate, `#41575`; two unapproved candidates in the continuation output were already present in the parent checkpoint. Candidate `#41575` received 1,722 independent-goal trials across distinct goals 0050, 0052 and 0053. All were residual; there were zero new qualifications, approvals, receipts, adoptions or descendant checkpoints. The result's one approval and one receipt are inherited parent state, not new transitions. No oracle expression or held-out outcome was supplied.

Runtime resource accounting reports 61,722 cumulative attempts, 98 native rule steps in the runner counter, 889.58 seconds wall time, and 2,030,329,856 bytes peak RSS. The isolated native rule-work snapshot has complete rule-identity coverage and zero unresolved rule IDs. Its exact per-metric totals and digest are preserved in the raw result.

## Retained artifacts

- Compressed development result: `evaluation/process_mastery/results/p26_search_repair_loopover_g1_0050_0053.json.gz`; SHA-256 `36dfe1cb6b935d1f7c86f502ff60441ab56c969fda3507e310a0601f2d285d68`. Decompressed JSON SHA-256: `2cd85646204f6d01b065ecf5972d72a6431977c790ac5431c8aea39c6b6de48b`.
- Compressed attempt projection: `evaluation/process_mastery/results/p26_search_attempt_details_loopover_g1_0050_0053.json.gz`; SHA-256 `3d198ab4b4e3c1f0c0c2eb68e6810602184e4d66f8d939c99b0906493fde87d9`. Decompressed report SHA-256: `55eeade8451582ad5eb491335073057971fdb398106f82c50b188bb05961542e`. It contains all 61,722 unique attempts, task/request/source/parent provenance, finite effects, statuses, and a candidate-source join from the result's exact `proposals[].source_attempt_ids` links.

Two earlier invocations of the same deterministic allocation completed the search computation but failed before writing a result: the first exposed structured-key handling in the attempt exporter; the second exposed quadratic edge scanning and was stopped after that cost was identified. Their in-memory graphs were lost, so their exact attempt counts are unrecoverable and they are not included in the retained branch totals or treated as independent evidence. The exporter fixes and regressions are included in the current source. The successful retained branch is the sole reportable allocation; this operational replay history means total debugging compute exceeded its recorded 41,722 new attempts.

## Verification and interpretation

The native search/export, reserve, independent-improvement, and feasibility regression bundle passed: 45 tests. Python compilation passed for the modified runner/exporter and seed generators. The attempt export is opt-in and read-only; it did not feed back into the agent.

P26.02 closes the measured search-repair mechanism for this finite training branch. It does not show independent-goal qualification, useful learning, efficacy, global search completeness, or a capability-level increase. P26.03 remains the next phase and must measure evidence selection through the common learner.
