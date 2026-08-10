# PHYSICS FROM OBSERVATION — Stage 0 pre-registration

**Posture:** wiring-confirmation + bugfix, NOT build-new-features. Default
assumption: the substrate's order-N dynamic-quantization loop can already
discover the generator that makes an unexplained accelerating stream
predictable (zero the residual). Task: wire a raw synthetic scalar stream into
the EXISTING loop, run the `run_rules` fixpoint, and confirm — or find and fix
the bug — WITHOUT inventing a new Term/detector.

**Seed block:** `SEED CLAIM 136000-136999: CLEAN -- no collision DETECTED.`
(`python3 scripts/seed_claim.py 136000 136999`, exit 0.)

**Engine:** shared canonical build, sha256
`3c2ef2902a5441bd8ef2398d617de098bdc2daa913d5556669c46aee0d7b2376`,
`source_match = shared`. No Rust touched (a wiring/seed/polarity fix was the
expectation; a new Term was forbidden).

## The streams (UNTUNED constants; each frame = one moving point)

| stream | positions | 1st diff | 2nd diff | order |
|---|---|---|---|---|
| const_vel (control) | 0 3 6 9 12 15 18 | 3 3 3 3 3 3 | 0 | N=1 |
| const_accel (TARGET) | 0 1 3 6 10 15 21 | 1 2 3 4 5 6 | **1 (const)** | N=2 |
| changing_accel (control) | 0 1 3 7 14 25 41 | 1 2 4 7 11 16 | 1 2 3 4 5 (not const) | N≥3 |
| random (control) | 10 4 9 11 3 11 12 | -6 5 2 -8 8 1 | irregular | none |

Wiring vehicle: the EXISTING temporal machinery `TimeInfer` + `time_axis` seed
(`time_infer_enabled=1`), exactly as the committed gate
`tests/test_time_infer_migrated.py` exercises it — a tick-ordered frame
sequence decoded for a single transition generator. This is the temporal
sibling the task named (`TimeInfer`).

## Discriminator (registered BEFORE any number)

- **CONFIRM:** the loop, correctly wired (≤ a minimal bugfix), mints the
  order-N generator (N=2) that zeroes the residual on `const_accel`; mints
  nothing spurious on the controls (const_vel explained at N=1; random not
  compressible; changing_accel keeps a residual); no seeded predicate/threshold.
- **DEGRADE:** works only after a real bugfix with caveats, or explains but the
  minted "law" is not cleanly the acceleration generator.
- **FALSIFY (high bar, code-evidenced):** the existing order-N machinery
  genuinely cannot mint on `const_accel` without a seeded constant/predicate —
  name the exact code limit. Must be PROVEN, not concluded from one failed wiring.

## Registered hypothesis / predicted numbers

Prediction (to be tested): const_vel → mints 1 `latent:time` generator (N=1);
const_accel → **?** (CONFIRM would mint the N=2 generator; FALSIFY would floor);
changing_accel → floor; random → floor. Oracle 222/0 before AND after.
