# GenMint process-restart persistence and reuse results

## Integrity and persistence

The preregistered 90 sequences completed: six matrix/layout cells × three arms × five fresh-process replicates, with K=16 held-out bases per sequence. The independent v1.1 analysis passes all 15 integrity and semantic gates: exact randomized schedule and label binding, no worker failures, five replicates per cell, unique producer/consumer PIDs, independent input reconstruction, stable repeat outcomes, and continuous/restart-enabled semantic parity.

All 60 restart sequences restore the graph and grammar exactly and the rule store semantically; checkpoint bytes and SHA-256 reconcile between producer and fresh consumer. Median checkpoint size is 392,424 bytes for enabled training and 389,206 bytes for the disabled arm. Median write time is 5.30 ms; median restore time is 132.9 ms.

## Acquisition and held-out use

The enabled learner acquires the intended matrix in 25/30 sequences in both continuous and restarted arms. Acquisition is 5/5 for prior-matrix adjacent/opposite, shearA adjacent/opposite, and shearB opposite; it is 0/5 for shearB adjacent. This remains a real limitation despite the training status being `recognized_transformed` in all cells.

Across the 25 acquisition-success sequences, every one of the 400 held-out calls selects the exact training-acquired generator, and all 400 predictions match the independently reconstructed target. The restart-enabled outputs match the continuous-enabled outputs in all 30 paired sequences. The additional 80 enabled-arm calls in the five acquisition-failure sequences are exact through an expected-matrix other-generator route; they are not credited as persistence/reuse of a training-acquired object. The restart-disabled arm acquires no training generator and has 0/480 exact held-out predictions on this scoring route.

## Costs and interpretation

Median whole-sequence wall time is 422 ms continuous-enabled, 840 ms restart-enabled, and 871 ms restart-disabled. Restart therefore adds a median 410 ms versus continuous execution, primarily for the extra process and checkpoint restore. Against restart-disabled, restart-enabled is faster in 19/30 paired sequences, with a pooled median paired difference of −28.8 ms. Restricting to the 25 sequences that actually acquired the intended generator, restart-enabled is faster than disabled in 19/25 pairs, with median difference −44.6 ms. The aggregate effect is modest and varies by matrix/layout; shearB-adjacent has no acquisitions and restart is slower than disabled there.

Median peak RSS is 39,832 KiB continuous and 48,122 KiB restart-enabled (maximum of producer and consumer process peaks). These are single-host process measurements, not a population estimate. The 90 repeats are source/runtime repetitions across six fixed task cells, not 90 independent task families.

This establishes that selected authored 2-D generators can survive a graph/grammar/rule checkpoint, be selected after a fresh process restart, and produce exact held-out predictions when acquisition succeeds. It does not establish natural-task acquisition frequency, broad family transfer, stable economic amortization, novel primitive induction, self-improvement efficacy, or substrate meta-learning.

## Artifacts

- [Preregistration](SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_PREREG_20260930.md)
- [Analysis amendment](SUBSTRATE_GENMINT_PROCESS_RESTART_REUSE_V1_1_AMENDMENT_20260930.md)
- [Runner](../../../scripts/genmint_process_restart_reuse_v1.py)
- [Original preregistered analyzer](../../../scripts/analyze_genmint_process_restart_reuse_v1.py)
- [Amended independent analyzer](../../../scripts/analyze_genmint_process_restart_reuse_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/genmint_process_restart_reuse_v1_lock_20260930.json)
- [Raw capture](../../../evaluation/reports/genmint_process_restart_reuse_v1_20260930.json)
- [Initial pilot capture](../../../evaluation/reports/genmint_process_restart_reuse_v1_initial_pilot_20260930.json)
- [Initial pilot lock](../../../evaluation/substrate_capability/genmint_process_restart_reuse_v1_initial_pilot_lock_20260930.json)
- [Amended analysis](../../../evaluation/reports/genmint_process_restart_reuse_v1_1_analysis_20260930.json)
