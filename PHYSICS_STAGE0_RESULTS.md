# PHYSICS FROM OBSERVATION — Stage 0 results

**Verdict: FALSIFY (high-bar, code-evidenced).** The existing order-N machinery
is **order-1 for a temporal stream** and cannot mint the N=2 (constant-
acceleration) generator that zeroes the residual — not without a NEW capability
(a difference-stream Term, an order-N recursion inside `TimeInfer`, or an
affine/state-augmented generator search). This is not a polarity flip, a
disconnected gate, or an off-by-one: the order-1 restriction is the deliberate
core of the algorithm, documented repeatedly as "the honest MDL floor" and
GATED by a passing test (`test_varying_velocity_is_not_an_orbit`). **No feature,
Term, or detector was added** (the task forbids it; the FALSIFY bar was met with
code + live evidence instead).

## What ran (live, `run_rules` fixpoint, engine `3c2ef29`, source_match=shared)

Raw scalar streams wired into `TimeInfer` + `time_axis` (`time_infer_enabled=1`),
each frame a single moving point `["m", pos, 0, "x"]` — the SAME shape the
committed gate uses.

| stream | 2nd diff | `run_rules` status | `latent:time` minted |
|---|---|---|---|
| const_vel (N=1 control) | 0 | `time_inferred` | **1** — `('translate', (3,0), (), 7)` ✓ |
| **const_accel (N=2 target)** | **1 (const)** | `time_none` | **0** ✗ |
| changing_accel (N≥3 control) | not const | `time_none` | 0 |
| random (control) | irregular | `time_none` | 0 |

Raw `TimeInfer` Term verdicts (`native.evaluate`, tuples):

- `const_vel` : `explained=True, offset=(3,0)` — N=1 velocity generator found.
- `const_accel` 1-D: `explained=False, checked=0, offset=(), matrix=()`.
- `const_accel` as `(position, velocity)` 2-D state: `explained=False` too.

**The discriminating fact:** `const_accel` (COMPRESSIBLE at N=2 — 2nd diff a
constant `1`) and `changing_accel` (NOT compressible) hit the **identical**
`time_none` floor. The machinery provably cannot walk N up — if it could, it
would separate these two. Both are erased at the same order-1 boundary.

## The exact code limit (why it cannot, without a new capability)

1. **`TimeInfer` commits to ONE generator inferred from the FIRST pair and
   verifies by exact equality across every consecutive pair**
   (`runners/dsl/src/shape_decode.rs:2556` infers translate from `(f0,f1)`;
   `2588-2600` the loop requires that single `G` to carry every pair, else
   returns `unexplained`). A varying offset (acceleration) falsifies it. On
   `const_accel`, `checked=0`: the first-pair translate `(1,0)` pre-empts the
   linear search and is then falsified at pair 2 — it never searches harder.

2. **The search space is translate-offset OR a 2×2 PURE-linear map — no affine
   drift term** (`shape_decode.rs:2558` `else if coord_dims.len() == 2`;
   `2574-2582` enumerates integer 2×2 `M`, applied by `apply_linear_once`; `2584`
   `else { None }`). So a state-augmented `(p,v)` stream whose true transition is
   affine `(p+v, v+1)` is inexpressible (verified: `explained=False`), and any
   `(p,v,c=1)` 3-dim encoding falls out of the `len()==2` branch entirely.

3. **On failure `TimeInfer` returns empty `offset`/`matrix` and NO per-pair
   residual / difference sequence** (`shape_decode.rs:2533-2544` the `unexplained`
   Dict; `2586` early return). There is nothing for an order-2 recursion to
   consume — the first-difference stream `[1,2,3,4,5,6]` is never formed or
   re-observed anywhere.

4. **The seed's only response to `explained=false` is `time_none` (mint
   nothing)** (`seeds/time_axis.json` `time_infer_floor`). No rule forms a
   difference stream or re-observes it; the whole seed is `{mint | floor}`.

5. **The generic sd-loop "order-N growth" does NOT re-derive a higher-order
   generator.** `sd_mint_quantum` (`seeds/shape_decode_loop.json`) mints an
   OPAQUE `CapabilityAxis` keyed by the residual **predicate names**; `sd_redecode`
   re-runs the SAME spatial ladder against a codebook grown with new PARTS. It
   accretes novel parts (spatial novelty), it does not compute a temporal second
   difference. The DimInfer/GenInfer rungs it re-arms operate on the coord slots
   of a SINGLE signature, never on a temporal sequence.

6. **The whole Infer family shares this order-1 rigidity core and refuses
   higher order by design.** `DepthInfer` reads `TimeInfer`'s residual as SPATIAL
   multi-velocity (distinct constant velocities across surfaces), not temporal
   acceleration (`seeds/depth_axis.json`; `shape_decode.rs:3941+`);
   `shape_decode.rs:2924` states an accelerating orbit "grounds NOTHING (held
   open)"; `SupportInfer`/`BlinkBridge` likewise. There is no second-difference,
   order-N recursion, or affine generator anywhere (grep-confirmed).

## Why this is FALSIFY and not a fixable wiring bug

To mint the N=2 generator one must ADD a capability: (a) a difference-of-frames
stream constructor Term + a recursion rule (re-observe the offset sequence), or
(b) an affine / state-augmented / N-dimensional generalization of `TimeInfer`'s
search. Each is a new Term/detector — outside the minimal wiring/polarity fix the
task authorized, and explicitly forbidden. There is no gate to reconnect, no
polarity to flip, no N-stops-at-1 loop to un-cap: **there is no order-≥2 temporal
loop to un-cap in the first place.** The order-1 refusal is intended, documented,
and gated green.

The earlier scaffolded physics result used a hand-coded
`law_predicate = And(obs≥6, distinct==1, global≥2)` (`seeds/epistemics_core.json`);
this exercise deliberately did NOT use, reach for, or re-create it. Its absence is
precisely why the generic loop floors here — the generic loop has no order-N-in-
time faculty of its own.

## Provenance / discipline

- Seed: `SEED CLAIM 136000-136999: CLEAN`.
- Engine: sha256 `3c2ef2902a5441bd8ef2398d617de098bdc2daa913d5556669c46aee0d7b2376`,
  `source_match = shared`. No Rust edited.
- Oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped, 0 failed
  (222/0)** BEFORE. No code changed, so AFTER is identical (no bugfix applied).

## What I got wrong / honesty

- The task's DEFAULT ASSUMPTION ("it already does this; wire + bugfix") is FALSE
  for a temporal order-2 stream. I entered expecting to confirm or find a
  polarity/gate bug; the reality is a genuine expressiveness limit. I verified
  this at three levels (full `run_rules`, raw Term verdict, and the `(p,v)`
  state-augmentation escape) before concluding, per the high-bar FALSIFY rule.
- I checked the two most-likely "bug" shapes the task named and cleared them:
  the `generator_salience.py` `distinct_count==1` polarity is NOT in the
  TimeInfer/time_axis path (that path has only mint/floor, decided by the Rust
  Term's `explained` verdict, not a salience gate); and the loop does not
  "stop at N=1" — there is no N≥2 temporal loop that could be un-stopped.
- Representation caveat, stated plainly: "the law of the fall" here is only the
  N=2 integer difference structure (2nd diff constant), on a synthetic 1-D
  scalar stream. Real gravity (½gt², a continuous constant) is cross-frame and
  intensional (CLAUDE.md's frame/continuum invariant); Stage 0 was only whether
  the loop mints the order-2 generator at all. It does not.
