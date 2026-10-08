# Live corruption replay v1.1 post-hoc analysis protocol

## Scope

This is a reproducibility and numerical-semantics analysis of the already completed v1 live capture. It is not a confirmatory experiment: the original exact-max failure was observed before this analysis was specified, and no new training or probes are run. The raw capture and v1 source lock remain immutable inputs.

## Analysis policy

For each captured corruption probe, recompute unit scores from captured weights and the exact recorded mask using Python `f64` summation. Report (a) exact reconstructed maxima, (b) whether each native winner is exactly maximal, and (c) whether it lies within one ULP of the reconstructed maximum. One ULP is an explicit diagnostic tolerance motivated by the observed discrepancy; passing it does not erase failure of the original exact-max gate. Check activation reconstruction with relative tolerance `2e-15` and absolute floor `1e-300`, and report maximum absolute and relative error.

Map each unit to nearest trained-site regions using its weight-derived receptive-field center. Report native single-winner correctness separately from the tie-set result over every exactly maximal reconstructed unit. A probe is tie-ambiguous when maximal units do not all agree on correctness. Never count a partially correct tie set as unambiguous success. Reconcile corruption masks to the frozen post-hoc v1.2 report.

## Gates and interpretation

Required integrity checks: locked inputs unchanged; 12 unique workers with six seed pairs; source lock and original capture hashes match; exact v2.1 weights and clean outputs; 3,456 corrupted rows joined; corruption masks match; weights remain frozen; activation reconstruction meets the stated tolerance; every native winner is within one ULP of reconstructed maximum. Also report the strict exact-max count, native accuracy, exact-max tie ambiguity, and set-valued accuracy by morphology and corruption condition.

Even a complete analysis pass establishes only numerical and scorer consistency on this synthetic, absolute-position-coded task. It does not establish independent robustness, semantic visual recognition, online learning, or general self-improvement. Since thresholds were selected after observing the v1 result, all pass language is descriptive and exploratory.

## Reproduction

Run `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1_1.py --lock`, then run `python3 evaluation/substrate_capability/analyze_vision_eye_corruption_live_replay_v1_1.py`. The lock identifies the protocol, analyzer, raw capture, original capture lock, v2.1 baseline, and post-hoc reference report.
