# Live corruption replay v1.5 post-hoc rule-oracle protocol

This is a post-hoc source-locked reanalysis of the existing v1 live capture. It adds no training or engine execution. It addresses a narrower and more direct question: does the live graph's `ph0_wunit_winner` rule select a maximum of the activation values actually recorded by that same graph?

The seed defines `Argmax` over the Eye's `has_wunit` neighbors, ranked by each WUnit's `act`; the effect writes `winner=1` and stamps `win_step`. The evaluator implementation scans selector candidates, replaces the current winner only on a strict comparison, and retains the first encountered candidate on equal values. The adapter constructs `eye.units` in WUnit creation/insertion order. The captured `acts` and `winners` arrays use that adapter order. The analysis checks (a) each native winner is among exact maxima of recorded native activations and (b) ties resolve to the first maximum in that order.

Separately preserve the weight-reconstruction comparison: reconstruct corruption sets with the original deterministic procedure, sum in that set's iteration order, and report strict equality and one-ULP membership. Those are analytical reconstructions and do not supersede native-act winner parity. Report native single-winner and offline set-valued task scores separately.

Required checks: source hashes for the rule seed, selector evaluator, adapter, runner, capture, and original lock; 12 unique workers; 2,880 corruption probes; exact native-act maximum membership; first-in-order tie resolution; exact frozen weights and mask identity; and the v1.4 numeric reconstruction checks. This remains exploratory because the oracle was selected after seeing the earlier mismatch. It establishes implementation consistency on this captured task, not general visual capability or robustness.

Reproduce using `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1_5.py --lock`, followed by the same command without `--lock`.
