# Learning-aperture current-checkout recheck

**Date:** 2026-09-25. This reruns the preregistered `STRESS_COMPRESSES_APERTURE_PREREG.md` addendum through the current native extension. It is a recheck of one mechanism, not a new task-family replication.

## Method and provenance

The harness [`learning_aperture_measure.py`](../../../scripts/learning_aperture_measure.py) loads the shipped `learning_progress_curiosity` and `learning_aperture_gate` seeds, writes synthetic observations/epochs, runs graph rules, and reads the resulting item attributes. The Python harness supplies observations and records outputs; it does not compute learning or attention decisions. It uses four arms (learnable, stressed/compressed, mastered, and learns-then-blinds) plus a 24/48/96/192-tick exposure sweep.

The harness now accepts `--output` and includes build, seed, source, and environment hashes in its report. The current run is [`substrate_learning_aperture_recheck_20260925.json`](../../../evaluation/reports/substrate_learning_aperture_recheck_20260925.json). Its native-extension hash matches `_native.build.json`.

## Observed outcomes

| Arm | Residual | Learning progress | Interest | Attended | Observation established |
|---|---:|---:|---:|---:|---:|
| Learnable, regulated | 6 | -5 | 1024 | 1 | 1 |
| Compressed, stressed | 0 | 0 | 1024 | 1 | 0 |
| Mastered, regulated | 0 | 0 | 0 | 0 | 1 |
| Learns, then becomes blind | 3 | -5 | 256 | 1 | 0 |

For the stressed arm, maximum residual and progress remain zero through 192 ticks. In this harness, `ever_attended` is still 1 for the stressed arm; therefore the result supports assessability-state separation and preservation of mid-learning residuals, not a claim that stress fully gates attention.

## Scope

The result shows that this graph-rule pipeline distinguishes a zero produced by an unassessable observation from a zero produced by a mastered prediction, and preserves nonzero residual state when assessability is lost mid-learning. It does not establish task acquisition, held-out generalization, transfer, rule/codebook adoption, or total learning economics. The broader P3-E1 continual-learning study remains a separate gated programme; its current preregistration says the local P3-R0 harness cannot authorize adoption and no P3-E1 result is established.
