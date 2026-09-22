# P5-R0 V3 repair results (local, no-go)

This document records the approved V3 repair status without replacing the historical V2/native artifacts. It is local readiness evidence only; it is not a release, adoption, positive-transfer, or general-intelligence result. No network access, image pull, commit, or authority/promotion action is permitted.

## Repair disposition

The V3 implementation now fails closed at the repaired boundaries:

- illegal-action stimuli are worker-boundary `protocol_error` cases and cannot be silently converted into legal evaluator actions;
- warm-reset identity/order mismatches reject before native invocation, preserve state, and can be written as signed V3 reset mutation artifacts;
- completed no-go seals require the same locked primary/control/contrast closure as any completed result, so omitted controls cannot be resealed;
- V3 native closure requires host execution, runtime, evidence/seal, rollback, and kill-path content digests in addition to the worker/runtime/image/seccomp bindings;
- host execution/runtime/kill evidence is closure- and lock-bound, and missing evidence contributes a no-go reason.

The remaining local result is intentionally **`local_readiness_only/no_go`** until a separately supplied authority trust binding, authority-bound signer, explicit custody boundary, and externally supervised kill/liveness path exist. A workspace/test authority remains insufficient for the required trust binding.

## Artifact preservation

The prior V2/native run and its receipts remain at their existing paths and are not rewritten. The repaired V3 output must use a separate lock, receipt, mutation, and result root; output collisions and V2-parent overlap are rejected. Existing native evidence that observed a red illegal-action control remains historical no-go evidence rather than being rewritten into a pass.

## Validation record

Focused adversarial coverage is in `tests/test_p5_r0_v3_repairs_adversarial.py`, alongside the existing V3 activation, repair, worker-privacy, runner, and gate-closure tests. The local environment used for this repair does not contain the `cryptography` package, so pytest collection could not run here; Python byte-compilation of all modified P5-R0 modules succeeded. No dependency installation or network request was attempted.
