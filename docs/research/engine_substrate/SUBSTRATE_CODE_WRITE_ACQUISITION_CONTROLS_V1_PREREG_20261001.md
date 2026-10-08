# Code-write acquisition controls v1 — preregistration

## Question

Does reading an example alone alter code-writing behavior, and does example teaching detect a source/request semantic mismatch?

## Arms and gates

Run four fresh full-seed processes in randomized order, two repetitions per arm:

1. **Exposure only:** read the parity example with `read_function`, do not call any teaching API, then attempt the parity request. Gate: the request remains unsupported by the starter codebook and no new write construction appears.
2. **Mismatched teaching:** teach that same parity function with a clamp request, then write the clamp request and check a preregistered held-out clamp set against an independent analytic oracle. Record whether the shape is admitted/selected and whether it is correct. This is a diagnostic false-transfer probe, not an expected pass condition.

The exposure and mismatched arms use separate fresh processes. Each worker records baseline and post-intervention codebook state, read/teach provenance, composition and emitted code, native Term results, Python results, independent oracle results, elapsed phases, RSS, and source fingerprints. The harness supplies no expected outputs to substrate APIs.

## Controls, scope, and decision

The parity source is fixed to `return value % 2 == 0`. The clamp request and 12-value held-out set are fixed in the runner. The oracle is separately coded in the analyzer. A mismatch admitted and selected but failing the oracle demonstrates that current teaching validation checks internal Term/write agreement, not request semantics. A mismatch refused is evidence only for this particular pair. Two repetitions per arm are screening evidence, not a calibrated rate estimate.

All implementation, runner, analyzer, protocol, native binary, boot manifests, and complete source trees are SHA-256 locked before capture and rechecked afterward. The panel must not overwrite existing lock or capture files. A failure to boot, read, teach, select, or write is retained as a result. No general program-synthesis or self-improvement claim follows from this study.
