# Production visual ingress scope v1.1 analysis amendment

The original analyzer's `checkpoint_identity` check compared each worker's prepared graph digest with the source-locked checkpoint **file** digest. Those are different objects, so the check failed even though the capture had restored the expected graph. The original analyzer and its 10/11 output are preserved unchanged.

The corrected analyzer now verifies both links independently: the checkpoint file SHA-256 matches the source lock, and a canonical digest recomputed from the checkpoint graph matches the worker's prepared-graph digest. It also adds an owner-omission projection sensitivity check and reports a post-hoc rate-equation diagnostic using stored update stamps. The corrected analysis passes 12/12 integrity and sensitivity checks.

The rate-equation diagnostic is not a semantic pass: `WaveWorld.step` exposes only its completed tick, not the internal rule phase. Of 4,096 final unit samples with equal `act_step` and `rate_step`, 1,208 differ from `max(act - theta, 0)` by more than 1e-9. The exact rate-write phase remains unobserved; a follow-up must add phase-local capture and compare its final graph to the default adapter before claiming equation parity.

The amendment changes analysis only. It does not modify the runner, raw capture, source lock, or measured outcomes.
