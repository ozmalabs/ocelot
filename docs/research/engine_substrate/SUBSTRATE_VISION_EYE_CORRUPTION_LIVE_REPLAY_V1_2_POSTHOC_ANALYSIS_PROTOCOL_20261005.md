# Live corruption replay v1.2 post-hoc analysis protocol

This is an exploratory numerical-semantics analysis of the fixed v1 live capture; it runs no new engine work. The analysis is post-hoc because the original exact-max discrepancy was already observed.

Reconstruct activation sums by iterating `set(recorded_mask)`, matching the iteration semantics of the v1.2 offline scorer. This is necessary because floating-point summation is order-sensitive. Report activation error using relative tolerance `2e-15` and absolute floor `1e-300`. Report strict exact-max membership and one-ULP membership separately; the latter is a diagnostic tolerance and cannot convert the original strict gate into a pass. Determine receptive centers from captured weights. Report native single-winner accuracy and exact-max set-valued accuracy separately, including probes where tied maxima span both correct and incorrect regions.

Required checks are source-lock integrity, 12 unique workers and six seed pairs, exact weight and clean-output parity, all 3,456 corruption-mask joins against the offline report, frozen weights, activation reconstruction, and native winner membership within one ULP of the reconstructed maximum. Include strict exact-max counts and tie ambiguity as reported outcomes. Passing remains descriptive: no independent robustness, semantic recognition, online learning, or self-improvement claim follows.

The v1.1 post-hoc analyzer is retained but superseded because it summed a sorted list instead of the offline scorer's set, changing addition order. The v1.2 analyzer source lock records all fixed inputs and this protocol. Reproduce with `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1_2.py --lock`, then invoke it without arguments.
