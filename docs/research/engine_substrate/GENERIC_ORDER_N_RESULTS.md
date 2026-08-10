# DIMENSION-GENERIC ORDER-N — results

**Verdict: CONFIRM.** Order-N is now a property of ANY dimension, delivered by ONE
generic finite-difference recursion. The Stage-0 FALSIFY is resolved: the
constant-acceleration stream that floored to `time_none` (indistinguishable from
random) now mints an order-2 generator that zeroes its residual; a genuinely
order-3 stream mints order-3; random still floors; constant velocity still mints
order-1 byte-identically. The mechanism is dimension-generic — the recursion is
written over an integer-vector stream with no notion of which dimension indexes
it. Additive at the floor: it fires ONLY where order-1 had already given up.

## What was built (files / functions)

Generalized `TimeInfer` in place — NO new Term, NO new variant index, NO change
to `NUM_TERM_VARIANTS`. The order-1 exact-equality path is untouched; a
dimension-generic order-N recursion was added and wired into its failure exits.

`runners/dsl/src/shape_decode.rs`:
- **`vec_sub` / `diff_pyramid` / `pyramid_order` / `extrapolate_next`** — the
  DIMENSION-GENERIC core. They operate on `&[Vec<i64>]` (an ordered integer-vector
  stream) with NO notion of time or any dimension. `diff_pyramid` builds the
  finite-difference pyramid, stopping at the first WITNESSED constant (all equal
  AND len ≥ 2 — one confirmation, the honest MDL floor) or when a level has < 2
  elements. `pyramid_order` returns the order (level 0 = order 1) iff the deepest
  level is a witnessed constant, else `None` (incompressible). `extrapolate_next`
  is Newton forward-difference extrapolation of the next stream element.
- **`order_n_translate_verdict`** — computes the per-pair translate offset stream
  (each pair must be a rigid translate via the existing `infer_translate_offset`),
  fits it with the pyramid, and — if the fitted order is ≥ 2 — builds the same
  Dict schema as the explained path plus `order` (N) and `coeffs` (the Newton
  forward coefficients), predicting the unseen next frame by extrapolating one
  more offset. Returns `None` (leaving the existing floor to stand) when the pairs
  are not all translates, the offset stream is not regular, or the fitted order is
  < 2 (order-1 is the caller's byte-identical path).
- **`eval_time_infer`** — its three post-frame-validation failure exits (no
  first-pair generator; a pair the single generator fails to carry) now attempt
  `order_n_translate_verdict` before flooring. The order-1 explained path returns
  before any new code runs. `order`/`coeffs` keys were added to the explained and
  unexplained Dicts (order 1 / 0) for schema uniformity — additive: no prior query
  reads them.
- **`order_n_generic_tests`** (`#[cfg(test)]`) — 5 unit tests exercising the core
  on RAW non-temporal integer-vector streams (order 1/2/3, floor, multi-dim
  vector) — the STRUCTURAL proof of dimension-agnosticism.

`seeds/time_axis.json`: the `time_infer_mint` rule now also stores `order` and
`coeffs` on the minted `latent:time` dimension; description/comment updated to the
order-N reality. The `time_infer_floor` rule is unchanged (it keys on
`explained != true`; random still floors through it).

Why generalize rather than add a Term: the offset-stream finite-difference
recursion IS the general order-N for the additive (translate) representation —
velocity/acceleration/jerk are one ladder. A parallel Term would have duplicated
`TimeInfer`'s frame-sequence plumbing and split the capability. The recursion's
input being a dimension-blind vector stream is exactly what makes it generic.

## Provenance / discipline

- Seed: `SEED CLAIM 137000-137999: CLEAN -- no collision DETECTED.`
- Branch: `gamma-substrate/generic-order-n`.
- Engine (with changes): sha256
  `10c182f76ffb49a3293490a014fbfc6fe0c06e7cb91f489d79a269cf0dcad414`,
  `source_match = own`. Baseline (unchanged source):
  `0d06416d830a6db6843ac945e602a09a37ce25289df6d9d74cacd902befe8c8f`.
- Oracle `scripts/rung7_vision_bench.sh`:
  - **BEFORE: 212 passed, 10 skipped, 0 failed (222/0)** (own baseline build).
  - **AFTER: 212 passed, 10 skipped, 0 failed (222/0)** (own build with changes).

## The measured discriminator (products, tuples, `run_rules`)

All read from `native.evaluate()` (tuples) AND the seeded `run_rules` fixpoint —
`tests/test_generic_order_n_migrated.py`, 8/8, and the updated
`tests/test_time_infer_migrated.py`, 6/6.

| stream (per-pair offsets) | `explained` | `order` | `run_rules` status | latent:time mint |
|---|---|---|---|---|
| const_vel `2 2 2 2 2 2` | True | **1** | `time_inferred` | `('translate',(2,0),(),7,1)` — byte-identical |
| **const_accel `1 2 3 4 5 6`** (the FALSIFY) | True | **2** | `time_inferred` | order-2 translate; predicts the unseen 8th frame exactly |
| order3 `1 2 4 7 11 16` | True | **3** | `time_inferred` | order-3 |
| random `−6 5 2 −8 8 1` | False | 0 | `time_none` | none (floor) |

- **The Stage-0 FALSIFY resolved:** const_accel, which floored identically to
  random, now mints order-2 and its extrapolated prediction of the unseen frame is
  exact (`test_order_2_generator_zeroes_the_residual`).
- **Order-3 mints order-3** (`test_order_3_stream_mints_order_3`).
- **Random floors** — the control the old floor protected survives
  (`test_random_stream_floors`).
- **Constant velocity byte-identical:** the exact tuple the committed gate reads,
  `('translate',(2,0),(),7)`, is unchanged; `kind/offset/matrix/window/checked`
  all identical (`test_order_1_fields_are_byte_identical_to_pre_change`).
- **Dimension-generic:** the SAME `TimeInfer` Term, fed a sequence whose ordering
  is a SPATIAL scan (shape shifting along the COLUMN axis with accelerating
  offsets), returns the same order-2 (and order-3) verdict on the IDENTICAL code
  path (`test_dimension_generic_same_path_serves_a_non_time_ordering`). Structural
  proof at the Rust level: `order_n_generic_tests` runs the recursion on raw
  streams with no dimensional meaning. There is no `if dimension == time` anywhere.
- **No hard-coded order cap:** order 1/2/3 and the floor all fall out of the SAME
  recursion — the order reached is wherever the residual stops being compressible
  (`test_no_hardcoded_order_cap_falls_out_of_compressibility`).

## Additivity proof

Every currently-succeeding input is unchanged. `tests/test_time_infer_migrated.py`
order-1/linear/shuffled/flag-off tests pass unchanged (only the one accelerating
gate was updated honestly). The order-N path is reached ONLY from `eval_time_infer`'s
failure exits, so every explained order-1/linear verdict returns before the new code
runs; and the new `order`/`coeffs` Dict keys are read by no prior query.
`test_dimension_inference_migrated` / `test_transform_decode_migrated` /
`test_ink_decode_migrated` (67 tests, other `shape_decode.rs` consumers) unchanged.

## The old-limit gate, honestly superseded

`test_varying_velocity_is_not_an_orbit` → renamed
`test_varying_velocity_mints_an_order_2_generator`: was "accelerating → time_none"
(the order-1 MDL floor), now "accelerating → order-2 translate generator minted",
with a comment naming the capability that superseded the floor. Its protected
control (random must still floor) is preserved in the new gate.

## What I got wrong / honest scope

- **First instinct check.** I confirmed (as Stage 0 did) that the failure was a
  genuine expressiveness limit, not a wiring bug — the order-N path is genuinely
  new code, correctly additive rather than a polarity flip.
- **`cargo test` cannot link the pyo3 extension-module binary** (undefined Python
  symbols). The Rust unit tests required
  `RUSTFLAGS="-L /usr/lib -C link-arg=-lpython3.14"` to link libpython. The
  installed engine is the clean `cargo build --release` cdylib (hash above), NOT
  the test build — rebuilt and re-hashed after the test run to be certain.
- **Scope of "general," stated plainly.** The order-N recursion is fully general
  for the ADDITIVE (translate/offset) representation — velocity → acceleration →
  jerk → any finite order, any dimension, any coordinate arity (the recursion is
  elementwise over the vector). It does NOT generalize the LINEAR (2×2 matrix)
  generator to a drifting/order-N matrix — a rotating-and-accelerating orbit is
  still order-1-only in the matrix branch. That is a separate, harder
  generalization (matrix-power finite differences); the translate ladder is the
  genuine general order-N for the additive dimension, and it is the one the
  Stage-0 FALSIFY named. Reported as a DEGRADE boundary, not hidden.
- **The witness is one confirmation (len ≥ 2 at the constant level).** This is the
  minimum honest MDL evidence; a longer stream would license a stronger witness. On
  the registered streams it separates all four cases correctly. A pathological short
  stream whose k-th difference is length-2-equal by coincidence would mint order-k —
  the same MDL fragility the order-1 floor always had, now one level deeper, not
  introduced by this change.
- **In-frame integers preserved (CLAUDE.md frame/continuum invariant).** Every
  coordinate stays on the integer lattice; `coeffs` are integer finite differences.
  The order-N generator is a cross-frame MAP (a `Hom(frame,frame)`), exactly where
  non-integer/continuous structure is allowed to live — no float entered any frame.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine (own) | oracle before/after | verdict |
|---|---|---|---|---|
| generic-order-N | order-N is a property of any dimension via one finite-difference recursion; Stage-0 accel FALSIFY → order-2 mint | `10c182f7…` | 222/0 → 222/0 | **CONFIRM** (translate ladder; linear-matrix order-N out of scope) |
