# P22 candidate-specific simulated-adoption request: D4 0932–0935

**Status: awaiting exact user approval. No action has been taken.**

This packet requests exactly one D4 training-simulator transition for candidate `#1870`, followed by a conditional generation-one checkpoint rooted in the registered P22 D4 invention-only generation-zero ancestor. The candidate has digest `209f9861ca82daf500284f696298b28b18a420c885bf6c16d4a5aa23e714fd65` and parameters `[1, 3, 0, 2]`. Its effect differs from the registered root process `[2, 3, 0, 1]`.

The candidate qualified on two independent-goal pairs. This request selects only qualification `#11710`, witnessed by training worlds `p22:d4-v2:train:0932` and `p22:d4-v2:train:0933`. The other qualification is not included in this request. There are no validation or held-out worlds in the reconstruction, and approval will establish only a lineage transition, not efficacy.

To authorize exactly this one transition and its conditional checkpoint, reply:

`approve 209f9861ca82daf500284f696298b28b18a420c885bf6c16d4a5aa23e714fd65; review_seconds=<your seconds>`

The review duration must be reported by the reviewer. No prior approval applies to this candidate.

## Reproduction binding

Machine request: [`COGNITION_P22_APPROVAL_REQUEST_D4_0932_0935.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0932_0935.json).

Training source: `evaluation/process_mastery/results/p22_training_panel_registered_root_d4_0932_0935.json` (SHA-256 `870f3011137e4bade21a8f159c9e74186191d3cbd901829f5777dd964e50462f`). It is rooted in the exact registered checkpoint `p22-d4-invention_only-g0`, digest `fe39a44242987c5c97404c8b0812c3928a7324aee2911f57133417ce2650236c` from `evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_d4_0520.json`.

The guarded CLI requires the exact request, training draws, root checkpoint digest, candidate digest, reviewer-reported time and one-shot output path. It creates no held-out allocation.
