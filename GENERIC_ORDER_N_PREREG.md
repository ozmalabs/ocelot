# DIMENSION-GENERIC ORDER-N — pre-registration

**Posture:** BUILD a genuine new capability in the discovery core — order-N as a
property of ANY dimension, delivered by ONE generic mechanism. Builds directly on
the Stage-0 FALSIFY (`PHYSICS_STAGE0_RESULTS.md`), which proved the substrate
accretes higher order in SPACE but was frozen at ORDER-1 IN TIME: `TimeInfer`
fit ONE generator from the first frame-pair and required exact equality across
all pairs, so constant VELOCITY minted but constant ACCELERATION floored to
`time_none`, indistinguishable from random.

**The mechanism (registered):** along any ordered frame sequence, fit a per-pair
generator; if that generator's PARAMETER is not constant but is itself REGULAR
(its finite differences reach a witnessed constant), RECURSE on the parameter's
difference-stream (order+1). Velocity → acceleration → jerk. The recursion is
written over an integer-vector STREAM with NO notion of which dimension indexes
it — the SAME code serves time, a spatial scan, or a minted latent axis. The
order reached falls out of where the residual stops being compressible: no
hard-coded cap, no seeded predicate, no `if dimension == time`.

**Seed block:** `SEED CLAIM 137000-137999: CLEAN -- no collision DETECTED.`
(`python3 scripts/seed_claim.py 137000 137999`, exit 0.)

**Engine:** own build required (Rust edited). Baseline (unchanged source) sha256
`0d06416d830a6db6843ac945e602a09a37ce25289df6d9d74cacd902befe8c8f`,
`source_match = own`. Oracle `scripts/rung7_vision_bench.sh` BEFORE: **212 passed,
10 skipped, 0 failed (222/0)**.

## The streams (per-pair translate offset sequences; each frame = the BASE shape shifted)

| stream | offsets | 1st diff | 2nd diff | 3rd diff | registered order |
|---|---|---|---|---|---|
| const_vel (control) | 2 2 2 2 2 2 | 0 | — | — | N=1 (byte-identical) |
| **const_accel (TARGET)** | 1 2 3 4 5 6 | 1 1 1 1 1 | 0 | — | **N=2** |
| order3 (jerk) | 1 2 4 7 11 16 | 1 2 3 4 5 | 1 1 1 1 | 0 | N=3 |
| random (control) | −6 5 2 −8 8 1 | irregular | irregular | irregular | none (floor) |

## Discriminator (registered BEFORE any number)

- **CONFIRM:** const_accel (the Stage-0 FALSIFY) mints an order-2 generator that
  zeroes its residual (predicts the unseen next frame exactly); order3 mints
  order-3; random floors; const_vel still mints order-1 BYTE-IDENTICALLY; the
  mechanism is dimension-generic (same Term/path serves a non-time ordering);
  no seeded predicate, no hard-coded order cap. Oracle 222/0 before AND after,
  only the one old-limit gate updated honestly.
- **DEGRADE:** order-2 works but clean general order-N needs a bounded cap, or
  the dimension-generality is only partial — report exactly what is general.
- **FALSIFY:** making order-N generic can't be done additively — it disturbs an
  existing success or breaks the oracle, revealing a deeper coupling; or the
  recursion can't be gated without a magic order/constant. Report the coupling
  with code evidence; do NOT rescue by special-casing time or seeding a cap.

## The old-limit gate this supersedes

`tests/test_time_infer_migrated.py::test_varying_velocity_is_not_an_orbit`
asserts "accelerating → time_none" as CORRECT (the order-1 MDL floor). With
generic order-N that becomes an order-2 mint. It is updated in place to
`test_varying_velocity_mints_an_order_2_generator` (accelerating → order-2
translate generator minted), with a comment naming the capability that superseded
the floor. The control it protected — a genuinely order-≥N-unstructured (random)
stream must still floor — is preserved in
`test_generic_order_n_migrated.py::test_random_stream_floors`.

## Predicted numbers

const_vel → order-1 mint (byte-identical); const_accel → **order-2 mint** (the
FALSIFY resolved); order3 → order-3 mint; random → floor. Oracle 222/0 before AND
after. Rust unit tests `order_n_generic_tests` 5/5 (dimension-agnostic on raw
streams). Gate `tests/test_generic_order_n_migrated.py` all green.
