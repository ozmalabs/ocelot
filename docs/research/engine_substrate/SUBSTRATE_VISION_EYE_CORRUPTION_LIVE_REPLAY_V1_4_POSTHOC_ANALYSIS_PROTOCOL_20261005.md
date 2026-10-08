# Live corruption replay v1.4 post-hoc analysis protocol

This is an exploratory analysis of the fixed v1 live capture. It performs no new engine work and does not change the original exact-max result.

Recreate every corruption mask from its clean held-out probe using the same deterministic corruption routine and retain the resulting set for summation, matching the offline scorer's addition order. There are 2,880 corrupted probes (12 workers × 240), plus 576 separate clean probes. Report these counts separately. Check activation sums with relative tolerance `2e-15` and absolute floor `1e-300`. Report exact-max membership, one-ULP membership, native single-winner scoring, and set-valued tie scoring separately.

Required integrity checks: source lock unchanged; 12 unique workers and six paired seeds; exact weights and clean outputs against v2.1; 2,880 corruption masks joined to the offline report; frozen weights; activation reconstruction; every native winner within one ULP of reconstructed maximum. The strict original exact-max criterion remains failed if any native winner is not an exact reconstructed maximum. The ULP criterion is an exploratory diagnostic, not a retroactive pass. Results do not establish natural-image robustness, semantics, online learning, or self-improvement.

The v1.1, v1.2, and v1.3 reports are retained for audit history; the v1.4 report corrects v1.3's denominator, which mistakenly included clean probes. Reproduce with `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1_4.py --lock`, then run the analyzer without arguments.
