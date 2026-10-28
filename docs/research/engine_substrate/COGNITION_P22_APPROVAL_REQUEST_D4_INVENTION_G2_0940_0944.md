# P22 candidate approval request: D4 invention-only g2

**Status:** awaiting exact candidate-specific approval. No adoption has been attempted.

Candidate `#9459` has verified expression digest `76465666626d8a7ffab2b195f59035076861b8285e661c840d008fdecea9808c` and finite effect `[[0,2,1,3]]`. It descends from approved D4 invention-only g2 checkpoint `p22-d4-g2-84854777d0e3` (digest `d8a916474c8e3bafd44dda0082fd7c71ccb3dac1c0a2daf9bbe7f759c70fb4df`).

The current-seed, one-tick training replay records typed qualification `#45873` (`independent_native_trials`) on verified attempts `#6916, #12175` from distinct training tasks `#6911, #12063` with trial keys `p22:d4-v2:train:0818, p22:d4-v2:train:0963`. The inherited malformed qualification `#15845` has no qualification kind and is excluded. The raw runner projection counts both status-qualified nodes; the typed-proof audit counts one valid receipt and one invalid legacy receipt for this candidate. The same finite effect also appears on a separate qualified candidate (`#12174`); this request binds only to `#9459` and its exact qualification witness pair.

The proposed action is one candidate-bound training-simulator transition and conditional generation-three checkpoint using distinct training draws 0940 and 0944, per-request ceiling 600, global ceiling 120,000, one search tick, transfer depth 3, 400 discovery attempts plus a 200 transfer reserve, and effect deduplication. The replay inherited two approvals and two receipts; it added none. Validation and held-out allocations are empty.

Evidence:

- [Structured request](COGNITION_P22_APPROVAL_REQUEST_D4_INVENTION_G2_0940_0944.json)
- [Current-seed replay](../../../evaluation/process_mastery/results/p22_training_panel_registered_root_d4_invention_g2_0940_0944_qualification_slot_replay_current.json.gz), SHA-256 `bc38dfdb21c941102f44e8a53c33c00320a98a3d5de3d387dfec95c44c96679a`
- [Read-only attempt export](../../../evaluation/process_mastery/results/p22_search_attempt_details_d4_invention_g2_0940_0944_qualification_slot_replay_current.json.gz), SHA-256 `b3e79d36834fd64afdf8e9254c4dda0bb93c667df5a137c353df358384657584`, covering 45,480 attempts
- [Typed qualification audit](../../../evaluation/process_mastery/results/p22_d4_invention_g2_qualification_slot_replay_audit_20261028.json), SHA-256 `b03fc061bc6773416d349db3711b8c0431ea750ff579a5ec3ad040d418fb872e`
- Parent checkpoint source `evaluation/process_mastery/results/p22_approved_candidate_d4_g1_0818_0821.json`, SHA-256 `f72db827c1e05f382ae7fd84c1655f4f0c4d1cac61dbe57823438d092feb1bc7`

To authorize exactly this candidate, reply:

`approve 76465666626d8a7ffab2b195f59035076861b8285e661c840d008fdecea9808c; review_seconds=<your seconds>`
