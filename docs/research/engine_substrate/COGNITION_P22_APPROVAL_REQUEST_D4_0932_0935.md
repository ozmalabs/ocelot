# P22 candidate-specific simulated-adoption request: D4 0932–0935

**Status: superseded. No action has been taken. Do not authorize this request.**

The candidate effect is identical to the already-held `rot90` process in the registered D4 generation-zero root. A proposal that adds no new process effect cannot count as an improvement; this request is invalid.

The invalidated candidate had digest `209f9861ca82daf500284f696298b28b18a420c885bf6c16d4a5aa23e714fd65` and parameters `[1, 3, 0, 2]`. Although its effect differed from the root's `flip_r` process `[2, 3, 0, 1]`, it matched the other active process, `rot90`.

The earlier rule recorded two independent-goal qualifications. This request had selected only `#11710`, witnessed by training worlds `p22:d4-v2:train:0932` and `p22:d4-v2:train:0933`. The later effect audit invalidates both as improvement evidence because the effect duplicates `rot90`. There are no validation or held-out worlds in the reconstruction.

This request has been superseded. Do not authorize the transition. The earlier candidate-specific approval prompt does not apply.

## Reproduction binding

Machine request: [`COGNITION_P22_APPROVAL_REQUEST_D4_0932_0935.json`](COGNITION_P22_APPROVAL_REQUEST_D4_0932_0935.json).

Training source: `evaluation/process_mastery/results/p22_training_panel_registered_root_d4_0932_0935.json` (SHA-256 `870f3011137e4bade21a8f159c9e74186191d3cbd901829f5777dd964e50462f`). It is rooted in the exact registered checkpoint `p22-d4-invention_only-g0`, digest `fe39a44242987c5c97404c8b0812c3928a7324aee2911f57133417ce2650236c` from `evaluation/process_mastery/results/p22_four_arm_checkpoint_roots_d4_0520.json`.

The machine request now has status `superseded`; the guarded CLI rejects it. The prior read-only replay verifies reproducibility only and did not authorize an action.
